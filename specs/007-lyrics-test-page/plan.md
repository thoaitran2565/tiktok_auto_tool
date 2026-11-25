# Implementation Plan: Lyrics Testing Page (/test)

**Branch**: `007-lyrics-test-page` | **Date**: 2026-11-21 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/007-lyrics-test-page/spec.md`

## Summary

Build a dedicated, high-speed lyrics testing web interface served at `/test` using `templates/test.html`. The page allows creators to test audio extraction, Whisper STT speech recognition, and Gemini AI lyrics cleansing on video files in seconds without generating or encoding MP4 videos. The interface features a streamlined setup bar (only requiring the video folder), single and batch testing controls, real-time status indicators, and an interactive side-by-side modal to compare raw Whisper transcripts with AI-refined lyrics.

## Technical Context

**Language/Version**: Python 3.8+ (Flask backend) / Vanilla ECMAScript 2022+ & CSS3 (Single-Page UI)

**Primary Dependencies**: Flask, Whisper (`TranscriptionService`), Google GenAI SDK, MoviePy (audio extraction only), FontAwesome 6

**Storage**: In-memory test queue state, `config.json` (reading configured video folder)

**Testing**: Bytecode verification (`py_compile`), endpoint integration validation, browser verification per `quickstart.md`

**Target Platform**: Windows 10/11 Local Environment

**Project Type**: Local Web Automation Tool (Flask Controller + Domain Services + Modular SPA)

**Performance Goals**:
- Test completion per 30s video: $\le 10–12$s
- 0 MB video files written to disk
- Instant UI modal response (<50ms)

**Constraints**:
- Zero video encoding (MoviePy / FFmpeg video rendering strictly skipped)
- Automatic cleanup of scratch audio files (`outputs/temp_test_audio_*.mp3`)
- Resilient 15s timeout on Gemini AI with instant fallback to clean raw Whisper transcript (Constitution Principle IV)
- Visual styling and tokens matching `index.html` (Constitution Principle II)

**Scale/Scope**: Handles folders of 10–60+ videos; responsive layout on standard desktop displays.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I: Pipeline Modularity & Decoupled Core**: **PASS**. Test execution reuses decoupled `TranscriptionService` and `clean_lyrics_with_ai` functions directly, fully independent of the 6-stage video rendering pipeline.
- **Principle II: Standard 9:16 Media Formatting & Visual Integrity**: **PASS**. The test interface preserves the project's consistent dark mode styling and responsive typography. No non-standard video formats are generated.
- **Principle III: Fail-Safe Media & Resource Management (NON-NEGOTIABLE)**: **PASS**. Temporary scratch audio clips are deleted immediately upon test completion in a `finally` block; no permanent video files are produced.
- **Principle IV: Resilient AI & External Service Degradation**: **PASS**. Reuses the 15-second timeout guard on Gemini API calls, with seamless fallback to raw Whisper transcripts.
- **Principle V: Observability & Asynchronous Processing**: **PASS**. Real-time item status (`Chờ test`, `Đang xử lý`, `Hoàn thành`, `Lỗi`) and processing elapsed timings are reflected live on the UI.

## Project Structure

### Documentation (this feature)

```text
specs/007-lyrics-test-page/
├── spec.md              # Feature specification & user clarifications
├── plan.md              # This implementation plan
├── research.md          # Architectural decisions & pattern choices
├── data-model.md        # Entities & state lifecycle
├── quickstart.md        # Validation scenarios & test steps
├── contracts/
│   └── test-api-contract.md   # Endpoint contracts for /test & test APIs
└── checklists/
    └── requirements.md  # Spec quality checklist (16/16 pass)
```

### Source Code Layout

```text
d:\Code\tools\tiktok_auto_render_tool/
├── app.py                          # Flask routing: /test, /api/test-scan-videos, /api/test-lyrics
├── extract_lyrics.py               # Shared Whisper STT & Gemini cleansing routines
├── services/
│   ├── scanner_service.py          # Fast video enumeration
│   ├── config_service.py           # Video folder configuration loader
│   └── transcription_service.py     # In-memory cached Whisper singleton
└── templates/
    ├── index.html                  # Main render page (add navigation link to /test)
    ├── manage.html                 # Video management page (add navigation link to /test)
    └── test.html                   # NEW: Dedicated lyrics testing single-page interface
```

## Complexity Tracking

*No architectural violations or complexity exceptions identified.*
