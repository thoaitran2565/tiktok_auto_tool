# Interface Contract: Speech Recognition Service with In-Memory Caching

**Feature**: `006-render-speed-optimization`  
**Date**: 2026-11-09  
**Scope**: Speech Transcription Subsystem (`services/transcription_service.py` / `extract_lyrics.py`)  

---

## 1. Class: `TranscriptionService`

Manages the lifecycle of speech recognition models with thread-safe in-memory caching.

```python
class TranscriptionService:
    _lock = threading.Lock()
    _cached_model = None
    _engine_type: Optional[str] = None  # 'faster_whisper' or 'whisper'

    @classmethod
    def initialize_model(cls, model_name: str = "small") -> None:
        """
        Loads the speech recognition model once into memory.
        1. Attempts to import and load 'faster_whisper.WhisperModel(model_name, device="auto", compute_type="auto")'.
        2. If unavailable, falls back to 'whisper.load_model(model_name)'.
        Sets _cached_model for subsequent reuse.
        """
        ...

    @classmethod
    def transcribe(cls, video_path: str, model_name: str = "small") -> str:
        """
        Transcribes the video audio using the warm in-memory model.
        Returns the raw text transcript without re-loading weights from disk.
        """
        ...

    @classmethod
    def is_warmed(cls) -> bool:
        """
        Returns True if the model weights are resident in RAM.
        """
        ...
```

---

## 2. Backward Compatibility Contract

- Function `extract_raw_lyrics(video_path)` in `extract_lyrics.py` delegates directly to `TranscriptionService.transcribe(video_path)`.
- Existing callers receive identical return types (`str` or `""`), preserving 100% backward compatibility.

