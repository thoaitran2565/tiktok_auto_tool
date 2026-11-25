# Contract: No-Lyrics Detection & Fallback Rendering

**Feature**: `008-no-lyrics-fallback`  
**Date**: 2026-11-21  

---

## 1. Non-Lyric Classification Contract

### Function Signature: `is_valid_lyrics(raw_text: str, ai_text: str) -> Tuple[bool, str]`

Evaluates raw Whisper text and AI output to determine if genuine song lyrics are present.

#### Input Parameters:
- `raw_text` (`str`): Transcribed audio from Whisper.
- `ai_text` (`str`): Refined text returned from Gemini AI.

#### Output Contract:
- `Tuple[bool, str]`:
  - `has_lyrics` (`bool`): `True` if lyrics are authentic; `False` if non-lyric, noise, or disclaimer.
  - `clean_text` (`str`): Cleaned lyrics if `True`, or empty string `""` if `False`.

#### Rejection Conditions (Triggers `has_lyrics = False`):
1. `raw_text` is empty, whitespace only, or consists solely of musical/punctuation symbols (`♪`, `♫`, `...`, `-`).
2. `ai_text` contains known disclaimer markers:
   - `không có nội dung lời bài hát`
   - `không chứa lời bài hát`
   - `không thể nhận diện`
   - `chỉ là các tiếng` / `tiếng lầm bầm`
3. `ai_text` starts with `(` or `[` and ends with `)` or `]`.

---

## 2. Video Naming & Path Contract

### Non-Lyric Video File Output

When `has_lyrics == False`:

```python
timestamp = int(time.time())
base_name = f"Cuộc sống chill {timestamp}"
output_filename = f"{base_name}.mp4"
target_directory = "outputs-no-lyrics"
output_path = os.path.join(target_directory, output_filename)
```

If `os.path.exists(output_path)` is true, append a 4-digit unique suffix:
`output_filename = f"{base_name}_{int(time.time()*1000)%10000}.mp4"`

---

## 3. Visual Canvas Rendering Contract

### Function Call: `compose_full_canvas_pil()`

```python
compose_full_canvas_pil(
    image_path=image_path,
    full_lyrics=None,          # EXPLICITLY None for non-lyric videos
    logo_path='logo-text.png',
    target_width=1080,
    target_height=1920
)
```

### Slideshow Rendering Contract

```python
if not has_lyrics:
    # Skip create_lyrics_image_pil() and skip canvas paste
    pass
```

---

## 4. Database / State API Contract

When rendering completes for a non-lyric video, the state payload saved to `videos_db.json` and broadcasted via SSE/polling MUST adhere to:

```json
{
  "id": 0,
  "video_name": "source_clip.mp4",
  "title": "Cuộc sống chill 1732168137",
  "has_lyrics": false,
  "lyric_source": "None",
  "first_line": "Cuộc sống chill 1732168137",
  "raw_lyrics": "",
  "refined_lyrics": "",
  "output_filename": "Cuộc sống chill 1732168137.mp4",
  "output_path": "outputs-no-lyrics/Cuộc sống chill 1732168137.mp4",
  "target_folder": "outputs-no-lyrics",
  "status": "Đã duyệt"
}
```
