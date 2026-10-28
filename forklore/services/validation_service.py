from pathlib import Path
from forklore.common import load_json

def validate_outputs(media_root: Path, manifest: dict) -> dict:
    errors=[]; warnings=[]
    duration=manifest["media"]["duration_seconds"]
    frames_path=media_root/"frames.json"
    if frames_path.exists():
        frames=load_json(frames_path).get("frames",[])
        for f in frames:
            if not (0 <= f["timestamp_seconds"] <= duration):
                errors.append(f"Frame timestamp outside media duration: {f.get('frame_id')}")
            p=Path(f["path"])
            if not p.is_file() or p.stat().st_size < 500:
                errors.append(f"Missing/invalid frame: {p}")
    if (media_root/"transcript.json").exists():
        transcript=load_json(media_root/"transcript.json")
        for s in transcript.get("segments",[]):
            if s["start_seconds"] < 0 or s["end_seconds"] < s["start_seconds"] or s["end_seconds"] > duration + 2:
                errors.append(f"Invalid transcript timestamps: {s.get('segment_id')}")
        if not transcript.get("segments"):
            warnings.append("Transcript contains zero segments; this is not proof of silence.")
        if transcript.get("overlaps"):
            warnings.append(f"Transcript has {len(transcript['overlaps'])} overlapping adjacent segment pairs.")
    return {"status":"failed" if errors else ("completed_with_warnings" if warnings else "passed"),
            "errors":errors,"warnings":warnings}
