import json
from pathlib import Path

root = Path.home() / "afterglow"
movie_id = "e83b51f5bdeb7f4b"
movie_root = root / "data/processed" / movie_id

frames = json.loads((movie_root / "frames.json").read_text())
transcript = json.loads((movie_root / "transcript.json").read_text())
segments = transcript["segments"]

aligned = []

for frame in frames:
    t = frame["timestamp_seconds"]

    matching = [
        segment for segment in segments
        if segment["start_seconds"] <= t < segment["end_seconds"]
    ]

    aligned.append({
        **frame,
        "transcript_segments": matching,
        "alignment_method": "frame_timestamp_inside_transcript_segment",
    })

output_path = movie_root / "frame_transcript_alignment.json"
output_path.write_text(
    json.dumps(aligned, indent=2, ensure_ascii=False) + "\n",
    encoding="utf-8",
)

matched = sum(bool(item["transcript_segments"]) for item in aligned)

print(f"Frames: {len(aligned)}")
print(f"Frames with matching dialogue segment: {matched}")
print(f"Frames without matching dialogue segment: {len(aligned) - matched}")
print(f"Saved: {output_path}")

print("\nFirst 10 alignments:")
for item in aligned[:10]:
    texts = " | ".join(
        segment["text"] for segment in item["transcript_segments"]
    )
    print(f"[{item['timestamp_seconds']:7.3f}s] {texts or '(no matching segment)'}")
