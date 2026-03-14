#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

AUDIO_EXTENSIONS = {".mp3", ".flac", ".m4a", ".wav", ".ogg", ".aac", ".wma", ".opus", ".aiff", ".aif", ".wv"}

XTRACTOR_MODEL_FILES = [
    "danceability.history",
    "gender.history",
    "genre_rosamerica.history",
    "mood_acoustic.history",
    "mood_aggressive.history",
    "mood_electronic.history",
    "mood_happy.history",
    "mood_sad.history",
    "mood_party.history",
    "mood_relaxed.history",
    "voice_instrumental.history",
    "moods_mirex.history",
]

XTRACTOR_TARGETS = {
    "bpm": ("rhythm.bpm", "integer"),
    "danceability": ("rhythm.danceability", "float"),
    "beats_count": ("rhythm.beats_count", "integer"),
    "average_loudness": ("lowlevel.average_loudness", "float"),
    "danceable": ("highlevel.danceability.all.danceable", "float"),
    "gender": ("highlevel.gender.value", "string"),
    "is_male": ("highlevel.gender.all.male", "float"),
    "is_female": ("highlevel.gender.all.female", "float"),
    "genre_rosamerica": ("highlevel.genre_rosamerica.value", "string"),
    "voice_instrumental": ("highlevel.voice_instrumental.value", "string"),
    "is_voice": ("highlevel.voice_instrumental.all.voice", "float"),
    "is_instrumental": ("highlevel.voice_instrumental.all.instrumental", "float"),
    "mood_acoustic": ("highlevel.mood_acoustic.all.acoustic", "float"),
    "mood_aggressive": ("highlevel.mood_aggressive.all.aggressive", "float"),
    "mood_electronic": ("highlevel.mood_electronic.all.electronic", "float"),
    "mood_happy": ("highlevel.mood_happy.all.happy", "float"),
    "mood_sad": ("highlevel.mood_sad.all.sad", "float"),
    "mood_party": ("highlevel.mood_party.all.party", "float"),
    "mood_relaxed": ("highlevel.mood_relaxed.all.relaxed", "float"),
    "mood_mirex": ("highlevel.moods_mirex.value", "string"),
    "mood_mirex_cluster_1": ("highlevel.moods_mirex.all.Cluster1", "float"),
    "mood_mirex_cluster_2": ("highlevel.moods_mirex.all.Cluster2", "float"),
    "mood_mirex_cluster_3": ("highlevel.moods_mirex.all.Cluster3", "float"),
    "mood_mirex_cluster_4": ("highlevel.moods_mirex.all.Cluster4", "float"),
    "mood_mirex_cluster_5": ("highlevel.moods_mirex.all.Cluster5", "float"),
}

DEFAULT_PRUNE_RULES = [
    "rhythm.beats_position",
    "lowlevel.mfcc.cov",
    "lowlevel.mfcc.icov",
    "lowlevel.gfcc.cov",
    "lowlevel.gfcc.icov",
    "chromaprint",
]


@dataclass
class PipelineConfig:
    input_dir: Path
    output_dir: Path
    extractor_path: Path
    svm_models_dir: Path | None
    temp_dir: Path
    threads: int
    prune_rules: list[str]
    profile_stats: list[str]
    fail_on_missing_models: bool


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze SpotSeek downloads with Essentia and move them into the library.")
    parser.add_argument("--input-dir", default=r"C:\Program Files\SpotSeek\pending")
    parser.add_argument("--output-dir", default=r"E:\Music")
    parser.add_argument("--extractor-path", default=os.getenv("ESSENTIA_EXTRACTOR", r"C:\Program Files\SpotSeek\essentia\streaming_extractor_music.exe"))
    parser.add_argument("--svm-models-dir", default=os.getenv("ESSENTIA_SVM_MODELS_DIR"))
    parser.add_argument("--temp-dir", default=os.getenv("ESSENTIA_TEMP_DIR", tempfile.gettempdir()))
    parser.add_argument("--threads", type=int, default=int(os.getenv("SPOTSEEK_PIPELINE_THREADS", "1")))
    parser.add_argument("--prune-rule", action="append", dest="prune_rules", default=[])
    parser.add_argument("--profile-stats", nargs="+", default=["mean", "var", "median", "min", "max"])
    parser.add_argument("--allow-missing-models", action="store_true")
    return parser.parse_args()


