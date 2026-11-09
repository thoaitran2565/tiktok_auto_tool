# Implementation Plan: Fast Video Render Pipeline & Performance Optimization

**Branch**: `006-render-speed-optimization` | **Date**: 2026-11-09 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/006-render-speed-optimization/spec.md`

## Summary

This plan addresses the primary bottlenecks causing ~3 to 4 minute render times per 30-second video:
1. **Direct High-Speed FFmpeg Media Encoding Engine**: Replaces MoviePy's slow Python per-frame generator loops with direct native FFmpeg stream muxing and auto-detected hardware acceleration (`h264_qsv`, `h264_mf`, `h264_nvenc`) with `libx264 -preset ultrafast` software fallback, slashing Stage 5 from ~130s down to $\le 15$s.
2. **In-Memory Whisper Singleton Caching & `faster-whisper`**: Eliminates cold disk re-loading of Whisper weights on every video, reducing Stage 2 from ~25s down to $\le 8$s.
3. **Resilient AI Lyric Refinement with 15s Timeout**: Prevents cloud API response delays from blocking the render queue.
4. **Asynchronous Queue Stage Pipelining**: Pre-fetches Audio, Transcription, and Lyrics for Video $N+1$ in the background while Video $N$ is encoding, reducing batch queue idle time by $> 30\%$.

## Technical Context

**Language/Version**: Python 3.8+ (Server) / Vanilla ECMAScript 2022+ & CSS3 (Client)

**Primary Dependencies**: FFmpeg 9.0+, Pillow (`PIL`), MoviePy, Whisper / `faster-whisper`, Google GenAI SDK, Flask

**Storage**: Local in-memory session queue, `data/render_telemetry.json`, `data/videos_db.json`, `config.json`

**Testing**: Python bytecode verification (`py_compile`), benchmark test harness, browser validation per `quickstart.md`

**Target Platform**: Windows 10/11 Desktop Environment

**Project Type**: Local Web Automation Tool (Flask Controller + Decoupled Domain Services + SPA Frontend)

**Performance Goals**:
- Single-video total render time: $\le 45$s (reduced from ~200s baseline, $> 4\times$ speedup)
- Stage 5 (Media Encoding): $\le 15$s with hardware acceleration, $\le 25$s on software fallback (reduced from ~130s)
- Stage 2 (Transcription): $\le 8$s on warmed model (reduced from ~25s)
- Stage 3 (Lyric Refinement): $\le 15$s hard timeout (eliminating spikes up to 290s)
- Batch throughput: $> 250\%$ increase in finished videos per hour

**Constraints**:
- Strict 1080x1920 vertical format without distortion (Constitution Principle II)
- Steady text overlays, logo placement, and 20% background dimming (Constitution Principle II)
- Clean temporary buffer cleanup upon completion or failure (Constitution Principle III)
- Resilient fallback cascade across hardware and cloud services (Constitution Principle IV)

**Scale/Scope**: Handles queues of 10–50+ videos without memory leaks or UI freezing.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I: Pipeline Modularity & Decoupled Core**: **PASS**. `FFmpegEncoderService` and `TranscriptionService` operate as standalone decoupled modules, testable independently without Flask.
- **Principle II: Standard 9:16 Media Formatting & Visual Integrity**: **PASS**. Output videos strictly adhere to 1080x1920 vertical formatting, 20% background dimming, upper-corner logo, and safe-margin lyrics.
- **Principle III: Fail-Safe Media & Resource Management**: **PASS**. Temporary audio/canvas files are cleaned up reliably in `finalization`; robust encoder fallback guards against driver failures.
- **Principle IV: Resilient AI & External Service Degradation**: **PASS**. Whisper singleton operates locally; Gemini API timeout enforces rapid fallback to raw transcript.
- **Principle V: Observability & Asynchronous Processing**: **PASS**. Telemetry benchmarks track all 6 stages; background pre-fetching runs on non-blocking worker threads.

## Project Structure

### Documentation (this feature)

```text
specs/006-render-speed-optimization/
├── spec.md              # Feature specification & clarifications
├── plan.md              # This implementation plan
├── research.md          # Phase 0 decisions & FFmpeg/Whisper benchmarks
├── data-model.md        # Entities, state lifecycle & telemetry metrics
├── quickstart.md        # Validation scenarios & test steps
├── contracts/
│   ├── encoder-service-contract.md   # Direct FFmpeg encoder & GPU probe
│   ├── whisper-service-contract.md   # In-memory Whisper model cache
│   └── pipeline-contract.md          # Pre-fetch pipelining orchestration
└── checklists/
    └── requirements.md  # Spec quality checklist (16/16 pass)
```

### Source Code Layout

```text
d:\Code\tools\tiktok_auto_render_tool/
├── app.py                          # Slim HTTP controller
├── extract_lyrics.py               # Wrapper delegating to TranscriptionService
├── services/
│   ├── ffmpeg_encoder.py           # NEW: Direct native FFmpeg streaming & GPU probe
│   ├── transcription_service.py     # NEW: In-memory cached Whisper & faster-whisper manager
│   ├── render_pipeline.py          # 6-stage pipelined video rendering engine
│   ├── queue_service.py            # Queue management & pre-fetch coordinator
│   ├── slideshow_service.py        # Slideshow canvas generator
│   ├── scanner_service.py          # Non-blocking media discovery
│   ├── progress_manager.py         # Multi-stage live progress observer
│   └── telemetry_manager.py        # Benchmark telemetry & duration predictions
└── templates/
    └── index.html                  # Frontend UI with live progress indicators
```

**Structure Decision**: Modular domain service architecture. Direct FFmpeg execution is isolated in `services/ffmpeg_encoder.py`, speech transcription in `services/transcription_service.py`, and stage orchestration in `services/render_pipeline.py`.

## Complexity Tracking

*No violations identified. Fully compliant with Constitution principles.*
