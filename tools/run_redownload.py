#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import subprocess
from pathlib import Path


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--csv", required=True)
    p.add_argument("--pending-dir", required=True)
    p.add_argument("--sldl", required=True)
    p.add_argument("--user", required=True)
    p.add_argument("--pass", dest="password", required=True)
    p.add_argument("--path", required=True)

    # passthrough options
    p.add_argument("--format", default=None)
    p.add_argument("--pref-format", default=None)
    p.add_argument("--min-bitrate", default=None)
    p.add_argument("--concurrent-downloads", default=None)
    p.add_argument("--skip-not-found", action="store_true")
    p.add_argument("--desperate", action="store_true")
    p.add_argument("--artist-maybe-wrong", action="store_true")
    p.add_argument("--on-complete-script", required=True)

    return p.parse_args()


def track_key(artist: str, title: str, album: str) -> str:
    return f"{artist}|{title}|{album}".lower()


def main():
    args = parse_args()

    pending_dir = Path(args.pending_dir)
    failed_json = Path(args.pending_dir) / "pending_redownload" / "failed_variants.json"

    if failed_json.exists():
        with open(failed_json, "r", encoding="utf-8") as f:
            failed_variants = json.load(f)
    else:
        failed_variants = {}

    # Leer CSV de redownload
    with open(args.csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    for row in rows:
        artist = row.get("Artist Name", "").strip()
        title = row.get("Track Name", "").strip()
        album = row.get("Album", "").strip()

        if not artist or not title:
            continue

        key = track_key(artist, title, album)
        entry = failed_variants.get(key, {})
        banned_users = entry.get("banned_users", [])

        # Guard duro: si ya hay 20 usuarios baneados, no insistimos más
        if len(banned_users) >= 20:
            print(f"  -> {artist} - {title}: límite de usuarios alcanzado, se omite")
            continue

        cmd = [
            args.sldl,
            args.csv,
            "--user", args.user,
            "--pass", args.password,
            "--path", args.path,
        ]

        if args.format:
            cmd += ["--format", args.format]
        if args.pref_format:
            cmd += ["--pref-format", args.pref_format]
        if args.min_bitrate:
            cmd += ["--min-bitrate", args.min_bitrate]
        if args.concurrent_downloads:
            cmd += ["--concurrent-downloads", args.concurrent_downloads]
        if args.skip_not_found:
            cmd.append("--skip-not-found")
        if args.desperate:
            cmd.append("--desperate")
        if args.artist_maybe_wrong:
            cmd.append("--artist-maybe-wrong")

        if banned_users:
            cmd += ["--banned-users", ",".join(banned_users)]

        # on-complete: registrar usuario fallido
        cmd += [
            "--on-complete",
            f"2:r: cmd /c python \"{args.on_complete_script}\" "
            f"\"{{sartist}}\" \"{{stitle}}\" \"{{salbum}}\" \"{{slsk-foldername}}\""
        ]

        print(f"  -> Reintentando: {artist} - {title}")
        subprocess.run(cmd)


if __name__ == "__main__":
    main()
