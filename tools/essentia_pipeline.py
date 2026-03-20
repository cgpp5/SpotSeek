#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
import time
import hashlib
import numpy as np
import librosa
import onnxruntime as ort
from pathlib import Path

AUDIO_EXTENSIONS = {".mp3", ".flac", ".m4a", ".wav", ".ogg", ".aac", ".wma", ".opus", ".aiff", ".aif", ".wv"}

def file_hash(path: Path) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def track_key(artist: str, title: str, album: str | None) -> str:
    album = album or ""
    return f"{artist}|{title}|{album}".lower()

def append_pending_redownload(redownload_dir: Path, artist: str, title: str, album: str):
    csv_path = redownload_dir / "pending_redownload.csv"
    exists = csv_path.exists()

    with open(csv_path, "a", encoding="utf-8", newline="") as f:
        if not exists:
            f.write("Artist Name,Track Name,Album\n")
        f.write(f"{artist},{title},{album}\n")

def remove_from_pending_redownload(redownload_dir: Path, artist: str, title: str, album: str):
    csv_path = redownload_dir / "pending_redownload.csv"
    if not csv_path.exists():
        return

    with open(csv_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    header = lines[0]
    remaining = [
        line for line in lines[1:]
        if line.strip() != f"{artist},{title},{album}"
    ]

    with open(csv_path, "w", encoding="utf-8") as f:
        f.write(header)
        f.writelines(remaining)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Análisis avanzado con Essentia (TensorFlow + SVM).")
    parser.add_argument("--input-dir", default=r"C:\Program Files\SpotSeek\pending")
    parser.add_argument("--output-dir", default=r"E:\Music")
    parser.add_argument("--essentia-dir", default=r"C:\Program Files\SpotSeek\essentia")
    parser.add_argument("--threads", type=int, default=1)
    return parser.parse_args()

def create_extractor_profile(temp_dir: Path, essentia_dir: Path) -> Path:
    """Crea el perfil YAML activando SVM pero desactivando cálculos redundantes."""
    profile_path = temp_dir / "profile.yaml"
    svm_models_dir = essentia_dir / "models" / "svm"
    
    svm_models = []
    if svm_models_dir.exists():
        svm_models = [str(p.as_posix()) for p in svm_models_dir.glob("*.history")]

    svm_config = "compute: 0"
    if svm_models:
        models_yaml = "\n".join(f"    - {m}" for m in svm_models)
        svm_config = f"compute: 1\n  svm_models:\n{models_yaml}"

    profile_content = f"""outputFormat: json
outputFrames: 0
highlevel:
  {svm_config}
chromaprint:
  compute: 0
"""
    profile_path.write_text(profile_content, encoding="utf-8")
    return profile_path

def run_subprocess(cmd: list[str]) -> bool:
    import os
    import subprocess
    import ctypes
    from pathlib import Path

    # --- AFINIDAD: cores 0–7 (P-cores típicos en i5-13600KF) ---
    P_CORE_MASK = 0xFF

    env = os.environ.copy()
    env["TF_CPP_MIN_LOG_LEVEL"] = "3"
    env["TF_ENABLE_ONEDNN_OPTS"] = "0"

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env
        )

        # Intentar fijar afinidad (optimización, NO crítica)
        try:
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel32.SetProcessAffinityMask(proc._handle, P_CORE_MASK)
        except Exception as e:
            print(f"  -> Aviso: no se pudo fijar afinidad: {e}")

        stdout, stderr = proc.communicate()

        if proc.returncode != 0:
            print(f"Fallo en: {Path(cmd[0]).name}")
            if stdout.strip():
                print(f"  -> STDOUT: {stdout.strip()}")
            if stderr.strip():
                print(f"  -> STDERR: {stderr.strip()}")
            return False

        return True

    except Exception as e:
        print(f"Excepción crítica en subprocess:\n{e}")
        return False

