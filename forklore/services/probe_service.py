from pathlib import Path
from forklore.common import run_command
import json

def probe_media(source: Path) -> dict:
    result = run_command(["ffprobe", "-v", "error", "-show_format", "-show_streams",
                          "-of", "json", str(source)])
    raw = json.loads(result.stdout)
    fmt = raw.get("format", {})
    streams = raw.get("streams", [])
    duration = float(fmt.get("duration") or max(
        [float(s.get("duration", 0) or 0) for s in streams] + [0]))
    if duration <= 0:
        raise ValueError("Could not determine a positive media duration")
    video = [s for s in streams if s.get("codec_type") == "video"]
    audio = [s for s in streams if s.get("codec_type") == "audio"]
    return {
        "duration_seconds": duration, "format_name": fmt.get("format_name"),
        "size_bytes": int(fmt.get("size") or source.stat().st_size),
        "has_video": bool(video), "has_audio": bool(audio),
        "video_streams": [{"index":s.get("index"),"codec":s.get("codec_name"),
            "width":s.get("width"),"height":s.get("height"),
            "avg_frame_rate":s.get("avg_frame_rate"),"time_base":s.get("time_base")} for s in video],
        "audio_streams": [{"index":s.get("index"),"codec":s.get("codec_name"),
            "sample_rate":s.get("sample_rate"),"channels":s.get("channels"),
            "channel_layout":s.get("channel_layout")} for s in audio],
    }
