from __future__ import annotations
import hashlib, json, platform, sys
from pathlib import Path
from forklore import __version__
from forklore.common import atomic_json, require_tool, run_command, sha256_file, utc_now
from forklore.config import PipelineConfig
from forklore.services.probe_service import probe_media
from forklore.services.media_service import extract_media
from forklore.services.transcription_service import transcribe_media
from forklore.services.shot_detection_service import detect_shot_changes
from forklore.services.ocr_service import extract_ocr
from forklore.services.validation_service import validate_outputs

def execute_pipeline(config: PipelineConfig) -> dict:
    config.validate()
    require_tool("ffmpeg"); require_tool("ffprobe")
    source=config.source.expanduser().resolve()
    output=config.output_dir.expanduser().resolve()
    output.mkdir(parents=True,exist_ok=True)
    digest=sha256_file(source)
    media_id=digest[:16]
    root=output/media_id
    root.mkdir(parents=True,exist_ok=True)
    manifest_path=root/"manifest.json"
    media=probe_media(source)
    run_config={"batch_seconds":config.batch_seconds,"frame_interval_seconds":config.frame_interval,
        "language":config.language,"whisper_model":config.whisper_model,
        "transcription":config.enable_transcription,"shot_detection":config.enable_shot_detection,
        "ocr":config.enable_ocr,"pipeline_version":__version__}
    config_hash=hashlib.sha256(json.dumps(run_config,sort_keys=True).encode()).hexdigest()
    previous={}
    if manifest_path.exists():
        try: previous=json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception: previous={}
        if previous.get("source",{}).get("sha256") not in (None,digest):
            raise RuntimeError("Existing manifest source hash mismatch; refusing to reuse outputs.")
    batches=[]
    start=0.0
    while start < media["duration_seconds"]-1e-6:
        end=min(media["duration_seconds"],start+config.batch_seconds)
        batches.append({"batch_id":f"batch_{len(batches):05d}","start_seconds":start,
            "end_seconds":end,"duration_seconds":end-start,"status":"pending"})
        start=end
    manifest={"schema_version":2,"pipeline_version":__version__,"media_id":media_id,
        "manifest_path":str(manifest_path),
        "source":{"path":str(source),"sha256":digest,"size_bytes":source.stat().st_size},
        "media":media,"run_config":run_config,"run_config_hash":config_hash,
        "environment":{"python":sys.version.split()[0],"platform":platform.platform(),
            "ffmpeg":run_command(["ffmpeg","-version"]).stdout.splitlines()[0]},
        "created_at":previous.get("created_at",utc_now()),"updated_at":utc_now(),
        "status":"running","warnings":[],"stages":{},"batches":batches}
    atomic_json(manifest_path,manifest)
    try:
        print("[1/5] Extracting audio and sampled frames")
        batches=extract_media(source,root,batches,media["has_audio"],media["has_video"],
                              config.frame_interval,config.force)
        manifest["batches"]=batches
        frame_records=[]
        for b in batches:
            idx=json.loads((root/b["batch_id"]/"frames.json").read_text(encoding="utf-8"))
            frame_records.extend(idx.get("frames",[]))
        frame_records.sort(key=lambda f:(f["timestamp_seconds"],f["frame_id"]))
        atomic_json(root/"frames.json",{"schema_version":1,"media_id":media_id,
            "timestamp_basis":"estimated_from_extraction_interval","frames":frame_records})
        manifest["stages"]["media"]={"status":"completed","completed_at":utc_now(),
            "frame_count":len(frame_records)}
        atomic_json(manifest_path,manifest)
        if config.enable_transcription and media["has_audio"]:
            print("[2/5] Transcribing audio sequentially")
            result=transcribe_media(media_id,root,batches,config.language,config.whisper_model,config.force)
            manifest["stages"]["transcription"]={"status":"completed" if result["segment_count"] else "completed_empty",
                "completed_at":utc_now(),**result}
        elif config.enable_transcription:
            manifest["stages"]["transcription"]={"status":"skipped","reason":"No audio stream"}
        else:
            manifest["stages"]["transcription"]={"status":"skipped","reason":"Disabled by configuration"}
        atomic_json(manifest_path,manifest)
        if config.enable_shot_detection and media["has_video"]:
            print("[3/5] Detecting shot-change candidates")
            result=detect_shot_changes(source,media_id,root,batches)
            manifest["stages"]["shot_detection"]={"status":"completed","completed_at":utc_now(),**result}
        else:
            manifest["stages"]["shot_detection"]={"status":"skipped","reason":"Disabled or no video stream"}
        atomic_json(manifest_path,manifest)
        if config.enable_ocr and media["has_video"]:
            print("[4/5] Running OCR on sampled frames")
            result=extract_ocr(media_id,root,frame_records)
            manifest["stages"]["ocr"]={"status":"completed","completed_at":utc_now(),**result}
        else:
            manifest["stages"]["ocr"]={"status":"skipped","reason":"Disabled or no video stream"}
        print("[5/5] Validating outputs")
        validation=validate_outputs(root,manifest)
        atomic_json(root/"validation_report.json",validation)
        manifest["stages"]["validation"]={"status":validation["status"],"completed_at":utc_now(),
            "report_path":str(root/"validation_report.json")}
        manifest["warnings"].extend(validation["warnings"])
        manifest["status"]="failed" if validation["errors"] else (
            "completed_with_warnings" if manifest["warnings"] else "completed")
        manifest["updated_at"]=utc_now()
        manifest["completed_at"]=utc_now()
        manifest["summary"]={"duration_seconds":media["duration_seconds"],"batch_count":len(batches),
            "frame_count":len(frame_records),
            "transcript_segment_count":manifest["stages"].get("transcription",{}).get("segment_count"),
            "has_audio":media["has_audio"],"has_video":media["has_video"]}
        atomic_json(manifest_path,manifest)
        print(f"Finished with status: {manifest['status']}")
        print(f"Output: {root}")
        print(f"Manifest: {manifest_path}")
        print(json.dumps(manifest["summary"],indent=2))
        if validation["errors"]:
            print("Validation errors:")
            for error in validation["errors"]: print(" - "+error)
        if manifest["warnings"]:
            print("Warnings:")
            for warning in manifest["warnings"]: print(" - "+warning)
        return manifest
    except Exception as exc:
        manifest["status"]="failed"
        manifest["error"]=f"{type(exc).__name__}: {exc}"
        manifest["updated_at"]=utc_now()
        atomic_json(manifest_path,manifest)
        raise