def build_config(args: argparse.Namespace) -> PipelineConfig:
    prune_rules = DEFAULT_PRUNE_RULES + list(args.prune_rules or [])
    return PipelineConfig(
        input_dir=Path(args.input_dir),
        output_dir=Path(args.output_dir),
        extractor_path=Path(args.extractor_path),
        svm_models_dir=Path(args.svm_models_dir) if args.svm_models_dir else None,
        temp_dir=Path(args.temp_dir),
        threads=max(1, args.threads),
        prune_rules=prune_rules,
        profile_stats=args.profile_stats,
        fail_on_missing_models=not args.allow_missing_models,
    )


def main() -> int:
    args = parse_args()
    config = build_config(args)
    validate_config(config)

    pending_files = sorted(path for path in config.input_dir.rglob("*") if path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS)
    if not pending_files:
        print(f"No supported audio files found in {config.input_dir}")
        return 0

    print(f"Found {len(pending_files)} pending file(s) in {config.input_dir}")
    profile_path = write_extractor_profile(config)

    processed = 0
    failed = 0
    try:
        for source_path in pending_files:
            try:
                process_file(source_path, config, profile_path)
                processed += 1
            except Exception as exc:  # noqa: BLE001
                failed += 1
                print(f"ERROR: {source_path} -> {exc}")
    finally:
        delete_file(profile_path)

    print(f"Pipeline finished. processed={processed} failed={failed}")
    return 1 if failed else 0


def validate_config(config: PipelineConfig) -> None:
    if not config.input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {config.input_dir}")
    config.output_dir.mkdir(parents=True, exist_ok=True)
    config.temp_dir.mkdir(parents=True, exist_ok=True)

    if not config.extractor_path.is_file():
        raise FileNotFoundError(
            "Essentia extractor not found. Set ESSENTIA_EXTRACTOR or pass --extractor-path. "
            f"Current value: {config.extractor_path}"
        )

    if config.svm_models_dir and not config.svm_models_dir.is_dir():
        raise FileNotFoundError(f"SVM models directory not found: {config.svm_models_dir}")

    if config.svm_models_dir:
        missing_models = [name for name in XTRACTOR_MODEL_FILES if not (config.svm_models_dir / name).is_file()]
        if missing_models and config.fail_on_missing_models:
            raise FileNotFoundError(
                "Missing SVM models required for xtractor-compatible high-level descriptors: " + ", ".join(missing_models)
            )


def write_extractor_profile(config: PipelineConfig) -> Path:
    profile_path = config.temp_dir / "spotseek_essentia_profile.yaml"
    svm_model_lines = ""
    if config.svm_models_dir:
        svm_paths = [config.svm_models_dir / name for name in XTRACTOR_MODEL_FILES if (config.svm_models_dir / name).is_file()]
        if svm_paths:
            svm_model_lines = "\n".join(f"      - {to_posix_path(path)}" for path in svm_paths)
    highlevel_compute = 1 if svm_model_lines else 0
    stats_yaml = ", ".join(f'\"{stat}\"' for stat in config.profile_stats)

    profile = f"""outputFormat: json
outputFrames: 0
requireMbid: false
indent: 2
analysisSampleRate: 44100.0

lowlevel:
  frameSize: 2048
  hopSize: 1024
  zeroPadding: 0
  windowType: blackmanharris62
  silentFrames: noise
  stats: [{stats_yaml}]

rhythm:
  method: degara
  minTempo: 40
  maxTempo: 208
  stats: [{stats_yaml}]

tonal:
  frameSize: 4096
  hopSize: 2048
  zeroPadding: 0
  windowType: blackmanharris62
  silentFrames: noise
  stats: [{stats_yaml}]

highlevel:
  compute: {highlevel_compute}"""
    if svm_model_lines:
        profile += f"\n  svm_models:\n{svm_model_lines}\n"
    else:
        profile += "\n"
    profile += """
chromaprint:
  compute: 0
"""
    profile_path.write_text(profile, encoding="utf-8")
    return profile_path


