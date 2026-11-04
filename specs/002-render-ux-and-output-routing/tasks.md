# Tasks: Render UX Optimizations, Adaptive Queue Learning, and Output Routing

**Input**: Design documents from `/specs/002-render-ux-and-output-routing/`  
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/output-routing-api.md, research.md, quickstart.md  
**Constitution**: Adheres strictly to Principles I (Modularity), II (9:16 layout), III (Fail-Safe Media), IV (Resilient AI), and V (Observability)  
**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

---

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., [US1], [US2], [US3], [US4])
- Clear, unambiguous file paths in every task description

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and directory structure preparation

- [X] T001 Initialize and ensure `outputs-no-lyrics/` directory and configure secondary output path in `app.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data model updates and pipeline routing primitives that MUST be completed before user stories

**⚠️ CRITICAL**: Foundational tasks must complete before user story implementation begins

- [X] T002 Parameterize `output_folder` and `no_lyrics_folder` in `RenderPipeline.__init__` in `services/render_pipeline.py`
- [X] T003 Update `VideoRecord` database serialization in `services/render_pipeline.py` to enforce `has_lyrics: boolean` and `output_folder: "outputs" | "outputs-no-lyrics"` attributes

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Viewport-Constrained Layout & Active Render Auto-Focus (Priority: P1) 🎯 MVP

**Goal**: Pin action controls in a fixed sticky header, constrain layout within viewport height (`100vh`) with an internally scrolling table, and automatically scroll the actively rendering video into view with its 6-stage timeline expanded.

**Independent Test**: Load a queue with 10+ items, start batch rendering, and verify that the outer window has no scrollbar, header buttons remain fixed at top, and the active video automatically scrolls to the top of the table viewport with its accordion expanded.

### Implementation for User Story 1

- [X] T004 [US1] Reconfigure CSS layout to `100vh` flexbox container with fixed header and internal scrollable table container in `templates/index.html`
- [X] T005 [US1] Relocate action controls (Start, Stop, Reload) from bottom toolbar to top sticky header area in `templates/index.html`
- [X] T006 [US1] Standardize table column alignments, paddings, and header stickiness (`position: sticky; top: 0`) in `templates/index.html`
- [X] T007 [US1] Implement smooth programmatic auto-scroll to top of viewport for active rendering row (`scrollIntoView`) in `templates/index.html`
- [X] T008 [US1] Implement automatic expansion of 6-stage timeline accordion upon render start in `templates/index.html`

**Checkpoint**: User Story 1 is functional and testable independently.

---

## Phase 4: User Story 2 - Smooth Progress Plateauing & Real-Time Adaptive Re-Estimation (Priority: P2)

**Goal**: Display all time counters strictly in whole integer seconds, smoothly animate progress with stage ceiling plateaus, and immediately recalculate remaining queue predictions and batch ETA as each video finishes.

**Independent Test**: Render a video and confirm all elapsed/remaining timers show integer seconds (`14s`, `~45s`). Observe that if a stage takes longer than predicted, progress plateaus at that stage's ceiling (10%, 40%, 60%, 70%, 95%) and jumps to 100% only on completion. Confirm queued items and total ETA update predictions immediately when each video completes.

### Implementation for User Story 2

- [X] T009 [P] [US2] Implement integer-only seconds formatting function eliminating decimal places in `templates/index.html`
- [X] T010 [US2] Implement progress bar plateauing logic adhering to cumulative stage ceilings (`audio_extraction`: 10%, `speech_transcription`: 40%, `lyric_refinement`: 60%, `visual_generation`: 70%, `media_encoding`: 95%, `finalization`: 100%) in `templates/index.html`
- [X] T011 [US2] Implement dynamic queue re-estimation triggering `fetchPredictions()` and `updateQueueSummary()` immediately after each video completion in `templates/index.html`

**Checkpoint**: User Stories 1 AND 2 both work independently.

---

## Phase 5: User Story 3 - No-Lyrics Output Routing & Media Inspection (Priority: P3)

**Goal**: Automatically route videos with no AI lyrics into `outputs-no-lyrics/`, tag with 'Không lời' badge, and provide a centered Modal/Lightbox overlay with dark blurred backdrop to inspect source images and output videos.

**Independent Test**: Render one video with lyrics and one without lyrics. Verify destination folders (`outputs/` vs `outputs-no-lyrics/`), badges, and media preview modals that close when clicking the close button or backdrop.

### Implementation for User Story 3

- [X] T012 [P] [US3] Implement `/outputs-no-lyrics/<path:filename>` and `/download/no-lyrics/<filename>` endpoints in `app.py`
- [X] T013 [US3] Implement dynamic output folder routing based on `lyric_source == "AI"` and non-empty lyrics in `services/render_pipeline.py`
- [X] T014 [US3] Update `POST /api/render-single` to return `output_folder`, `has_lyrics`, and routed `video_url` in `app.py`
- [X] T015 [P] [US3] Implement centered Modal/Lightbox HTML markup and backdrop overlay styling in `templates/index.html`
- [X] T016 [US3] Implement media modal preview JavaScript handlers for source images and output videos with backdrop dismiss in `templates/index.html`
- [X] T017 [P] [US3] Add "Có lyrics" and "Không lời" status badges and routed preview/download links in `templates/index.html`
- [X] T018 [P] [US3] Add "Có lyrics" and "Không lời" status badges and routed playback/download links in `templates/manage.html`

**Checkpoint**: User Stories 1, 2, and 3 work together cleanly.

---

## Phase 6: User Story 4 - Clean Terminal Logging (Priority: P4)

**Goal**: Streamline console terminal output into clean, single-line stage progress messages with emojis and suppress verbose raw lyrics text dumps.

**Independent Test**: Run a render and check terminal stdout for concise single-line messages (`[1/6] 🎵...`, `[6/6] ✅...`) with zero raw lyrics text dumps.

### Implementation for User Story 4

- [X] T019 [P] [US4] Clean up verbose stdout logs and suppress multiline transcripts in `extract_lyrics.py`
- [X] T020 [US4] Restructure `services/render_pipeline.py` terminal output into concise single-line status messages with emojis for each of the 6 stages

**Checkpoint**: All 4 user stories functional and observable.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Responsive validation and end-to-end quickstart scenario testing

- [X] T021 [P] Verify responsive viewport scaling on compact screens (>= 700px height) in `templates/index.html`
- [X] T022 Execute quickstart verification scenarios 1 through 7 in `specs/002-render-ux-and-output-routing/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Can start immediately.
- **Foundational (Phase 2)**: Depends on Phase 1; blocks User Stories 1-4.
- **User Story 1 (Phase 3)**: Depends on Phase 2. Delivers MVP viewport layout.
- **User Story 2 (Phase 4)**: Depends on Phase 3 (extends UI progress & prediction loop).
- **User Story 3 (Phase 5)**: Depends on Phase 2 (for routing backend) and Phase 3 (for UI table hooks).
- **User Story 4 (Phase 6)**: Can execute in parallel or after User Story 3.
- **Polish (Phase 7)**: Depends on all user stories being implemented.

### Parallel Opportunities

- T009 can run in parallel with T004-T008.
- T012 can run in parallel with T015.
- T017 and T018 can run in parallel once T013 and T014 are implemented.
- T019 and T020 can run independently.
- T021 can run in parallel with T022.

---

## Implementation Strategy

### MVP First (User Story 1 Only)
1. Complete Phase 1 (Setup: directory creation in `app.py`).
2. Complete Phase 2 (Foundational: pipeline folder parameters & DB schema).
3. Complete Phase 3 (User Story 1: `100vh` layout, sticky buttons, auto-scroll, timeline auto-expansion).
4. **Validate**: Verify queue table scrolling and active row auto-focusing on test queue.

### Incremental Delivery
1. Foundation & US1: Desktop layout + auto-focus (MVP).
2. US2: Whole integer seconds formatting + progress plateauing + dynamic re-estimation.
3. US3: Dedicated `outputs-no-lyrics/` routing + Modal lightbox for media inspection.
4. US4: Clean, emoji-based terminal output.
5. Polish: Cross-browser verification against `quickstart.md`.

