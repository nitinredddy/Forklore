from pathlib import Path
import shutil
from forklore.common import run_command, atomic_json

def extract_ocr(media_id: str, media_root: Path, frame_records: list[dict]) -> dict:
    if not shutil.which("tesseract"):
        raise RuntimeError("OCR requested but tesseract is not installed")
    records=[]
    for fr in frame_records:
        try:
            r=run_command(["tesseract",fr["path"],"stdout","--psm","6"])
            txt=r.stdout.strip()
        except Exception as e:
            txt=""
            records.append({"frame_id":fr["frame_id"],"timestamp_seconds":fr["timestamp_seconds"],
                            "text":txt,"status":"failed","error":str(e)})
            continue
        records.append({"frame_id":fr["frame_id"],"timestamp_seconds":fr["timestamp_seconds"],
                        "text":txt,"status":"completed" if txt else "completed_empty","engine":"tesseract"})
    out={"schema_version":1,"media_id":media_id,"records":records}
    atomic_json(media_root/"ocr.json",out)
    return {"frame_count":len(records),"frames_with_text":sum(bool(x.get("text")) for x in records)}
