
import json
import sys
from pathlib import Path
from faster_whisper import WhisperModel

if len(sys.argv) != 2:
    print("Usage: python transcribe_batch.py <batch_directory>")
    sys.exit(1)

batch_dir = Path(sys.argv[1]).expanduser().resolve()
audio_path = batch_dir / "audio.wav"
output_path = batch_dir / "transcript.json"

if not audio_path.is_file():
    sys.exit(f"Audio file not found: {audio_path}")

print(f"Loading small Whisper model on CPU for {audio_path}")
model = WhisperModel(
    "small",
    device="cpu",
    compute_type="int8",
)

segments, info = model.transcribe(
    str(audio_path),
    task="transcribe",
    language="en",
    beam_size=5,
    vad_filter=False,
)

results = []
for segment in segments:
    item = {
        "start_seconds": round(segment.start, 3),
        "end_seconds": round(segment.end, 3),
        "text": segment.text.strip(),
    }
    results.append(item)
    print(
        f"[{item['start_seconds']:.3f}–"
        f"{item['end_seconds']:.3f}] {item['text']}"
    )

payload = {
    "schema_version": 1,
    "audio_file": str(audio_path),
    "language": info.language,
    "language_probability": round(info.language_probability, 4),
    "model": "small",
    "segments": results,
}

tmp_path = output_path.with_suffix(".json.tmp")
tmp_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
tmp_path.replace(output_path)

print(f"\nLanguage: {info.language}")
print(f"Segments: {len(results)}")
print(f"Saved: {output_path}")
