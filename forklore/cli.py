import argparse, sys
from pathlib import Path
from forklore.config import PipelineConfig
from forklore.pipeline import execute_pipeline

def main():
    parser=argparse.ArgumentParser(description="Forklore sequential media extraction pipeline")
    sub=parser.add_subparsers(dest="command",required=True)
    p=sub.add_parser("run",help="Run extraction services sequentially")
    p.add_argument("source",type=Path)
    p.add_argument("--output-dir",type=Path,default=Path("forklore_data"))
    p.add_argument("--batch-seconds",type=float,default=60)
    p.add_argument("--frame-interval",type=float,default=5)
    p.add_argument("--language",default="auto",help="auto, en, hi, etc.")
    p.add_argument("--model",default="small")
    p.add_argument("--no-transcribe",action="store_true")
    p.add_argument("--no-shot-detection",action="store_true")
    p.add_argument("--ocr",action="store_true")
    p.add_argument("--force",action="store_true")
    args=parser.parse_args()
    try:
        execute_pipeline(PipelineConfig(source=args.source,output_dir=args.output_dir,
            batch_seconds=args.batch_seconds,frame_interval=args.frame_interval,
            language=args.language,whisper_model=args.model,
            enable_transcription=not args.no_transcribe,
            enable_shot_detection=not args.no_shot_detection,
            enable_ocr=args.ocr,force=args.force))
    except Exception as exc:
        print(f"PIPELINE FAILED: {type(exc).__name__}: {exc}",file=sys.stderr)
        sys.exit(1)

if __name__=="__main__":
    main()
