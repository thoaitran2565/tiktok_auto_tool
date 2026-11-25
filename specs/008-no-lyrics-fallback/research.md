# Phase 0 Research: No-Lyrics Fallback & Chill Video Naming

**Feature**: `008-no-lyrics-fallback`  
**Date**: 2026-11-21  
**Status**: Completed  

---

## Technical Decisions

### Decision 1: Robust Detection of Non-Lyric Audio

- **Context**: Video audio can be purely instrumental, ambient sound, sound effects, or speech advertising without any musical lyrics. Whisper may output empty strings, musical notes (`♪♪♪`), or garbled noise phonemes. Furthermore, Gemini AI may return explanatory disclaimers such as `(Đoạn âm thanh không chứa lời bài hát...)` or `(Không có nội dung lời bài hát)`.
- **Decision**: Implement a multi-stage validation rule:
  1. *Whisper output check*: If Whisper returns empty text, only whitespace, or text containing only musical notes/punctuation (e.g. regex `^[\s\.\,\!\?\♪\♫\-\_]+$`), classify as `has_lyrics = False` immediately and skip Gemini AI call.
  2. *AI refusal/disclaimer filter*: In `extract_lyrics.py` and `render_pipeline.py`, inspect AI response. If it starts with parentheses/brackets `(`, `[` or contains known disclaimer phrases (`không chứa lời`, `không có lời bài hát`, `không có nội dung`, `chỉ là các tiếng`), treat as non-lyric (`has_lyrics = False`, `full_lyrics = ""`).
- **Rationale**: Completely prevents AI explanatory text or noise transcripts from being burned onto video frames or used as video titles.
- **Alternatives Considered**: 
  - *Trusting AI output blindly*: Caused previous bugs where `(Không có nội dung lời bài hát).mp4` was generated as a video file name.
  - *Setting character count threshold*: Too blunt; short haiku-like lyrics or 2-line chorus clips could be falsely rejected.

---

### Decision 2: Skipping Canvas Lyric Overlay in Pillow & MoviePy

- **Context**: When `has_lyrics` is `False`, the video should have zero lyric text rendered on the canvas while preserving all visual quality (1080x1920 9:16 vertical resolution, background brightness reduction to 50%, and logo watermark in top right).
- **Decision**:
  - In `compose_full_canvas_pil()`: pass `full_lyrics=None`. The function already conditionally bypasses `create_lyrics_image_pil` and paste operations when `full_lyrics` is falsy.
  - In `SlideshowService` / multi-image slide builder: wrap `create_lyrics_image_pil` and pasting inside `if has_lyrics and full_lyrics:`.
- **Rationale**: Saves ~15-20% rendering overhead per non-lyric video by skipping complex text layout, font measurement, shadow offset rendering, and alpha compositing. Fully conforms to Constitution Principle II (Visual Integrity) and Principle I (Pipeline Modularity).
- **Alternatives Considered**: 
  - *Rendering an empty transparent PNG overlay*: Inefficient; causes unnecessary PIL allocations and MoviePy blending cycles.

---

### Decision 3: Standardized "Cuộc sống chill [timestamp]" Naming Convention

- **Context**: The user specified that when lyrics cannot be extracted, the video must be named `"Cuộc sống chill [timestamp]"`. Clarification resolved that `[timestamp]` should be a Unix timestamp (e.g. `int(time.time())`).
- **Decision**:
  - Generate base prefix: `file_prefix = f"Cuộc sống chill {int(time.time())}"`.
  - Format output file: `output_filename = f"{file_prefix}.mp4"`.
  - Collision avoidance: If `os.path.join(target_folder, output_filename)` already exists (e.g. rapid rendering), append a 4-digit unique identifier: `f"{file_prefix}_{int(time.time()*1000)%10000}.mp4"`.
- **Rationale**: Produces clean, uniform file names that are directly ready for social media posting without unwanted symbols or garbled text.
- **Alternatives Considered**: 
  - *Naming based on source video*: Often dirty (e.g. `Có thể khi yêu không thể mang lại cho em...mp4`), whereas user explicitly instructed `"Cuộc sống chill [timestamp]"`.

---

### Decision 4: Output Folder Routing & Queue State Representation

- **Context**: Videos rendered without lyrics should be cleanly separated from videos with lyrics.
- **Decision**:
  - Save to `outputs-no-lyrics/` directory (created automatically if not existing).
  - Update `videos_db.json` and session queue:
    - `title`: `"Cuộc sống chill [timestamp]"`
    - `has_lyrics`: `False`
    - `lyric_source`: `"None"`
    - `first_line`: `"Cuộc sống chill [timestamp]"`
    - `status`: `"Đã duyệt"`
    - `target_folder`: `"outputs-no-lyrics"`
- **Rationale**: Aligns with Constitution Principle III (Fail-Safe Media Management) and user preference for clean directory separation.
- **Alternatives Considered**: 
  - *Mixing all outputs in outputs/*: Harder for users to distinguish which videos have lyrics and which are instrumental/chill.
