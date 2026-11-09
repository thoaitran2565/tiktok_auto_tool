# Tasks: Fast Video Render Pipeline & Performance Optimization

**Input**: Design documents from `/specs/006-render-speed-optimization/`  
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`  
**Organization**: Tasks are grouped by foundational prerequisites and user stories to enable independent implementation and testing.

## Format: `- [ ] [ID] [P?] [Story?] Description with file path`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (`[US1]`, `[US2]`, `[US3]`)
- Clear action and exact file path in every description

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize new service modules and interface scaffolding.

- [X] T001 [P] Create `services/ffmpeg_encoder.py` scaffolding with encoder probing and direct stream rendering interfaces per `contracts/encoder-service-contract.md`
- [X] T002 [P] Create `services/transcription_service.py` scaffolding with in-memory model cache singleton interface per `contracts/whisper-service-contract.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core encoder detection, model cache lifecycle, and telemetry infrastructure.

**⚠️ CRITICAL**: Must complete before user stories to ensure hardware capabilities and telemetry tracking are established.

- [X] T003 Implement hardware & software encoder probe `probe_best_encoder()` in `services/ffmpeg_encoder.py` supporting `h264_qsv`, `h264_mf`, `h264_nvenc`, and `libx264 -preset ultrafast`
- [X] T004 Implement in-memory singleton cache and device/engine selection in `services/transcription_service.py` supporting `faster-whisper` and standard `whisper`
- [X] T005 [P] Extend `services/telemetry_manager.py` schema to record `encoder_backend`, `whisper_engine`, `pipelined` flag, and `speedup_factor` per `data-model.md`

**Checkpoint**: Foundational services ready for video encoding acceleration and speech recognition optimization.

---

## Phase 3: User Story 1 - Accelerated Video Encoding Engine (Priority: P1) 🎯 MVP

**Goal**: Replace MoviePy's slow Python per-frame generator loop with direct native FFmpeg stream muxing and GPU hardware acceleration, reducing Stage 5 from ~130s down to $\le 15$s.

**Independent Test**: Render a single video in the queue. Verify Stage 5 (`media_encoding`) completes in under 15–20s (a 5x–10x reduction from baseline) with exact 1080x1920 vertical output, synchronized audio, and sharp overlays.

### Implementation for User Story 1

- [X] T006 [US1] Implement `render_static_video()` in `services/ffmpeg_encoder.py` for direct single-canvas FFmpeg stream looping (`-loop 1 -i canvas.png -i audio.mp3 -shortest`) with active encoder and ultrafast fallback
- [X] T007 [US1] Implement `render_slideshow_video()` in `services/ffmpeg_encoder.py` for multi-image slideshow videos using native high-throughput FFmpeg stream composition
- [X] T008 [US1] Integrate `FFmpegEncoderService` into Stage 5 (`media_encoding`) of `services/render_pipeline.py`, replacing MoviePy `write_videofile` with direct FFmpeg encoding
- [X] T009 [US1] Ensure standard 9:16 vertical formatting (`1080x1920`), 20% background dimming, upper-corner logo, and safe-margin lyrics overlay integrity in `services/render_pipeline.py` per Constitution Principle II

**Checkpoint**: User Story 1 operational. Media encoding completes in seconds instead of minutes.

---

## Phase 4: User Story 2 - In-Memory Model Caching & Fast Transcription (Priority: P1)

**Goal**: Eliminate cold disk reloading of Whisper weights on every video render and enforce a 15s timeout on Gemini AI, cutting transcription and refinement time to $\le 8$s and $\le 15$s.

**Independent Test**: Render two consecutive videos. Verify the second video begins Whisper transcription instantly without disk reload, finishing in under 8s, and simulate API delay to verify Gemini 15s timeout fallback.

### Implementation for User Story 2

