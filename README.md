# Forklore

**Making movies explorable, not just watchable.**

Forklore is building an AI-powered interactive layer for movies: a system designed to understand the characters, scenes, events, and relationships that make up a story, and eventually let audiences explore narratives in entirely new ways.

## The Vision

Imagine asking a movie why a character made a particular decision, tracing how an early scene foreshadows a later twist, exploring how relationships evolve throughout a story, or discovering how one event influences another.

Imagine going further: exploring alternative decisions and seeing how a story could unfold differently.

Forklore aims to transform movies from passive viewing experiences into interactive, explorable narrative worlds.

## What We're Building

Understanding a movie requires more than transcribing dialogue or summarizing isolated clips. The underlying system must process long-form media, preserve temporal context, and connect information across the entire film.

Forklore is developing the processing foundation for this vision.

### Current Pipeline

The current implementation, version 0.2.0, includes:

- **Media probing:** Inspect media streams and retrieve duration and format information.
- **Batched media processing:** Divide long videos into manageable time intervals.
- **Frame extraction:** Sample video frames at configurable intervals.
- **Audio transcription:** Transcribe audio using Faster-Whisper.
- **Shot-change detection:** Identify candidate visual transitions.
- **Optional OCR:** Extract visible text from sampled frames using Tesseract.
- **Structured manifests:** Record media metadata, processing configuration, batch status, and stage results.
- **Output validation:** Validate generated artifacts and produce a report.

The pipeline runs these stages sequentially and records its outputs locally.

### Product Direction

The longer-term product vision includes:

- Contextual question-answering grounded in movie content.
- Character profiles, relationships, and character-arc exploration.
- Cross-scene connections and event timelines.
- Narrative navigation that links events to relevant moments.
- Interactive exploration of hypothetical storylines and alternative outcomes.

These are roadmap goals, not claims that all capabilities are implemented in the current version.

## Architecture

The current processing flow is:

```text
Long-form video
      |
      v
Media probing and validation
      |
      v
Batch planning
      |
      v
Audio and sampled-frame extraction
      |
      +-------------------+
      |                   |
      v                   v
Audio transcription   Shot-change detection
      |                   |
      +---------+---------+
                |
                v
       Optional frame OCR
                |
                v
      Output validation
                |
                v
 Structured manifests and artifacts
```

This extraction pipeline is the foundation for future narrative-understanding components that connect characters, events, and scenes across a movie.

## Technology

- Python 3.12
- Faster-Whisper for audio transcription
- FFmpeg and FFprobe for media processing
- Tesseract OCR (optional)
- JSON manifests for structured pipeline outputs

## Getting Started

### Prerequisites

- Python 3.10 or newer; Python 3.12 is the development environment.
- FFmpeg and FFprobe installed and available on your PATH.
- Tesseract installed if OCR is required.

On Ubuntu:

```bash
sudo apt update
sudo apt install ffmpeg
```

For optional OCR:

```bash
sudo apt install tesseract-ocr
```

### Installation

Clone the repository and enter the project directory:

```bash
git clone https://github.com/YOUR_USERNAME/forklore.git
cd forklore
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the Python dependency:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Run the Pipeline

Process a local video:

```bash
python -m forklore.cli run /path/to/video.mp4 \
  --output-dir ./forklore_data
```

Useful options:

```text
--batch-seconds 60       Batch duration in seconds
--frame-interval 5       Interval between sampled frames
--language auto          Transcription language
--model small            Whisper model size
--no-transcribe          Disable transcription
--no-shot-detection      Disable shot-change detection
--ocr                    Enable OCR on sampled frames
--force                  Force reprocessing where supported
```

For example, to process a video with OCR enabled:

```bash
python -m forklore.cli run /path/to/video.mp4 \
  --output-dir ./forklore_data \
  --frame-interval 5 \
  --model small \
  --ocr
```

The first transcription run may download the selected Whisper model. Processing speed and memory requirements depend on the model and hardware.

### Outputs

The pipeline writes results under the output directory, organized by a media identifier derived from the input file's SHA-256 hash.

Outputs include a manifest, sampled-frame indexes, per-batch artifacts, transcription results where applicable, and a validation report.

Generated outputs and source videos are local data; they are not included in this repository.

## Project Status

Forklore is an early-stage project.

The current focus is building a reliable foundation for processing long-form video and producing structured, validated outputs. Higher-level narrative understanding, persistent character and event relationships, and interactive story exploration remain part of the broader product direction.

## Contributing

The project is evolving as the underlying pipeline develops. Issues, technical feedback, and ideas for improving long-form video understanding are welcome.

## License

No open-source license has been applied yet. All rights are reserved by default unless a separate license is added.
