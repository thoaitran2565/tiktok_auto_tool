# Interface Contract: High-Speed FFmpeg Encoder Service

**Feature**: `006-render-speed-optimization`  
**Date**: 2026-11-09  
**Scope**: Media Encoding Subsystem (`services/ffmpeg_encoder.py`)  

---

## 1. Class: `FFmpegEncoderService`

Provides direct FFmpeg execution bypassing Python MoviePy per-frame generator loops.

```python
class FFmpegEncoderService:
    @classmethod
    def probe_best_encoder(cls) -> Dict[str, Any]:
        """
        Probes host FFmpeg capabilities in order:
        1. h264_nvenc (NVIDIA GPU)
        2. h264_qsv (Intel QuickSync GPU)
        3. h264_mf (Windows MediaFoundation)
        4. libx264 (Software with preset=ultrafast)

        Returns:
            Dict containing:
            - 'encoder': str (e.g. 'h264_qsv' or 'libx264')
            - 'preset': str (e.g. 'ultrafast')
            - 'is_hardware': bool
            - 'extra_args': List[str]
        """
        ...

    @classmethod
    def render_static_video(
        cls,
        canvas_path: str,
        audio_path: str,
        output_path: str,
        duration: float,
        fps: int = 24,
        encoder_override: Optional[str] = None
    ) -> bool:
        """
        Encodes a single pre-rendered 1080x1920 canvas PNG and MP3 audio into a vertical MP4.
        Uses native FFmpeg image looping:
        ffmpeg -loop 1 -framerate {fps} -i {canvas_path} -i {audio_path} -t {duration}
               -c:v {best_encoder} -preset ultrafast -pix_fmt yuv420p
               -c:a aac -b:a 192k -shortest {output_path}
        
        Executes in ~2-5s instead of ~130s.
        """
        ...

    @classmethod
    def render_slideshow_video(
        cls,
        slide_canvas_paths: List[str],
        audio_path: str,
        output_path: str,
        total_duration: float,
        transition_duration: float = 0.65,
        fps: int = 24
    ) -> bool:
        """
        Encodes sequential 1080x1920 slide images with native FFmpeg filtergraph (xfade)
        matching audio duration.
        """
        ...
```

---

## 2. CLI Execution & Return Codes

- All FFmpeg subprocess invocations MUST specify `timeout=120` to prevent deadlocks.
- Standard output and error MUST be captured for diagnostic telemetry.
- On non-zero exit code, error MUST raise `RuntimeError` naming the failing encoder, triggering immediate fallback to `libx264 -preset ultrafast`.

