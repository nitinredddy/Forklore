from pathlib import Path
import re
from forklore.common import run_command, atomic_json

def detect_shot_changes(source: Path, media_id: str, media_root: Path,
                        batches: list[dict], threshold: float = 0.30) -> dict:
    candidates=[]
    for b in batches:
        r=run_command(["ffmpeg","-nostdin","-hide_banner","-loglevel","info",
            "-ss",str(b["start_seconds"]),"-i",str(source),"-t",str(b["duration_seconds"]),
            "-vf",f"select='gt(scene,{threshold})',showinfo","-an","-f","null","-"])
        for m in re.finditer(r"pts_time:([0-9]+(?:\.[0-9]+)?)",r.stderr):
            ts=b["start_seconds"]+float(m.group(1))
            if b["start_seconds"] <= ts < b["end_seconds"]:
                candidates.append({"timestamp_seconds":round(ts,3),
                    "batch_id":b["batch_id"],"threshold":threshold,
                    "kind":"shot_change_candidate"})
    candidates.sort(key=lambda x:x["timestamp_seconds"])
    dedup=[]
    for c in candidates:
        if not dedup or c["timestamp_seconds"]-dedup[-1]["timestamp_seconds"] > .1:
            dedup.append(c)
    out={"schema_version":1,"media_id":media_id,"threshold":threshold,
         "interpretation":"Shot-change candidates, not verified narrative scenes.",
         "candidate_count":len(dedup),"candidates":dedup}
    atomic_json(media_root/"shot_change_candidates.json",out)
    return {"candidate_count":len(dedup)}
