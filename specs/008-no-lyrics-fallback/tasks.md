# Tasks: No-Lyrics Fallback & Chill Video Naming

**Input**: Design documents from `/specs/008-no-lyrics-fallback/`  
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/no-lyrics-contract.md`, `quickstart.md`  
**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `- [ ] [ID] [P?] [Story?] Description with file path`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (`[US1]`, `[US2]`, `[US3]`)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Ensure target filesystem directories and directory structures are initialized.

- [X] T001 Ensure target export directory `outputs-no-lyrics/` is verified and created in `services/render_pipeline.py` and `app.py` per Constitution Principle III

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core non-lyric audio detection and disclaimer filtering that MUST complete before user stories can execute.

**⚠️ CRITICAL**: Must complete before user stories to ensure the pipeline correctly identifies non-lyric media.

- [X] T002 Implement non-lyric audio detection and disclaimer filtering in `extract_lyrics.py` to identify empty Whisper transcripts, noise symbols, and AI disclaimer phrases per `contracts/no-lyrics-contract.md`

**Checkpoint**: Detection logic operational. System can distinguish between genuine lyrics and non-lyric audio.

---

## Phase 3: User Story 1 - Video Rendering Without Lyric Overlay (Priority: P1) 🎯 MVP

**Goal**: Deliver clean video rendering without any lyrics overlay text for non-lyric videos, preserving background visual, logo watermark, and original audio.

**Independent Test**: Render an instrumental video. Verify the resulting video has audio and background visuals, with zero lyric text rendered on the canvas.

### Implementation for User Story 1

- [X] T003 [US1] Update static canvas compositing in `services/render_pipeline.py` to bypass `create_lyrics_image_pil` and text pasting when `has_lyrics` is False
- [X] T004 [US1] Update multi-image slideshow generation in `services/render_pipeline.py` to skip `create_lyrics_image_pil` and slide text pasting when `has_lyrics` is False

**Checkpoint**: User Story 1 operational. Non-lyric videos render cleanly without superimposed lyrics text.

---

## Phase 4: User Story 2 - Standardized "Cuộc sống chill [timestamp]" Naming Convention (Priority: P1)

**Goal**: Export non-lyric videos named `"Cuộc sống chill [timestamp].mp4"` with Unix timestamps and route them to `outputs-no-lyrics/`.

**Independent Test**: Render a non-lyric video. Verify the exported file is saved in `outputs-no-lyrics/` with filename starting with `Cuộc sống chill ` followed by a 10-digit Unix timestamp.

### Implementation for User Story 2

- [X] T005 [US2] Implement standardized file naming in `services/render_pipeline.py` using `Cuộc sống chill {int(time.time())}.mp4` with collision resolution
- [X] T006 [US2] Configure output routing in `services/render_pipeline.py` to save non-lyric videos strictly into `outputs-no-lyrics/`

**Checkpoint**: User Story 2 operational. Non-lyric videos are consistently named and isolated in `outputs-no-lyrics/`.

---

## Phase 5: User Story 3 - Intelligent Non-Lyric Audio Detection & Queue Classification (Priority: P2)

**Goal**: Update database records, queue status badges, and test endpoint logic for non-lyric media.

**Independent Test**: Scan and render an instrumental video. Verify table row and `/manage` view show title `"Cuộc sống chill [timestamp]"` and badge `🔇 Không có lyrics`.

### Implementation for User Story 3

- [X] T007 [US3] Update queue state and metadata persistence in `services/render_pipeline.py` to record `title: "Cuộc sống chill [timestamp]"`, `has_lyrics: false`, `lyric_source: "None"`, and `target_folder: "outputs-no-lyrics"` in `videos_db.json`
- [X] T008 [US3] Update test endpoint `POST /api/test-lyrics` in `app.py` to apply non-lyric detection and fallback naming for `/test` page consistency
- [X] T009 [P] [US3] Update queue table status rendering in `templates/index.html` and `templates/manage.html` to display `"Cuộc sống chill [timestamp]"` and `🔇 Không có lyrics` badge

**Checkpoint**: User Story 3 operational. Complete end-to-end consistency across rendering, management, and testing UIs.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Code compilation verification, regression testing, and end-to-end scenario validation.

- [X] T010 [P] Verify Python syntax integrity across `extract_lyrics.py`, `services/render_pipeline.py`, and `app.py` via `python -m py_compile`
- [X] T011 Execute full validation scenarios against `specs/008-no-lyrics-fallback/quickstart.md` verifying 0 text overlay, Unix timestamp naming, and `outputs-no-lyrics/` routing

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - starts immediately
- **Foundational (Phase 2)**: Depends on Phase 1 - BLOCKS all user stories
- **User Story 1 (Phase 3 - P1)**: Depends on Phase 2 - delivers core MVP clean rendering
- **User Story 2 (Phase 4 - P1)**: Depends on Phase 2 - delivers standardized naming & routing
- **User Story 3 (Phase 5 - P2)**: Depends on Phase 3 and Phase 4 - updates database and UI state
- **Polish (Phase 6)**: Runs after all user stories are complete

### Parallel Opportunities

- `T003` and `T004` can run in parallel within Phase 3
- `T005` and `T006` can run in parallel within Phase 4
- `T009` and `T010` can run in parallel with backend tasks

---

## Implementation Strategy

### MVP First (User Story 1 & 2)
1. Complete Phase 1 (Setup) and Phase 2 (Foundational detection in `extract_lyrics.py`)
2. Complete Phase 3 (User Story 1: Skip lyric canvas overlays)
3. Complete Phase 4 (User Story 2: Name as `"Cuộc sống chill [timestamp].mp4"`)
4. **Validate**: Render 1 instrumental video. Verify clean visual (no lyrics) and correct file name in `outputs-no-lyrics/`!

### Incremental Delivery
1. Add User Story 3 (Queue and `/manage` UI status badges)
2. Run complete quickstart validation suite (`T011`)
