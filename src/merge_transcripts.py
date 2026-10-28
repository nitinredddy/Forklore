import json
from pathlib import Path

root = Path.home() / "afterglow/data/processed/e83b51f5bdeb7f4b"
manifest_path = Path.home() / "afterglow/data/manifests/e83b51f5bdeb7f4b.json"

manifest = json.loads(manifest_path.read_text())
merged = []

for batch in manifest["batches"]:
    batch_dir = root / batch["batch_id"]
    transcript_path = batch_dir / "transcript.json"

    if not transcript_path.is_file():
        raise FileNotFoundError(f"Missing transcript: {transcript_path}")

    transcript = json.loads(transcript_path.read_text())
    offset = batch["start_seconds"]

    for segment in transcript["segments"]:
        merged.append({
            "start_seconds": round(offset + segment["start_seconds"], 3),
            "end_seconds": round(offset + segment["end_seconds"], 3),
            "text": segment["text"],
        })

merged.sort(key=lambda x: x["start_seconds"])

output = {
    "schema_version": 1,
    "movie_id": manifest["movie_id"],
    "source_path": manifest["source_path"],
    "duration_seconds": manifest["duration_seconds"],
    "language": "en",
    "segments": merged,
}

output_path = root / "transcript.json"
output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n")

print(f"Total segments: {len(merged)}")
print(f"Saved: {output_path}")
print("\nFirst 3 segments:")
for segment in merged[:3]:
    print(
        f"[{segment['start_seconds']:.3f}–"
        f"{segment['end_seconds']:.3f}] {segment['text']}"
    )

print("\nLast 3 segments:")
for segment in merged[-3:]:
    print(
        f"[{segment['start_seconds']:.3f}–"
        f"{segment['end_seconds']:.3f}] {segment['text']}"
    )
