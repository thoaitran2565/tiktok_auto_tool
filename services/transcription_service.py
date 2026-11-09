import os
import threading
import time
from typing import Optional, Dict, Any


class TranscriptionService:
    """
    Speech Recognition Service with In-Memory Singleton Caching.
    Eliminates disk I/O cold loading of neural network weights on every render.
    Supports faster-whisper (CTranslate2) with seamless fallback to standard OpenAI Whisper.
    """

    _lock = threading.Lock()
    _cached_model = None
    _cached_model_name: Optional[str] = None
    _engine_type: Optional[str] = None  # 'faster_whisper' or 'whisper'

    @classmethod
    def initialize_model(cls, model_name: str = "small") -> None:
        """
        Loads the model weights into memory once if not already resident.
        Thread-safe singleton initialization.
        """
        with cls._lock:
            if cls._cached_model is not None and cls._cached_model_name == model_name:
                return

            t0 = time.time()
            # Try faster-whisper first
            try:
                import faster_whisper
                print(f"🎙️ [TranscriptionService] Nạp model faster-whisper ('{model_name}')...")
                # Detect device: cuda if torch.cuda.is_available() else cpu
                device = "cpu"
                compute_type = "int8"
                try:
                    import torch
                    if torch.cuda.is_available():
                        device = "cuda"
                        compute_type = "float16"
                except Exception:
                    pass

                model = faster_whisper.WhisperModel(model_name, device=device, compute_type=compute_type)
                cls._cached_model = model
                cls._cached_model_name = model_name
                cls._engine_type = "faster_whisper"
                elapsed = time.time() - t0
                print(f"✓ [TranscriptionService] faster-whisper ('{model_name}') nạp thành công vào RAM trong {elapsed:.2f}s (device={device})")
                return
            except ImportError:
                pass
            except Exception as e:
                print(f"⚠️ [TranscriptionService] Không thể nạp faster-whisper: {e}, chuyển sang standard Whisper...")

            # Fallback to standard OpenAI Whisper
            try:
                import whisper
                print(f"🎙️ [TranscriptionService] Nạp model Whisper ('{model_name}') vào RAM...")
                model = whisper.load_model(model_name)
                cls._cached_model = model
                cls._cached_model_name = model_name
                cls._engine_type = "whisper"
                elapsed = time.time() - t0
                print(f"✓ [TranscriptionService] Whisper ('{model_name}') đã nạp sẵn vào RAM trong {elapsed:.2f}s")
            except Exception as e:
                print(f"❌ [TranscriptionService] Lỗi nạp Whisper model: {e}")
                cls._cached_model = None
                cls._cached_model_name = None
                cls._engine_type = None

    @classmethod
    def is_warmed(cls) -> bool:
        """
        Returns True if model weights are resident in RAM.
        """
        return cls._cached_model is not None

    @classmethod
    def get_engine_type(cls) -> str:
        """
        Returns the active transcription engine ('faster_whisper' or 'whisper').
        """
        return cls._engine_type or "none"

    @classmethod
    def get_model(cls, model_name: str = "small"):
        """
        Returns the cached model instance and active engine type, initializing if needed.
        """
        if not cls.is_warmed() or cls._cached_model_name != model_name:
            cls.initialize_model(model_name)
        return cls._cached_model, cls.get_engine_type()

    @classmethod
    def transcribe(cls, video_path: str, model_name: str = "small") -> str:
        """
        Transcribes the video audio using the warm in-memory model without reading from disk.
        """
        if not os.path.exists(video_path):
            print(f"❌ [TranscriptionService] Không tìm thấy video: {video_path}")
            return ""

        if not cls.is_warmed() or cls._cached_model_name != model_name:
            cls.initialize_model(model_name)

        if cls._cached_model is None:
            print("❌ [TranscriptionService] Model chưa được khởi tạo!")
            return ""

        with cls._lock:
            t0 = time.time()
            if cls._engine_type == "faster_whisper":
                segments, info = cls._cached_model.transcribe(video_path, beam_size=1, language="vi", task="transcribe")
                text = " ".join([seg.text for seg in segments]).strip()
            else:
                result = cls._cached_model.transcribe(video_path, task="transcribe", verbose=False)
                text = result.get("text", "").strip()

            elapsed = time.time() - t0
            print(f"🎙️ [TranscriptionService] Nhận diện xong trong {elapsed:.2f}s (độ dài: {len(text)} ký tự)")
            return text
