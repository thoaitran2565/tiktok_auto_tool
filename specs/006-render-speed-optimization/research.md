# Phase 0 Research: Fast Video Render Pipeline & Performance Optimization

**Feature**: `006-render-speed-optimization`  
**Date**: 2026-11-09  
**Status**: Completed  

---

## 1. Research Decision 1: Direct High-Speed FFmpeg Media Encoding Engine

### Context
Telemetry in `data/render_telemetry.json` confirms Stage 5 (`media_encoding`) accounts for ~65% to 75% of total render duration (120s–140s for a 35s video). MoviePy composites every frame (24 fps = 840 frames) through Python memory (`get_frame` generator loops), converting PIL images to NumPy arrays in Python before piping raw bytes to FFmpeg stdin with software `libx264` (`preset='veryfast'`).

Benchmarking direct FFmpeg encoding on the local host shows:
- Direct FFmpeg `libx264 -preset ultrafast` encodes 1080x1920 video at **12.5x speed** (0.08s per 1.0s video, or ~2.5s for a 30s video).
- Hardware encoders `h264_qsv` (Intel QuickSync) and `h264_mf` (Windows MediaFoundation) are active and verified on this system.

### Decision
Implement a dedicated `FFmpegEncoderService` with:
1. **Direct Stream Compositing**:
   - For single-image videos: Pillow generates the final 1080x1920 canvas image (with 20% dimming, logo watermark, and transparent lyrics) **once**. FFmpeg loops this single image over the audio track (`-loop 1 -i canvas.png -i audio.mp3 -shortest`) in native C code without executing a single per-frame Python loop.
   - For multi-image slideshows: Pillow pre-scales slides into 1080x1920 vertical canvas images; FFmpeg native `xfade` (or hardware-accelerated filtergraph) executes smooth horizontal transitions directly.
2. **Hardware Acceleration Probe & Fallback**:
   - Probes hardware encoders in order: `h264_nvenc` -> `h264_qsv` -> `h264_mf` -> `libx264 -preset ultrafast`.
   - On this machine, `h264_qsv` and `h264_mf` are verified functional; `libx264 -preset ultrafast` delivers 12.5x speedup.

### Alternatives Considered
- *Keep MoviePy and change `preset='ultrafast'`*: Still suffers from Python per-frame overhead and GIL contention, taking ~45–60s instead of ~2–5s.
- *GPU-only requirement*: Fails on systems without dedicated NVIDIA GPUs. Auto-probe with fallback guarantees universal compatibility per Constitution Principle III.

---

## 2. Research Decision 2: In-Memory Singleton Caching & `faster-whisper`

### Context
Currently, `extract_raw_lyrics()` in `extract_lyrics.py` executes:
```python
model = whisper.load_model("small")
result = model.transcribe(video_path, task="transcribe", verbose=False)
```
Loading model weights from disk takes 10–20 seconds on every video item in a queue. In addition, standard Whisper on CPU processes audio sequentially without quantization.

### Decision
1. **Singleton Model Cache (`WhisperCache`)**:
   - Load the model into memory **once** on first invocation (or preload on startup) and retain the reference in a thread-safe singleton.
   - Subsequent calls transcribe directly from memory, eliminating disk I/O and weight re-allocation.
2. **Engine Upgrade & Graceful Fallback**:
   - If `faster-whisper` (CTranslate2) is present, use `WhisperModel("small" or "base", device="auto", compute_type="auto")` for up to 4x faster execution and 50% less RAM.
   - If `faster-whisper` is not installed, seamlessly fall back to the in-memory singleton standard `whisper` model.
   - Support model selection (`base` for ultra-fast ~4-6s transcription, `small` for standard ~8-12s).

### Alternatives Considered
- *Re-loading Whisper per item*: Current bottleneck; rejected.
- *External Whisper Cloud API*: Introduces API billing and network dependency; rejected per Constitution Principle IV.

---

## 3. Research Decision 3: Resilient AI Lyric Refinement with Hard Timeout

### Context
In telemetry record `tel_1793872987172`, Stage 3 (`lyric_refinement`) stalled for **293.8 seconds** due to sequential fallback loops and cloud API response lag.

### Decision
1. **Strict 15-Second Timeout per Request**:
   - Use `concurrent.futures.ThreadPoolExecutor` or client timeout parameters (15 seconds maximum).
   - If Gemini does not respond within 15 seconds, instantly fall back to cleaned Whisper transcript rather than holding the entire rendering queue hostage.
2. **Prioritized Fast Model**:
   - Target `gemini-2.5-flash` or `gemini-2.5-flash-lite` first. If rate-limited or lagging, immediately fall back.

### Alternatives Considered
- *Indefinite retries*: Causes user-facing freezes of up to 5 minutes; rejected.
- *Removing AI refinement completely*: Degrades lyrics typography quality; rejected.

---

## 4. Research Decision 4: Asynchronous Batch Queue Stage Pipelining

### Context
In batch renders, currently Video 1 runs stages 1->2->3->4->5->6, and only after completion does Video 2 start stage 1. During stage 5 (encoding), CPU/network are free from AI workloads; during stages 2 & 3, the video encoder is completely idle.

### Decision
Implement **2-Stage Pipelined Producer-Consumer Flow**:
- **Stage Group A (Pre-processing / AI)**: Audio extraction (Stage 1), Whisper transcription (Stage 2), Gemini refinement (Stage 3), and Pillow canvas preparation (Stage 4).
- **Stage Group B (Media Encoding & Finalization)**: Direct FFmpeg encoding (Stage 5) and file finalization (Stage 6).
- While Video $N$ is executing Stage Group B in FFmpeg, a background worker pre-executes Stage Group A for Video $N+1$.
- By the time Video $N$ finishes encoding, Video $N+1$'s canvas and audio are already prepared and waiting, reducing aggregate batch render time by an additional 30%–40%.

### Alternatives Considered
- *Full 2-video concurrent rendering*: Renders two heavy 1080x1920 video encodings simultaneously, causing CPU/GPU throttling and thermal spikes on local laptops. Pipelining decouples AI from encoding without multiplying peak encoder load.

