import json
from pathlib import Path

root = Path.home() / "afterglow"
manifest_path = root / "data/manifests/e83b51f5bdeb7f4b.json"
manifest = json.loads(manifest_path.read_text())

interval = manifest["frame_interval_seconds"]
movie_root = root / "data/processed" / manifest["movie_id"]
frames = []

for batch in manifest["batches"]:
    frames_dir = movie_root / batch["batch_id"] / "frames"
    start = batch["start_seconds"]

    for i, frame_path in enumerate(
        sorted(frames_dir.glob("frame_*.jpg"))
    ):
        frames.append({
            "frame_id": f"{batch['batch_id']}_{frame_path.stem}",
            "batch_id": batch["batch_id"],
            "path": str(frame_path),
            "timestamp_seconds": round(start + i * interval, 3),
            "timestamp_basis": "estimated_from_extraction_interval",
        })

output_path = movie_root / "frames.json"
output_path.write_text(
    json.dumps(frames, indent=2) + "\n",
    encoding="utf-8",
)

print(f"Frames indexed: {len(frames)}")
print(f"Saved: {output_path}")
print("\nFirst 5 entries:")
for frame in frames[:5]:
    print(
        f"{frame['timestamp_seconds']:7.3f}s  "
        f"{frame['frame_id']}  {frame['path']}"
    )
