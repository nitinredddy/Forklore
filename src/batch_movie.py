
#!/usr/bin/env python3

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path.home() / "afterglow"
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
MANIFEST_DIR = ROOT / "data" / "manifests"


def run_command(args):
    return subprocess.run(
        args,
        check=True,
        capture_output=True,
        text=True,
    )


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def probe_duration(path):
    result = run_command([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(path),
    ])
    return float(result.stdout.strip())


def atomic_write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8",
    )
    temporary.replace(path)


def process_batch(movie, movie_id, batch, frame_interval):
    start = batch["start_seconds"]
    end = batch["end_seconds"]
    duration = end - start

    output_dir = (
        PROCESSED_DIR / movie_id / batch["batch_id"]
    )
    audio_path = output_dir / "audio.wav"
    frames_dir = output_dir / "frames"
    output_dir.mkdir(parents=True, exist_ok=True)
    frames_dir.mkdir(parents=True, exist_ok=True)

    # Extract mono, 16 kHz audio for speech recognition.
    if not audio_path.exists():
        run_command([
            "ffmpeg", "-nostdin", "-v", "error", "-y",
            "-ss", str(start),
            "-i", str(movie),
            "-t", str(duration),
            "-map", "0:a:0?",
            "-vn",
            "-ac", "1",
            "-ar", "16000",
            "-c:a", "pcm_s16le",
            str(audio_path),
        ])

    # Extract periodic frames with timestamps relative to the batch.
    existing_frames = list(frames_dir.glob("frame_*.jpg"))
    if not existing_frames:
        run_command([
            "ffmpeg", "-nostdin", "-v", "error", "-y",
            "-ss", str(start),
            "-i", str(movie),
            "-t", str(duration),
            "-vf",
            f"fps=1/{frame_interval},"
            "scale=640:-2",
            "-q:v", "5",
            str(frames_dir / "frame_%05d.jpg"),
        ])

    batch["outputs"] = {
        "audio": str(audio_path) if audio_path.exists() else None,
        "frames_dir": str(frames_dir),
        "frame_count": len(list(frames_dir.glob("frame_*.jpg"))),
    }
    batch["status"] = "media_extracted"
    batch["updated_at"] = datetime.now(timezone.utc).isoformat()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("movie", help="Path to the movie file")
    parser.add_argument(
        "--batch-minutes", type=float, default=5.0
    )
    parser.add_argument(
        "--frame-interval", type=float, default=10.0,
        help="Seconds between sampled frames",
    )
    args = parser.parse_args()

    movie = Path(args.movie).expanduser().resolve()

    if not movie.is_file():
        sys.exit(f"Movie file not found: {movie}")
    if args.batch_minutes <= 0 or args.frame_interval <= 0:
        sys.exit("Batch duration and frame interval must be positive")

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)

    movie_hash = sha256_file(movie)
    movie_id = movie_hash[:16]
    duration = probe_duration(movie)
    batch_seconds = args.batch_minutes * 60

    manifest_path = MANIFEST_DIR / f"{movie_id}.json"

    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    else:
        batches = []
        start = 0.0
        index = 0

        while start < duration:
            end = min(start + batch_seconds, duration)
            batches.append({
                "batch_id": f"batch_{index:05d}",
                "start_seconds": round(start, 3),
                "end_seconds": round(end, 3),
                "status": "pending",
                "outputs": {},
            })
            start = end
            index += 1

        manifest = {
            "schema_version": 1,
            "movie_id": movie_id,
            "source_path": str(movie),
            "source_sha256": movie_hash,
            "duration_seconds": duration,
            "batch_minutes": args.batch_minutes,
            "frame_interval_seconds": args.frame_interval,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "batches": batches,
        }
        atomic_write_json(manifest_path, manifest)

    print(f"Movie ID: {movie_id}")
    print(f"Duration: {duration:.2f} seconds")
    print(f"Batches: {len(manifest['batches'])}")
    print(f"Manifest: {manifest_path}")

    for batch in manifest["batches"]:
        if batch["status"] == "media_extracted":
            continue

        print(
            f"Processing {batch['batch_id']}: "
            f"{batch['start_seconds']:.1f}–"
            f"{batch['end_seconds']:.1f}s"
        )

        batch["status"] = "processing"
        batch["updated_at"] = datetime.now(timezone.utc).isoformat()
        atomic_write_json(manifest_path, manifest)

        try:
            process_batch(
                movie, movie_id, batch, args.frame_interval
            )
        except subprocess.CalledProcessError as exc:
            batch["status"] = "failed"
            batch["error"] = (exc.stderr or str(exc))[-2000:]
            batch["updated_at"] = datetime.now(timezone.utc).isoformat()
            atomic_write_json(manifest_path, manifest)
            print(f"Failed: {batch['batch_id']}: {batch['error']}")
            sys.exit(1)

        atomic_write_json(manifest_path, manifest)

    manifest["status"] = "media_extracted"
    manifest["completed_at"] = datetime.now(timezone.utc).isoformat()
    atomic_write_json(manifest_path, manifest)
    print("All batches extracted successfully.")


if __name__ == "__main__":
    main()