def merge_jsons(json_results: dict[str, Path], output_path: Path, semantic_data: dict | None = None):
    """Combina la salida de todas las redes neuronales y del extractor base."""
    merged_data = {"neural_networks": {}}
    
    for key, p in json_results.items():
        if not p.exists():
            continue
        with open(p, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                if key == "base":
                    merged_data.update(data)
                elif key == "tempo":
                    # Reemplazar el BPM clásico por el de la red neuronal (TempoCNN)
                    if "global_bpm" in data and "rhythm" in merged_data:
                        merged_data["rhythm"]["bpm"] = data["global_bpm"]
                else:
                    merged_data["neural_networks"][key] = data
            except json.JSONDecodeError:
                pass
                
    if semantic_data:
        merged_data["semantic"] = semantic_data

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(merged_data, f, indent=4)

def run_onnx_model(audio_path: Path, model_path: Path, metadata_path: Path, out_json: Path):
    with open(metadata_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    sr = meta.get("sample_rate", 16000)
    duration = meta.get("duration", None)

    y, _ = librosa.load(audio_path, sr=sr, mono=True)

    if duration:
        target_len = int(duration * sr)
        if len(y) < target_len:
            y = np.pad(y, (0, target_len - len(y)))
        else:
            y = y[:target_len]

    mel = librosa.feature.melspectrogram(
        y=y,
        sr=sr,
        n_fft=1024,
        hop_length=256,
        n_mels=meta.get("n_mels", 96),
        fmin=0,
        fmax=sr // 2,
    )

    logmel = librosa.power_to_db(mel, ref=np.max)
    logmel = (logmel - logmel.mean()) / (logmel.std() + 1e-8)

    x = logmel.T[np.newaxis, :, :].astype(np.float32)

    sess = ort.InferenceSession(str(model_path), providers=["CPUExecutionProvider"])
    input_name = sess.get_inputs()[0].name
    output_name = sess.get_outputs()[0].name

    out = sess.run([output_name], {input_name: x})[0]

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(out.tolist(), f)

def run_effnet_track_embeddings(audio_path: Path, model_path: Path, meta_path: Path, out_json: Path):
    import numpy as np
    import librosa
    import onnxruntime as ort
    import json

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    sr = meta.get("sample_rate", 16000)

    y, _ = librosa.load(audio_path, sr=sr, mono=True)

    PATCHES = 64
    PATCH_DURATION = 1.0
    PATCH_SAMPLES = int(PATCH_DURATION * sr)

    if len(y) < PATCHES * PATCH_SAMPLES:
        y = np.pad(y, (0, PATCHES * PATCH_SAMPLES - len(y)))

    patches = []
    for i in range(PATCHES):
        start = i * PATCH_SAMPLES
        end = start + PATCH_SAMPLES
        patches.append(y[start:end])

    patches = np.stack(patches)

    mels = []

    for p in patches:
        mel = librosa.feature.melspectrogram(
            y=p,
            sr=sr,
            n_fft=1024,
            hop_length=256,
            n_mels=96,
            fmin=0,
            fmax=sr // 2,
        )

        logmel = librosa.power_to_db(mel, ref=np.max)
        logmel = (logmel - logmel.mean()) / (logmel.std() + 1e-8)

        if logmel.shape[1] < 128:
            logmel = np.pad(logmel, ((0, 0), (0, 128 - logmel.shape[1])))
        else:
            logmel = logmel[:, :128]

        mels.append(logmel.T)

    x = np.stack(mels).astype(np.float32)

    sess = ort.InferenceSession(str(model_path), providers=["CPUExecutionProvider"])
    input_name = sess.get_inputs()[0].name
    output_name = sess.get_outputs()[0].name

    out = sess.run([output_name], {input_name: x})[0]

    embedding = out.mean(axis=0)

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(embedding.tolist(), f)

def run_openl3_embeddings(audio_path: Path, model_path: Path, meta_path: Path, out_json: Path):
    import numpy as np
    import librosa
    import onnxruntime as ort
    import json

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    sr = meta.get("sample_rate", 48000)

    y, _ = librosa.load(audio_path, sr=sr, mono=True)

    # OpenL3 usa ventanas de 1s con hop de 0.5s
    WINDOW_SEC = 1.0
    HOP_SEC = 0.5

    win_samples = int(WINDOW_SEC * sr)
    hop_samples = int(HOP_SEC * sr)

    frames = []
    for start in range(0, len(y) - win_samples + 1, hop_samples):
        frames.append(y[start:start + win_samples])

    if not frames:
        frames.append(np.pad(y, (0, win_samples - len(y))))

    mels = []

    for frame in frames:
        mel = librosa.feature.melspectrogram(
            y=frame,
            sr=sr,
            n_fft=2048,
            hop_length=512,
            n_mels=199,
            fmin=0,
            fmax=sr // 2,
        )

        logmel = librosa.power_to_db(mel, ref=np.max)
        logmel = (logmel - logmel.mean()) / (logmel.std() + 1e-8)

        # Forzar exactamente 256 frames (eje tiempo = axis 1)
        if logmel.shape[1] < 256:
            logmel = np.pad(logmel, ((0, 0), (0, 256 - logmel.shape[1])))
        else:
            logmel = logmel[:, :256]

        mels.append(logmel.T)

    sess = ort.InferenceSession(str(model_path), providers=["CPUExecutionProvider"])
    input_name = sess.get_inputs()[0].name
    output_name = sess.get_outputs()[0].name

    BATCH_SIZE = 8
    embeddings = []

    for i in range(0, len(mels), BATCH_SIZE):
        batch = mels[i:i + BATCH_SIZE]
        x = np.stack(batch)[..., np.newaxis].astype(np.float32)
        out = sess.run([output_name], {input_name: x})[0]
        embeddings.append(out)

    embedding = np.concatenate(embeddings, axis=0).mean(axis=0)


    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(embedding.tolist(), f)

def run_maest_30s_519(audio_path: Path, model_path: Path, meta_path: Path, out_json: Path):
    import numpy as np
    import librosa
    import onnxruntime as ort
    import json

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    sr = meta.get("sample_rate", 16000)

    # MAEST 30s: audio fijo 30 segundos
    DURATION_SEC = 30.0
    target_len = int(DURATION_SEC * sr)

    y, _ = librosa.load(audio_path, sr=sr, mono=True)

    if len(y) < target_len:
        y = np.pad(y, (0, target_len - len(y)))
    else:
        y = y[:target_len]

    # MAEST: mel 96, hop 256, n_fft 1024 -> frames esperados ~1876
    mel = librosa.feature.melspectrogram(
        y=y,
        sr=sr,
        n_fft=1024,
        hop_length=256,
        n_mels=96,
        fmin=0,
        fmax=sr // 2,
        power=2.0,
    )

    logmel = librosa.power_to_db(mel, ref=np.max)
    logmel = (logmel - logmel.mean()) / (logmel.std() + 1e-8)

    # Forzar exactamente 1876 frames (eje tiempo = axis 1)
    EXPECTED_FRAMES = 1876
    if logmel.shape[1] < EXPECTED_FRAMES:
        logmel = np.pad(logmel, ((0, 0), (0, EXPECTED_FRAMES - logmel.shape[1])))
    else:
        logmel = logmel[:, :EXPECTED_FRAMES]

    # (batch, frames, mels, channel)
    x = logmel.T[np.newaxis, ...].astype(np.float32)

    sess = ort.InferenceSession(str(model_path), providers=["CPUExecutionProvider"])
    
    input_name = sess.get_inputs()[0].name

    # Elegir la salida activations = sigmoid(logits)
    pred_output_name = sess.get_outputs()[13].name

    out = sess.run([pred_output_name], {input_name: x})[0]

    # Aplanar SIEMPRE a 519 floats
    scores = np.asarray(out, dtype=np.float32).reshape(-1).tolist()

    if len(scores) != 519:
        raise RuntimeError(f"Salida MAEST incorrecta: {len(scores)} valores (esperados 519)")

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(scores, f)

def map_maest_labels(scores, classes):
    pairs = list(zip(classes, scores))
    pairs.sort(key=lambda x: x[1], reverse=True)

    top = pairs[:5]

    genres = []
    styles = []

    for label, score in top:
        if "---" in label:
            genre, style = label.split("---", 1)
            genres.append(genre)
            styles.append(style)

    return {
        "top_labels": [
            {"label": label, "score": float(score)}
            for label, score in top
        ],
        "genre_main": genres[0] if genres else None,
        "subgenres": sorted(set(styles)),
    }

def process_file(audio_path: Path, args: argparse.Namespace, failed_variants: dict):
    essentia_dir = Path(args.essentia_dir)
    temp_dir = Path(tempfile.gettempdir()) / "spotseek_analysis"
    temp_dir.mkdir(parents=True, exist_ok=True)
    redownload_dir = Path(args.input_dir).parent / "pending_redownload"
    redownload_dir.mkdir(exist_ok=True)

    
    base_name = audio_path.stem
    json_results: dict[str, Path] = {}
    semantic_data = {}
    onnx_failed = False
    
    print(f"  -> Extrayendo características base y SVM...")
    extractor_exe = essentia_dir / "streaming_extractor_music.exe"
    profile_yaml = create_extractor_profile(temp_dir, essentia_dir)
    base_json = temp_dir / f"{base_name}_base.json"
    
    if extractor_exe.exists() and run_subprocess([str(extractor_exe), str(audio_path), str(base_json), str(profile_yaml)]):
        json_results["base"] = base_json

    print(f"  -> Extrayendo BPM (TempoCNN)...")
    tempocnn_exe = essentia_dir / "standard_tempocnn.exe"
    tempocnn_model = essentia_dir / "models" / "tempocnn" / "deeptemp-k16-3.pb"
    if tempocnn_exe.exists() and tempocnn_model.exists():
        tempo_json = temp_dir / f"{base_name}_tempo.json"
        if run_subprocess([str(tempocnn_exe), str(audio_path), str(tempo_json), str(tempocnn_model)]):
            json_results["tempo"] = tempo_json
    
    print(f"  -> Evaluando EffNet track embeddings (ONNX)...")

    effnet_model = essentia_dir / "models" / "discogs_track_embeddings-effnet-bs64-1.onnx"
    effnet_meta = essentia_dir / "models" / "discogs_track_embeddings-effnet-bs64-1.json"
    effnet_out = temp_dir / f"{base_name}_effnet_track.json"

    if effnet_model.exists() and effnet_meta.exists():
        try:
            run_effnet_track_embeddings(audio_path, effnet_model, effnet_meta, effnet_out)
            json_results["effnet_track"] = effnet_out
        except Exception as e:
            print(f"    Fallo EffNet ONNX: {repr(e)}")
            onnx_failed = True
    else:
        print("    Fallo EffNet ONNX: modelo o meta no existe")
        onnx_failed = True
        
    print(f"  -> Evaluando OpenL3 music embeddings (ONNX)...")

    openl3_model = essentia_dir / "models" / "openl3-music-mel256-emb512-3.onnx"
    openl3_meta = essentia_dir / "models" / "openl3-music-mel256-emb512-3.json"
    openl3_out = temp_dir / f"{base_name}_openl3_music.json"

    if openl3_model.exists() and openl3_meta.exists():
        try:
            run_openl3_embeddings(audio_path, openl3_model, openl3_meta, openl3_out)
            json_results["openl3_music"] = openl3_out
        except Exception as e:
            print(f"    Fallo OpenL3 ONNX: {repr(e)}")
            onnx_failed = True
    else:
        print("    Fallo OpenL3 ONNX: modelo o meta no existe")
        onnx_failed = True
        
    print(f"  -> Evaluando MAEST 30s 519L (ONNX)...")

    maest_model = essentia_dir / "models" / "discogs-maest-30s-pw-519l-2.onnx"
    maest_meta = essentia_dir / "models" / "discogs-maest-30s-pw-519l-2.json"
    maest_out = temp_dir / f"{base_name}_maest_519.json"

    if maest_model.exists() and maest_meta.exists():
        try:
            run_maest_30s_519(audio_path, maest_model, maest_meta, maest_out)
            json_results["maest_519"] = maest_out
        except Exception as e:
            print(f"    Fallo MAEST ONNX: {repr(e)}")
            onnx_failed = True
    else:
        print("    Fallo MAEST ONNX: modelo o meta no existe")
        onnx_failed = True
    
    if onnx_failed:
        artist = audio_path.parent.name
        title = audio_path.stem
        album = ""
        
        key = track_key(artist, title, album)
        
        h = file_hash(audio_path)

        entry = failed_variants.setdefault(key, {"hashes": {}})

        # Si este binario ya fue probado, no hacemos nada nuevo
        if h in entry["hashes"]:
            print(f"  -> Variante ya probada, se descarta: {audio_path.name}")
            from send2trash import send2trash
            send2trash(audio_path)
            return

        # Variante nueva: registrar hash
        entry["hashes"][h] = int(time.time())

        # Persistir inmediatamente el estado
        failed_variants_path = redownload_dir / "failed_variants.json"
        with open(failed_variants_path, "w", encoding="utf-8") as f:
            json.dump(failed_variants, f, indent=2)

        # Añadir a pending_redownload.csv
        append_pending_redownload(
            Path(args.input_dir),
            artist,
            title,
            album
        )

        print(f"  -> Añadido a pending_redownload: {artist} - {title}")

        from send2trash import send2trash
        send2trash(audio_path)
        return

    with open(maest_meta, "r", encoding="utf-8") as f:
        maest_info = json.load(f)

    with open(maest_out, "r", encoding="utf-8") as f:
        scores = json.load(f)

    semantic = map_maest_labels(scores, maest_info["classes"])
    semantic_data["maest"] = semantic
    print(f"  -> Consolidando datos y moviendo a biblioteca...")
    merged_json_path = temp_dir / f"{base_name}_merged.json"
    merge_jsons(json_results, merged_json_path, semantic_data)
    
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    artist = audio_path.parent.name
    title = audio_path.stem
    album = ""

    key = track_key(artist, title, album)

    # --- LIMPIEZA DE ESTADO AL ÉXITO ---
    if key in failed_variants:
        del failed_variants[key]

        failed_variants_path = redownload_dir / "failed_variants.json"
        with open(failed_variants_path, "w", encoding="utf-8") as f:
            json.dump(failed_variants, f, indent=2)

        remove_from_pending_redownload(
            Path(args.input_dir),
            artist,
            title,
            album
        )
    
    shutil.move(str(merged_json_path), str(out_dir / f"{base_name}.json"))
    shutil.move(str(audio_path), str(out_dir / audio_path.name))
    
    for f in json_results.values():
        if f.exists():
            f.unlink()
    if profile_yaml.exists():
        profile_yaml.unlink()

def main():
    args = parse_args()
    input_dir = Path(args.input_dir)

    if not input_dir.exists():
        print(f"El directorio {input_dir} no existe.")
        return

    # ------------------------------------------------------------
    # Registro persistente de variantes fallidas (en pending/)
    # ------------------------------------------------------------
    redownload_dir = input_dir.parent / "pending_redownload"
    redownload_dir.mkdir(exist_ok=True)
    failed_variants_path = redownload_dir / "failed_variants.json"

    if failed_variants_path.exists():
        try:
            with open(failed_variants_path, "r", encoding="utf-8") as f:
                failed_variants = json.load(f)
        except Exception:
            failed_variants = {}
    else:
        failed_variants = {}

    pending_files = [
        p for p in input_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in AUDIO_EXTENSIONS
    ]

    print(f"Encontrados {len(pending_files)} archivos pendientes en {input_dir}")

    for audio_file in pending_files:
        print(f"\nProcesando: {audio_file.name}")
        try:
            process_file(audio_file, args, failed_variants)
        except Exception as e:
            print(f"ERROR procesando {audio_file.name}: {e}")
            # No abortar el pipeline completo; seguimos con el siguiente
            continue

    # ------------------------------------------------------------
    # Persistir estado actualizado (limpio automáticamente)
    # ------------------------------------------------------------
    with open(failed_variants_path, "w", encoding="utf-8") as f:
        json.dump(failed_variants, f, indent=2)

    print("\nPipeline finalizado.")

if __name__ == "__main__":
    main()