# Forklore Architecture

## Current implementation

```mermaid
flowchart TD
    A[Long-form video] --> B[Media probing and batch planning]
    B --> C[FFmpeg media extraction]
    C --> D[Sampled frames and audio]
    D --> E[Faster-Whisper transcription]
    D --> F[Shot-change detection]
    D --> G[Optional Tesseract OCR]
    E --> H[Structured outputs]
    F --> H
    G --> H
    H --> I[Output validation]
    I --> J[JSON manifest and validation report]
```

## Future direction

The current pipeline provides the foundation for future narrative-understanding
components connecting characters, events, scenes, and relationships across movies.
Contextual question-answering and interactive story exploration are longer-term
goals, not claims about the current implementation.
