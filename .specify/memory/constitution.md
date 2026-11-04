<!--
Sync Impact Report
------------------
- Version change: Uninitialized -> 1.0.0
- List of modified principles:
  - [PRINCIPLE_1_NAME] -> I. Pipeline Modularity & Decoupled Core
  - [PRINCIPLE_2_NAME] -> II. Standard 9:16 Media Formatting & Visual Integrity
  - [PRINCIPLE_3_NAME] -> III. Fail-Safe Media & Resource Management (NON-NEGOTIABLE)
  - [PRINCIPLE_4_NAME] -> IV. Resilient AI & External Service Degradation
  - [PRINCIPLE_5_NAME] -> V. Observability & Asynchronous Processing
- Added sections:
  - Technical Standards & Performance Constraints
  - Development Workflow & Quality Gates
- Removed sections: None
- Follow-up TODOs: None (all template placeholders resolved)
-->

# TikTok Auto Render Tool Constitution

## Core Principles

### I. Pipeline Modularity & Decoupled Core
Media processing routines (audio extraction, lyrics transcription, AI text cleansing, image compositing, video rendering) MUST operate as decoupled, standalone modules with strict input/output contracts. Core video processing logic MUST NOT be tightly bound to the Flask HTTP request cycle; processing routines MUST be independently testable and executable via script, CLI, or test harness without requiring a running web server.

### II. Standard 9:16 Media Formatting & Visual Integrity
Every rendered video MUST strictly adhere to standard vertical short-form video specifications (`1080x1920` resolution, 9:16 aspect ratio). Visual scaling MUST preserve original image aspect ratios—stretching or distortion is prohibited. Non-filling imagery MUST use solid black matting or blurred backgrounds. Visual overlays (including 20% background brightness reduction, contrast stroke on text, logo placement in upper corner, and safe-margin bounded lyrics capped at 90% height) MUST remain consistent and readable across target mobile screens.

### III. Fail-Safe Media & Resource Management (NON-NEGOTIABLE)
All file system mutations, temporary scratch video generation, and source file removals MUST be guarded with defensive validations. Temporary video/audio intermediate clips (e.g., MoviePy temp files, FFmpeg buffers) MUST be cleaned up reliably upon completion or failure. Source media deletion MUST ONLY execute after positive verification that the target output video exists, is non-empty, and has rendered completely without errors.

### IV. Resilient AI & External Service Degradation
Integrations with AI models (Whisper STT, Gemini API) MUST be designed defensively against rate limits, connectivity drops, and model deprecation. The system MUST maintain fallback cascades across multiple Gemini model variants (`gemini-2.5-flash`, `gemini-2.5-flash-lite`, etc.) and fall back gracefully to raw transcripts or un-cleansed lyrics if AI services are unavailable. External API credentials MUST be resolved strictly from environment variables or secure local configuration, never checked into version control.

### V. Observability & Asynchronous Processing
Heavy rendering workflows and batch operations MUST execute asynchronously off the main application thread to prevent request blocking and UI freezes. Real-time rendering status, item-level progress, and operational failures MUST be captured via structured logging and exposed through state APIs for transparent user feedback and diagnostic observability.

## Technical Standards & Performance Constraints

- **Technology Baseline**: Python 3.8+, Flask for local server orchestration, MoviePy / FFmpeg for audio-video composition, Pillow for typography and canvas graphics, and Google GenAI SDK for NLP enhancement.
- **Encoding & Compatibility**: Final exports MUST be encoded in H.264 (video) and AAC/MP3 (audio) inside an MP4 container, ensuring universal playback compatibility across TikTok, YouTube Shorts, and Instagram Reels.
- **Typography & Localization**: Lyrics and text rendering MUST use UTF-8 typography capable of rendering Vietnamese diacritical marks accurately, with automatic font fallback when system-specific fonts are missing.
- **Resource Constraints**: Concurrency MUST be bounded to prevent CPU and memory exhaustion caused by parallel FFmpeg subprocesses on local development machines.

## Development Workflow & Quality Gates

- **Configuration Isolation**: Machine-dependent paths, directory pointers, and API keys MUST reside in `config.json` or `.env` and MUST be ignored by version control.
- **Non-Destructive Testing**: Test fixtures and pipeline validation MUST operate on sample dummy media rather than production input directories.
- **Change Verification**: Any modification to video compositing parameters, coordinate calculations, or audio extraction MUST be verified with representative edge cases (portrait vs. landscape source photos, long lyrics exceeding typical bounds, silent or low-bitrate audio).

## Governance

This Constitution serves as the single source of truth for architectural standards, quality gates, and system principles in the TikTok Auto Render Tool project.
- **Precedence**: Architectural rules and principles defined here supersede conflicting conventions or ad-hoc practices.
- **Amendments**: Amendments require an explicit justification, assessment of impact on existing pipelines, and incrementation of the constitution version.
- **Versioning Policy**: Semantic versioning MUST be applied to this document:
  - MAJOR: Incompatible governance changes, removal or redefinition of Core Principles.
  - MINOR: Addition of new principles, sections, or expanded operational constraints.
  - PATCH: Clarifications, typo fixes, and non-semantic formatting updates.
- **Compliance**: All feature specifications, implementation plans, and automated tasks MUST align with the principles ratified in this document.

**Version**: 1.0.0 | **Ratified**: 2026-11-04 | **Last Amended**: 2026-11-04
