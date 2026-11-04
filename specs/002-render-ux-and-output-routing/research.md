# Research & Technical Decisions: Render UX & Output Routing

**Feature**: Render UX Optimizations, Adaptive Queue Learning, and Output Routing  
**Branch**: `002-render-ux-and-output-routing`  
**Date**: 2026-11-04  

---

## 1. Viewport-Constrained Layout & Sticky Header (`100vh`)

### Decision
Structure the interface container with CSS Flexbox pinned to `100vh` (`height: 100vh; overflow: hidden; display: flex; flex-direction: column`).
- **Header & Controls Area**: Includes page title, folder setup inputs, batch action buttons (Start, Stop, Reload), and queue summary statistics. Configured with `flex-shrink: 0`.
- **Queue Table Container**: Configured with `flex: 1; min-height: 0; overflow-y: auto`. Table header (`<th>`) has `position: sticky; top: 0`.

### Rationale
- Completely eliminates browser-level outer window scrollbars on displays >= 700px height.
- Keeps primary controls permanently accessible at the top, regardless of queue length.
- Provides a desktop-app quality UX similar to professional video editing suites.

---

## 2. Active Render Auto-Scroll & Timeline Accordion Auto-Expansion

### Decision
When batch rendering advances to a video item:
1. Automatically expand the detailed 6-stage timeline accordion: `document.getElementById('timeline-' + item.id).style.display = 'block'`.
2. Programmatically scroll the table container so the active row is aligned at the top of the viewport:
   ```javascript
   const rowEl = document.getElementById(`row-${item.id}`);
   rowEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
   ```

### Rationale
- Directs user attention immediately to the active work without requiring manual scrolling through dozens of items.
- Solves user frustration when running batches of 20-50 videos where the active video is pushed off-screen.

---

## 3. Progress Bar Plateauing & Integer Second Formatter

### Decision
- **Integer Formatting**: All time values formatted strictly as whole numbers:
  - `< 60s`: `${Math.round(sec)}s` (e.g., `14s`, `45s`).
  - `≥ 60s`: `${Math.floor(sec/60)}p ${Math.round(sec%60)}s` (e.g., `1p 25s`).
- **Progress Plateauing**: Rather than jumping randomly or exceeding stage boundaries, progress is mapped to cumulative stage weight limits:
  - Stage 1 (Audio): max 10%
  - Stage 2 (Whisper): max 40%
  - Stage 3 (Gemini AI): max 60%
  - Stage 4 (Visuals): max 70%
  - Stage 5 (Encoding): max 95%
  - Stage 6 (Finalize): 100%
  If a stage takes longer than predicted, progress smoothly caps at that stage's ceiling until the backend signals stage completion.

---

## 4. Real-Time Dynamic Adaptive Queue Re-Estimation

### Decision
After every video finishes rendering (`data.success`), the frontend immediately calls:
```javascript
await fetchPredictions();
updateQueueSummary();
```
`fetchPredictions()` queries `GET /api/render-predictions`. Because the completed video has just appended its performance metrics to `data/render_telemetry.json`, the newly calibrated `avg_duration_ratio` is immediately applied to all remaining queued items.

### Rationale
- Prediction accuracy improves in real-time as the queue renders.
- The overall queue batch ETA updates dynamically after every completed video.

---

## 5. Output Directory Routing (`outputs/` vs `outputs-no-lyrics/`)

### Decision
- Create `outputs-no-lyrics/` on startup.
- In `RenderPipeline`:
  - If `lyric_source == "AI"` and `full_lyrics`: Target folder = `outputs/`, `has_lyrics = True`.
  - Else: Target folder = `outputs-no-lyrics/`, `has_lyrics = False`.
- In `videos_db.json`: Record `has_lyrics: bool`, `output_folder: str`.
- In `app.py`: Expose `/outputs-no-lyrics/<path:filename>` and `/download/no-lyrics/<filename>`.
- In UI: Display green badge `🎵 Có lyrics` or amber badge `🔇 Không lời`.

---

## 6. Media Preview Inspector (Modal / Lightbox)

### Decision
Implement a centered overlay modal (`#mediaModal`) with:
- Dark blurred backdrop (`backdrop-filter: blur(8px); background: rgba(0,0,0,0.85)`).
- Centered container supporting both high-resolution images (`<img>`) and vertical MP4 videos (`<video controls autoplay>`).
- Close triggers: Close button `X`, clicking the backdrop area, or pressing `Escape`.

---

## 7. Streamlined Terminal Logging

### Decision
Replace verbose text dumps in `services/render_pipeline.py` and `extract_lyrics.py` with structured, single-line messages:
- `[1/6] 🎵 Trích xuất âm thanh...`
- `[2/6] 🎙️ Nhận diện giọng nói (Whisper)...`
- `[3/6] ✨ Gemini AI làm sạch lyrics: "{first_line}" ({lyric_source})`
- `[4/6] 🎨 Tạo hình ảnh & canvas lyrics...`
- `[5/6] 🎬 Ghép video & mã hóa MP4...`
- `[6/6] ✅ Hoàn tất video: {output_filename} -> {target_folder}`
- Suppress raw multiline Whisper transcripts and Gemini model retry dumps from stdout.

