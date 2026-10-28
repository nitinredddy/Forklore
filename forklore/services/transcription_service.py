from pathlib import Path
from forklore.common import atomic_json
import json

def transcribe_media(media_id: str, media_root: Path, batches: list[dict],
                     language: str, model_name: str, force: bool = False) -> dict:
    from faster_whisper import WhisperModel
    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    batch_results = []
    for b in batches:
        audio = Path(b["audio_path"]) if b.get("audio_path") else None
        if not audio or not audio.exists():
            continue
        out = media_root / b["batch_id"] / "transcript.json"
        if out.exists() and not force:
            try:
                old = json.loads(out.read_text(encoding="utf-8"))
                if old.get("media_id") == media_id and old.get("model") == model_name and old.get("language_requested") == language:
                    batch_results.append((b, old))
                    print(f"[skip] transcription {b['batch_id']}")
                    continue
            except Exception:
                pass
        print(f"[transcribe] {b['batch_id']}")
        lang = None if language == "auto" else language
        segments, info = model.transcribe(str(audio), language=lang, task="transcribe",
                                          beam_size=5, vad_filter=True)
        out_segments = []
        for s in segments:
            txt = (s.text or "").strip()
            if not txt or s.end < s.start or s.start < 0:
                continue
            out_segments.append({"segment_id":f"{media_id}_{b['batch_id']}_{len(out_segments)+1:06d}",
                "start_seconds":float(s.start),"end_seconds":float(s.end),"text":txt,
                "avg_logprob":getattr(s,"avg_logprob",None),
                "no_speech_probability":getattr(s,"no_speech_prob",None)})
        data = {"schema_version":2,"media_id":media_id,"batch_id":b["batch_id"],
            "time_basis":"batch_relative_seconds","language":getattr(info,"language",None),
            "language_probability":getattr(info,"language_probability",None),
            "language_requested":language,"model":model_name,
            "segments":out_segments,"status":"completed" if out_segments else "completed_empty",
            "warning":None if out_segments else "No speech segments returned"}
        atomic_json(out,data)
        batch_results.append((b,data))
    merged=[]
    for b,d in batch_results:
        for s in d.get("segments",[]):
            merged.append({**s,"local_start_seconds":s["start_seconds"],
                "local_end_seconds":s["end_seconds"],
                "start_seconds":b["start_seconds"]+s["start_seconds"],
                "end_seconds":b["start_seconds"]+s["end_seconds"],
                "batch_start_seconds":b["start_seconds"],"batch_id":b["batch_id"]})
    merged.sort(key=lambda x:(x["start_seconds"],x["end_seconds"]))
    overlaps=[]
    for prev,cur in zip(merged,merged[1:]):
        if cur["start_seconds"] < prev["end_seconds"]:
            overlaps.append({"previous_segment_id":prev["segment_id"],
                "current_segment_id":cur["segment_id"],
                "overlap_seconds":round(prev["end_seconds"]-cur["start_seconds"],3)})
    result={"schema_version":2,"media_id":media_id,"time_basis":"global_media_seconds",
        "segments":merged,"segment_count":len(merged),"overlaps":overlaps,
        "warnings":["No transcript segments were produced"] if not merged else []}
    atomic_json(media_root/"transcript.json",result)
    (media_root/"transcript.txt").write_text(
        "\n".join(f"[{s['start_seconds']:.3f}-{s['end_seconds']:.3f}] {s['text']}" for s in merged)
        + ("\n" if merged else ""),encoding="utf-8")
    return {"segment_count":len(merged),"overlap_count":len(overlaps)}
