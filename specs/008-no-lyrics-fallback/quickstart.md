# Quickstart Validation Guide: No-Lyrics Fallback & Chill Video Naming

**Feature**: `008-no-lyrics-fallback`  
**Date**: 2026-11-21  

---

## 1. Prerequisites

- Python environment with Flask, MoviePy, and Pillow installed.
- Sample instrumental or non-lyric video (or mock audio).
- Image folder with at least 1 background photo (`.jpg` / `.png`).

---

## 2. Validation Scenarios

### Scenario 1: Instrumental / Non-Lyric Video Detection
1. Run `python -c "from extract_lyrics import clean_lyrics_with_ai; print(clean_lyrics_with_ai(''))"`
2. Verify output is `("", "None")` or `("", "Original")` indicating empty/non-lyric status.
3. Test with sample AI disclaimer string: `"(Đoạn âm thanh không chứa lời bài hát...)"`.
4. Verify validation function identifies this as non-lyric, clearing `full_lyrics` and setting `has_lyrics = False`.

### Scenario 2: Render Execution Without Lyric Overlay
1. Execute a single-item render for an instrumental video:
   ```powershell
   python scratch/test_render_no_lyrics.py
   ```
2. **Verify**:
   - Visual generation completes without generating or pasting any lyric text image.
   - Total render time is faster (~15-20% decrease compared to full typography rendering).
   - Video output exists, plays audio cleanly, and displays background photo + logo with NO text overlays.

### Scenario 3: Standardized File Naming & Folder Routing
1. Check output directory after render completes:
   - File is located in `outputs-no-lyrics/`.
   - File name starts with `Cuộc sống chill ` followed by a 10-digit Unix timestamp (e.g. `Cuộc sống chill 1732168137.mp4`).
   - File size is > 0 MB.
2. Verify no corrupt or empty files are created.

### Scenario 4: UI & Database Consistency
1. Open web application at `http://127.0.0.1:5000/manage`.
2. Find the rendered non-lyric video in the list.
3. **Verify**:
   - Title is `"Cuộc sống chill [timestamp]"`.
   - Badge displays `🔇 Không có lyrics`.
   - Video preview player plays video cleanly from `/outputs-no-lyrics/...`.