def process_file(source_path: Path, config: PipelineConfig, profile_path: Path) -> None:
    relative_path = source_path.relative_to(config.input_dir)
    destination_path = unique_destination(config.output_dir / relative_path)
    destination_path.parent.mkdir(parents=True, exist_ok=True)

    extractor_output_path = config.temp_dir / f"spotseek_{safe_stem(destination_path)}.json"
    try:
        run_essentia_extractor(config.extractor_path, source_path, extractor_output_path, profile_path)

        raw_descriptors = json.loads(extractor_output_path.read_text(encoding="utf-8"))
        pruned_descriptors = prune_payload(raw_descriptors, config.prune_rules)
        xtractor_summary = build_xtractor_summary(raw_descriptors)

        shutil.move(str(source_path), str(destination_path))
        sidecar_path = destination_path.with_name(destination_path.name + ".essentia.json")
        write_sidecar(sidecar_path, source_path, destination_path, pruned_descriptors, xtractor_summary, config)
    finally:
        delete_file(extractor_output_path)

    delete_if_empty(source_path.parent, stop_at=config.input_dir)
    print(f"Processed {source_path.name} -> {destination_path}")


def run_essentia_extractor(extractor_path: Path, input_path: Path, output_path: Path, profile_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [str(extractor_path), str(input_path), str(output_path), str(profile_path)]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(
            "Essentia extraction failed with code "
            f"{completed.returncode}. stdout={completed.stdout.strip()} stderr={completed.stderr.strip()}"
        )
    if not output_path.is_file():
        raise FileNotFoundError(f"Expected Essentia output file was not created: {output_path}")


def write_sidecar(
    sidecar_path: Path,
    source_path: Path,
    destination_path: Path,
    descriptors: dict[str, Any],
    xtractor_summary: dict[str, Any],
    config: PipelineConfig,
) -> None:
    payload = {
        "pipeline": {
            "name": "spotseek-essentia-pipeline",
            "version": 1,
            "input_dir": str(config.input_dir),
            "output_dir": str(config.output_dir),
            "extractor_path": str(config.extractor_path),
            "svm_models_dir": str(config.svm_models_dir) if config.svm_models_dir else None,
            "prune_rules": config.prune_rules,
            "profile_stats": config.profile_stats,
        },
        "files": {
            "source_path": str(source_path),
            "output_path": str(destination_path),
            "sidecar_path": str(sidecar_path),
        },
        "xtractor_summary": xtractor_summary,
        "descriptors": descriptors,
    }
    sidecar_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def prune_payload(payload: Any, prune_rules: Iterable[str], path: tuple[str, ...] = ()) -> Any:
    dotted_path = ".".join(path)
    if dotted_path and should_prune(dotted_path, prune_rules):
        return None

    if isinstance(payload, dict):
        result = {}
        for key, value in payload.items():
            child = prune_payload(value, prune_rules, path + (key,))
            if child is not None:
                result[key] = child
        return result

    if isinstance(payload, list):
        return [prune_payload(value, prune_rules, path) if isinstance(value, (dict, list)) else value for value in payload]

    return payload


def should_prune(dotted_path: str, prune_rules: Iterable[str]) -> bool:
    lowered = dotted_path.lower()
    for rule in prune_rules:
        rule_lower = rule.lower()
        if lowered == rule_lower or lowered.startswith(rule_lower + "."):
            return True
    if lowered.endswith(".cov") or lowered.endswith(".icov"):
        return True
    return False


def build_xtractor_summary(payload: dict[str, Any]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for field, (path, value_type) in XTRACTOR_TARGETS.items():
        value = extract_value(payload, path)
        if value is None:
            continue
        if value_type == "integer":
            summary[field] = int(round(float(value)))
        elif value_type == "float":
            summary[field] = float(value)
        elif value_type == "string":
            summary[field] = str(value)
        else:
            summary[field] = value
    return summary


def extract_value(payload: dict[str, Any], dotted_path: str) -> Any:
    current: Any = payload
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def unique_destination(candidate: Path) -> Path:
    if not candidate.exists():
        return candidate
    stem = candidate.stem
    suffix = candidate.suffix
    parent = candidate.parent
    counter = 1
    while True:
        alt = parent / f"{stem} ({counter}){suffix}"
        if not alt.exists():
            return alt
        counter += 1


def delete_file(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        return


def delete_if_empty(directory: Path, stop_at: Path) -> None:
    current = directory
    stop_at_resolved = stop_at.resolve()
    while True:
        try:
            current_resolved = current.resolve()
        except FileNotFoundError:
            return
        if current_resolved == stop_at_resolved:
            return
        try:
            current.rmdir()
        except OSError:
            return
        current = current.parent


def safe_stem(path: Path) -> str:
    return "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in path.stem)


def to_posix_path(path: Path) -> str:
    return path.as_posix()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"FATAL: {exc}")
        raise SystemExit(1)
