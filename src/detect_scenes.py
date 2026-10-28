#!/usr/bin/env python3

import json
import subprocess
import re
from pathlib import Path

ROOT = Path.home() / "afterglow"
MOVIE_ID = "e83b51f5bdeb7f4b"

manifest_path = ROOT / "data/manifests" / f"{MOVIE_ID}.json"
manifest = json.loads(manifest_path.read_text())

output_dir = ROOT / "data/processed" / MOVIE_ID
output_path = output_dir / "scene_candidates.json"

# Load prior results so completed batches can be skipped on reruns.
if output_path.exists():
    data = json.loads(output_path.read_text())
else:
    data = {
        "movie_id": MOVIE_ID,
        "threshold": 0.30,
        "batches": {},
    }

for batch in manifest["batches"]:
    batch_id = batch["batch_id"]

    if batch_id in data["batches"]:
        print(f"Skipping already processed {batch_id}")
        continue

    start = float(batch["start_seconds"])
    end = float(batch["end_seconds"])

    print(f"Scanning {batch_id}: {start:.2f}–{end:.2f}s", flush=True)

    command = [
        "ffmpeg",
        "-hide_banner",
        "-nostdin",
        "-loglevel", "info",
        "-ss", str(start),
        "-i", str(manifest["source_path"]),
        "-t", str(end - start),
        "-vf", "select='gt(scene,0.30)',showinfo",
        "-an",
        "-f", "null",
        "-"
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        print(f"FFmpeg failed for {batch_id}:")
        print(result.stderr[-2000:])
        raise SystemExit(result.returncode)

    local_times = [
        float(match)
        for match in re.findall(r"pts_time:([0-9]+(?:\.[0-9]+)?)", result.stderr)
    ]

    candidates = [
        round(start + t, 3)
        for t in local_times
        if 0 <= t <= end - start
    ]

    data["batches"][batch_id] = {
        "start_seconds": start,
        "end_seconds": end,
        "candidate_count": len(candidates),
        "candidate_timestamps_seconds": candidates,
    }

    # Save after every batch so progress survives interruption.
    temp_path = output_path.with_suffix(".json.tmp")
    temp_path.write_text(json.dumps(data, indent=2) + "\n")
    temp_path.replace(output_path)

    print(f"Found {len(candidates)} candidates in {batch_id}", flush=True)

all_candidates = sorted(
    timestamp
    for batch_data in data["batches"].values()
    for timestamp in batch_data["candidate_timestamps_seconds"]
)

data["all_candidate_timestamps_seconds"] = all_candidates
output_path.write_text(json.dumps(data, indent=2) + "\n")

print(f"\nSaved scene candidates to: {output_path}")
print(f"Total candidates: {len(all_candidates)}")
print("Candidates:", all_candidates)
