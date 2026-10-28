import json
import subprocess
from pathlib import Path

root = Path.home() / "afterglow"
movie_id = "e83b51f5bdeb7f4b"
movie_root = root / "data/processed" / movie_id
video = root / "data/raw/YCVideo.mov"

data = json.loads((movie_root / "scene_boundaries.json").read_text())
output_dir = movie_root / "scene_candidate_frames"
output_dir.mkdir(parents=True, exist_ok=True)

for index, item in enumerate(data["boundaries"], start=1):
    timestamp = item["timestamp_seconds"]
    output = output_dir / f"candidate_{index:02d}_{timestamp:.3f}s.jpg"

    if output.exists():
        continue

    subprocess.run([
        "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-ss", str(timestamp),
        "-i", str(video),
        "-frames:v", "1",
        "-vf", "scale=640:-2",
        "-q:v", "5",
        str(output),
    ], check=True)

print(f"Candidate frames saved to: {output_dir}")
print(f"Frames: {len(list(output_dir.glob('*.jpg')))}")