- [X] T010 [US2] Implement `transcribe()` in `services/transcription_service.py` utilizing the warm in-memory model singleton with thread-safe execution
- [X] T011 [US2] Update `extract_raw_lyrics()` in `extract_lyrics.py` to delegate directly to `TranscriptionService.transcribe()`
- [X] T012 [US2] Implement 15-second hard timeout for Gemini API calls in `clean_lyrics_with_ai()` in `extract_lyrics.py` with immediate fallback to clean raw transcript
- [X] T013 [US2] Pre-warm the Whisper model singleton during application startup in `app.py` in a background worker thread

**Checkpoint**: User Story 2 operational. Speech recognition and AI refinement run at maximum speed with zero disk I/O stalls.

---

## Phase 5: User Story 3 - Pipelined Background Processing for Batch Renders (Priority: P2)

**Goal**: Pre-fetch Audio Extraction (Stage 1), Whisper Transcription (Stage 2), and Lyric Refinement (Stage 3) for Video $N+1$ in the background while Video $N$ encodes in FFmpeg (Stage 5), cutting batch idle time by $> 30\%$.

**Independent Test**: Queue 3 videos and execute batch render. Verify Video #2 runs Stages 1–3 concurrently while Video #1 is encoding in Stage 5, transitioning to Stage 5 immediately when Video #1 finishes.

### Implementation for User Story 3

- [X] T014 [US3] Implement `pre_fetch_item()` in `services/render_pipeline.py` to execute Stages 1–4 asynchronously and cache prepared audio and canvas
- [X] T015 [US3] Add thread-safe pre-fetch artifact coordinator in `services/queue_service.py` managing prepared jobs
- [X] T016 [US3] Wire background pre-fetch invocation into `/api/render-single` and queue loop in `app.py` and `templates/index.html`
- [X] T017 [US3] Update timeline progress status rendering in `templates/index.html` to display pre-fetched states on upcoming items cleanly

**Checkpoint**: User Story 3 operational. Batch queue rendering runs with overlapped execution and zero idle gap.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Syntax verification, regression testing, and end-to-end scenario validation.

- [X] T018 [P] Verify Python syntax and import integrity across all service modules and `app.py` via `python -m py_compile`
- [X] T019 Execute full validation scenarios against `specs/006-render-speed-optimization/quickstart.md` measuring speedup factors across all stages

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - starts immediately
- **Foundational (Phase 2)**: Depends on Phase 1 - BLOCKS all user stories
- **User Story 1 (Phase 3 - P1)**: Depends on Phase 2 - delivers primary MVP speedup
- **User Story 2 (Phase 4 - P1)**: Depends on Phase 2 - optimizes transcription and cloud API
- **User Story 3 (Phase 5 - P2)**: Depends on User Story 1 & 2 - overlaps encoding with pre-fetch
- **Polish (Phase 6)**: Runs after all user stories complete

### Parallel Opportunities

- `T001` and `T002` in Setup can run in parallel
- `T005` can run in parallel with `T003` and `T004`
- `T010` and `T012` can be developed in parallel
- `T018` runs in parallel with documentation checks

---

## Implementation Strategy

### MVP First (User Story 1 Only)
1. Complete Phase 1 (Setup) and Phase 2 (Foundational)
2. Complete Phase 3 (User Story 1: Direct FFmpeg Media Encoding)
3. **Validate**: Stage 5 encoding drops from ~130s down to $\le 15$s immediately (70%+ total time saved!)

### Incremental Delivery
1. Add User Story 2 (In-memory Whisper caching + 15s Gemini timeout) -> Stage 2 drops to $\le 8$s
2. Add User Story 3 (Queue pipelining) -> Batch queue idle time eliminated
3. Run complete quickstart validation suite

---

## Phase 7: Convergence

**Purpose**: Address gaps identified by convergence assessment against spec, plan, and constitution.

- [X] T020 Add `performance_profile` ("max_speed" / "balanced") persistence and preset mapping in `services/config_service.py` and `services/ffmpeg_encoder.py` per FR-008 (partial)
- [X] T021 Expose performance profile configuration endpoint and UI toggle in `app.py` and `templates/index.html` per FR-008 (partial)


