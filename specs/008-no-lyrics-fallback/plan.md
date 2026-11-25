# Implementation Plan: No-Lyrics Fallback & Chill Video Naming

**Branch**: `008-no-lyrics-fallback` | **Date**: 2026-11-21 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/008-no-lyrics-fallback/spec.md`

## Summary

When audio processing detects no genuine lyrics (empty transcript, noise, instrumental audio, or AI disclaimer notes), the render pipeline automatically bypasses the lyric text image generation and overlay steps. The resulting video is composed solely of the background imagery, upper-right logo watermark, and source audio. Exported videos are automatically routed to `outputs-no-lyrics/` and named `"Cuộc sống chill [timestamp].mp4"` using a Unix timestamp.

## Technical Context

**Language/Version**: Python 3.8+ (current environment: Python 3.14 on Windows)  
**Primary Dependencies**: MoviePy, Pillow, OpenAI Whisper, Google GenAI SDK, Flask  
**Storage**: Local filesystem (`outputs-no-lyrics/`, `outputs/`, `videos_db.json`)  
**Testing**: Standalone python verification scripts in `scratch/` + quickstart validation scenarios  
**Target Platform**: Windows 11 / Local Flask server  
**Project Type**: Standalone desktop/local web utility  
**Performance Goals**: Rendering non-lyric videos completed in < 15 seconds; zero unnecessary PIL typography rasterization  
**Constraints**: 1080x1920 vertical canvas, 9:16 aspect ratio, defensive scratch file cleanup  
**Scale/Scope**: Single-item and batch queue operations across directories with 10–100+ clips  

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I: Pipeline Modularity & Decoupled Core**: PASS. Detection and rendering logic are implemented in modular services (`extract_lyrics.py`, `services/render_pipeline.py`) testable without running the HTTP server.
- **Principle II: Standard 9:16 Media Formatting & Visual Integrity**: PASS. All non-lyric videos retain 1080x1920 resolution, 50% background darkening, logo watermark in top right, and un-distorted aspect ratio.
- **Principle III: Fail-Safe Media & Resource Management (NON-NEGOTIABLE)**: PASS. Scratch audio and slide files are defensively cleaned up in `finally` blocks; destination folder `outputs-no-lyrics/` is verified or created automatically.
- **Principle IV: Resilient AI & External Service Degradation**: PASS. Whisper silence and AI timeouts/disclaimers cleanly trigger fallback to `"Cuộc sống chill [timestamp]"`.
- **Principle V: Observability & Asynchronous Processing**: PASS. Background rendering status updates via structured logs and queue notifications.

## Project Structure

### Documentation (this feature)

```text
specs/008-no-lyrics-fallback/
├── plan.md              # Implementation plan
├── research.md          # Technical research & decisions
├── data-model.md        # Entities, schemas & state transitions
├── quickstart.md        # Validation scenarios
├── contracts/           # Interfaces & contracts
│   └── no-lyrics-contract.md
├── checklists/
│   └── requirements.md
└── tasks.md             # Implementation tasks (/speckit-tasks output)
```

### Source Code Layout

```text
tiktok_auto_render_tool/
├── app.py                      # Flask routing & endpoint state updates
├── extract_lyrics.py           # Lyrics detection, AI cleaning, and non-lyric filtering
├── services/
│   ├── render_pipeline.py      # Core render pipeline, visual generation, naming & routing
│   ├── slideshow_service.py    # Multi-image slide transitions
│   └── scanner_service.py      # Video scanning & metadata extraction
├── outputs/                    # Export folder for videos with lyrics
├── outputs-no-lyrics/          # Dedicated export folder for chill non-lyric videos
├── templates/
│   ├── index.html              # Main rendering queue UI
│   ├── manage.html             # Video management UI
│   └── test.html               # Dedicated lyrics testing interface
└── videos_db.json              # Persistent metadata database
```

**Structure Decision**: Monolithic script and modular services structure maintained; updates isolated to `extract_lyrics.py`, `services/render_pipeline.py`, and `app.py`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| None | All designs conform strictly to Constitution Principles | N/A |
