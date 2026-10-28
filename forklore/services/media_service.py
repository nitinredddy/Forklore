from pathlib import Path
import os
from forklore.common import run_command, atomic_json

def extract_media(source: Path, media_root: Path, batches: list[dict],
                  has_audio: bool, has_video: bool, frame_interval: float,
                  force: bool = False) -> list[dict]:
    for batch in batches:
        batch_dir = media_root / batch["batch_id"]
        batch_dir.mkdir(parents=True, exist_ok=True)
        start, duration = batch["start_seconds"], batch["duration_seconds"]
        audio = batch_dir / "audio.wav"
        if has_audio:
            tmp = batch_dir / "audio.tmp.wav"
            if force or not audio.exists() or audio.stat().st_size < 1000:
                run_command(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
                    "-ss",str(start),"-i",str(source),"-t",str(duration),"-map","0:a:0",
                    "-vn","-ac","1","-ar","16000","-c:a","pcm_s16le",str(tmp)])
                if not tmp.exists() or tmp.stat().st_size < 1000:
                    raise RuntimeError(f"Invalid audio extraction for {batch['batch_id']}")
                os.replace(tmp,audio)
            batch["audio_path"], batch["audio_bytes"] = str(audio), audio.stat().st_size
        else:
            batch["audio_path"] = None
        frames_dir = batch_dir / "frames"
        frames_dir.mkdir(parents=True, exist_ok=True)
        frames = sorted(frames_dir.glob("frame_*.jpg"))
        if force:
            for f in frames: f.unlink()
            frames = []
        if has_video and not frames:
            run_command(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
                "-ss",str(start),"-i",str(source),"-t",str(duration),
                "-vf",f"fps=1/{frame_interval},scale=640:-2","-q:v","4",
                str(frames_dir/"frame_%06d.jpg")])
            frames = sorted(frames_dir.glob("frame_*.jpg"))
        frame_records = []
        for i, fp in enumerate(frames):
            if fp.stat().st_size < 500:
                continue
            frame_records.append({
                "frame_id":f"{batch['batch_id']}_{i+1:06d}", "path":str(fp),
                "timestamp_seconds":min(batch["end_seconds"], start+i*frame_interval),
                "timestamp_basis":"estimated_from_extraction_interval",
                "batch_id":batch["batch_id"], "size_bytes":fp.stat().st_size
            })
        atomic_json(batch_dir/"frames.json", {
            "schema_version":1,"batch_id":batch["batch_id"],"frames":frame_records})
        batch["frame_count"] = len(frame_records)
        batch["status"] = "media_extracted"
    return batches
