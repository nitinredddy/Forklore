from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class PipelineConfig:
    source: Path
    output_dir: Path
    batch_seconds: float = 60.0
    frame_interval: float = 5.0
    language: str = "auto"
    whisper_model: str = "small"
    enable_transcription: bool = True
    enable_shot_detection: bool = True
    enable_ocr: bool = False
    force: bool = False

    def validate(self) -> None:
        if not self.source.is_file():
            raise FileNotFoundError(f"Source file does not exist: {self.source}")
        if self.batch_seconds <= 0:
            raise ValueError("batch_seconds must be positive")
        if self.frame_interval <= 0:
            raise ValueError("frame_interval must be positive")
