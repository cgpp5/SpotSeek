import sys
import json
from pathlib import Path

# Args esperados:
# 1: artist
# 2: title
# 3: album
# 4: username

artist, title, album, user = sys.argv[1:5]

key = f"{artist}|{title}|{album}".lower()
redownload_dir = Path(r"C:\Program Files\SpotSeek\pending_redownload")
redownload_dir.mkdir(exist_ok=True)
json_path = redownload_dir / "failed_variants.json"

if json_path.exists():
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
else:
    data = {}

entry = data.setdefault(key, {"hashes": {}, "banned_users": []})

users = entry.setdefault("banned_users", [])

if user not in users:
    users.append(user)
    users[:] = users[:20]  # guard de 20 usuarios

with open(json_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
