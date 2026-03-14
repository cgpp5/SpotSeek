# SpotSeek Essentia pipeline

This pipeline analyzes every audio file downloaded into `C:\Program Files\SpotSeek\pending` and moves the processed result into `E:\Music`.

## What it does

- runs Essentia `streaming_extractor_music` on each pending file
- computes low-level, rhythm, tonal, and optional high-level descriptors
- keeps the full aggregated descriptor payload
- omits very heavy outputs such as histograms, covariance matrices, beat position sequences, and chromaprints
- creates a sidecar JSON file next to the output audio file: `<filename>.essentia.json`
- includes an `xtractor_summary` block that mirrors the main descriptor mapping used by `beets-xtractor`

## Required paths

Set these values in `credentials.env` or pass them as command line arguments:

- `ESSENTIA_EXTRACTOR=C:\Program Files\SpotSeek\essentia\streaming_extractor_music.exe`
- `ESSENTIA_SVM_MODELS_DIR=C:\Program Files\SpotSeek\essentia\models`
- `SPOTSEEK_PENDING_DIR=C:\Program Files\SpotSeek\pending`
- `SPOTSEEK_LIBRARY_DIR=E:\Music`
- `SPOTSEEK_PIPELINE_THREADS=1`

The SVM models directory should contain the same high-level models expected by `beets-xtractor`, including:

- `danceability.history`
- `gender.history`
- `genre_rosamerica.history`
- `mood_acoustic.history`
- `mood_aggressive.history`
- `mood_electronic.history`
- `mood_happy.history`
- `mood_sad.history`
- `mood_party.history`
- `mood_relaxed.history`
- `voice_instrumental.history`
- `moods_mirex.history`

## Manual execution

```bat
py -3 tools\essentia_pipeline.py ^
  --input-dir "C:\Program Files\SpotSeek\pending" ^
  --output-dir "E:\Music" ^
  --extractor-path "C:\Program Files\SpotSeek\essentia\streaming_extractor_music.exe" ^
  --svm-models-dir "C:\Program Files\SpotSeek\essentia\models"
```

## Output

For an audio file like:

- `E:\Music\Artist - Track.flac`

The pipeline creates:

- `E:\Music\Artist - Track.flac.essentia.json`

That sidecar file contains:

- pipeline metadata
- source and destination paths
- `xtractor_summary`
- the full Essentia aggregated descriptor payload after pruning heavy sections
