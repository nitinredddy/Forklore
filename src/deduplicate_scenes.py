import json
from pathlib import Path

root = Path.home() / "afterglow/data/processed/e83b51f5bdeb7f4b"
input_path = root / "scene_candidates.json"
output_path = root / "scene_boundaries.json"

data = json.loads(input_path.read_text())
candidates = sorted(data["all_candidate_timestamps_seconds"])

gap_seconds = 1.0
groups = []

for timestamp in candidates:
    if not groups or timestamp - groups[-1][-1] > gap_seconds:
        groups.append([timestamp])
    else:
        groups[-1].append(timestamp)

boundaries = [
    {
        "timestamp_seconds": group[0],
        "grouped_candidates": group,
        "candidate_count": len(group),
    }
    for group in groups
]

output = {
    "movie_id": data["movie_id"],
    "threshold": data["threshold"],
    "deduplication_gap_seconds": gap_seconds,
    "candidate_group_count": len(boundaries),
    "boundaries": boundaries,
}

output_path.write_text(json.dumps(output, indent=2) + "\n")

print(f"Raw candidates: {len(candidates)}")
print(f"Deduplicated candidates: {len(boundaries)}")
print(f"Saved: {output_path}")
print("\nCandidate timestamps:")
for item in boundaries:
    print(
        f"{item['timestamp_seconds']:7.3f}s "
        f"(grouped {item['candidate_count']})"
    )
