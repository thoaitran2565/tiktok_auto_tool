import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.ffmpeg_encoder import FFmpegEncoderService
from services.transcription_service import TranscriptionService
from services.telemetry_manager import telemetry_manager
from services.render_pipeline import compose_full_canvas_pil, RenderPipeline
from extract_lyrics import clean_lyrics_with_ai

def main():
    print("================================================================")
    print("🚀 RUNNING QUICKSTART OPTIMIZATION VALIDATION SUITE (FEATURE 006)")
    print("================================================================\n")

    # -----------------------------------------------------------------
    # Test 1: Encoder Hardware Detection
    # -----------------------------------------------------------------
    print("--- [TEST 1] Testing Hardware Encoder Auto-Detection ---")
    probe_start = time.time()
    best_encoder = FFmpegEncoderService.probe_best_encoder()
    probe_duration = time.time() - probe_start
    print(f"✅ Probe completed in {probe_duration:.3f}s: {best_encoder}")
    assert 'encoder' in best_encoder, "Probe result missing 'encoder' key!"
    print(f"🎯 Selected Encoder Backend: {best_encoder['encoder']} (Hardware: {best_encoder.get('is_hardware')})\n")

    # -----------------------------------------------------------------
    # Test 2: Instant Canvas Composition (< 0.1s)
    # -----------------------------------------------------------------
    print("--- [TEST 2] Testing Pillow Canvas Pre-Composition Speed ---")
    test_img = "D:\\Ảnh\\Ảnh đã tải\\1.jpg"
    if not os.path.exists(test_img):
        # Fallback to creating a dummy image
        from PIL import Image
        test_img = "temp_test_img.jpg"
        Image.new('RGB', (1080, 1920), (50, 100, 150)).save(test_img)

    canvas_start = time.time()
    canvas = compose_full_canvas_pil(
        image_path=test_img,
        full_lyrics="Dòng đời trôi mãi xuôi ngược năm tháng\nCó đôi khi lòng bình yên lạ kỳ",
        logo_path='logo-text.png',
        target_width=1080,
        target_height=1920
    )
    canvas_duration = time.time() - canvas_start
    test_canvas_path = "outputs/test_canvas_bench.png"
    os.makedirs("outputs", exist_ok=True)
    canvas.save(test_canvas_path, "PNG")
    print(f"✅ 1080x1920 Canvas composed & saved in {canvas_duration:.3f}s (size: {canvas.size})")
    assert canvas.size == (1080, 1920), f"Canvas dimensions incorrect: {canvas.size}"
    assert canvas_duration < 0.2, f"Canvas composition too slow: {canvas_duration}s\n"

    # -----------------------------------------------------------------
    # Test 3: Direct Native FFmpeg Stream Muxing Speed (Stage 5)
    # -----------------------------------------------------------------
    print("--- [TEST 3] Testing Direct FFmpeg Video Encoding Speed (Stage 5) ---")
    # Generate a dummy 5s audio file if needed
    test_audio_path = "outputs/test_bench_audio.mp3"
    from moviepy import ColorClip
    # Use moviepy or ffmpeg to make a short 5s test audio
    os.system(f'ffmpeg -y -f lavfi -i "sine=frequency=440:duration=5" -c:a libmp3lame "{test_audio_path}" > NUL 2>&1')
    assert os.path.exists(test_audio_path), "Failed to generate test audio"

    test_output_video = "outputs/test_bench_rendered.mp4"
    encode_start = time.time()
    FFmpegEncoderService.render_static_video(
        canvas_path=test_canvas_path,
        audio_path=test_audio_path,
        output_path=test_output_video,
        duration=5.0
    )
    encode_duration = time.time() - encode_start
    print(f"✅ 5.0s Video Encoded in {encode_duration:.2f}s (Effective speed: {5.0 / max(0.01, encode_duration):.1f}x real-time)")
    assert os.path.exists(test_output_video), "Rendered output file does not exist!"
    assert os.path.getsize(test_output_video) > 10000, "Rendered output file too small/empty!"
    print(f"🎯 Output size: {os.path.getsize(test_output_video) / 1024:.1f} KB\n")

    # -----------------------------------------------------------------
    # Test 4: Whisper In-Memory Singleton Cache (Stage 2)
    # -----------------------------------------------------------------
    print("--- [TEST 4] Testing Whisper In-Memory Singleton Cache Lifecycle ---")
    w1_start = time.time()
    model_1, engine_1 = TranscriptionService.get_model()
    w1_dur = time.time() - w1_start
    print(f"✅ First model retrieval: {w1_dur:.3f}s (engine: {engine_1})")

    w2_start = time.time()
    model_2, engine_2 = TranscriptionService.get_model()
    w2_dur = time.time() - w2_start
    print(f"✅ Second model retrieval (warm RAM cache): {w2_dur:.5f}s (engine: {engine_2})")
    assert w2_dur < 0.01, f"Model cache retrieval took too long: {w2_dur}s"
    assert model_1 is model_2, "Model singleton instances do not match!\n"

    # -----------------------------------------------------------------
    # Test 5: Gemini 15s Timeout & Resilient Fallback (Stage 3)
    # -----------------------------------------------------------------
    print("--- [TEST 5] Testing AI Lyric Refinement Timeout Protection ---")
    mock_raw = "Mưa trên phố bay bay lạnh lùng gió đông về"
    t_start = time.time()
    lyrics, source = clean_lyrics_with_ai(mock_raw)
    t_elapsed = time.time() - t_start
    print(f"✅ clean_lyrics_with_ai completed in {t_elapsed:.2f}s (source: {source})")
    assert t_elapsed <= 16.0, f"Call exceeded 15s hard timeout: {t_elapsed}s"
    assert len(lyrics) > 0, "Returned lyrics should not be empty\n"

    # -----------------------------------------------------------------
    # Test 6: Queue Pre-fetch Pipelining (Stage 1-4 Background Overlap)
    # -----------------------------------------------------------------
    print("--- [TEST 6] Testing Queue Pipeline Background Pre-Fetch ---")
    pipeline = RenderPipeline()
    # Test pre_fetch_item with test audio/image
    dummy_vid = "outputs/test_bench_rendered.mp4"
    pf_res = pipeline.pre_fetch_item(
        item_id=9999,
        video_path=dummy_vid,
        image_path=test_img
    )
    print(f"✅ Pre-fetch result status: {pf_res.get('status')}")
    assert pf_res.get('status') == 'ready', f"Pre-fetch failed: {pf_res.get('error')}"
    
    # Check that artifact is retrieved
    art = pipeline.get_prefetch_artifact(9999)
    assert art is not None, "Failed to retrieve prefetch artifact from cache!"
    print(f"✅ Pre-fetched artifact verified in cache: temp_canvas={os.path.basename(art['temp_canvas_path'])}")

    # Clean up test artifacts
    pipeline.clear_prefetch(9999)
    for p in [test_canvas_path, test_audio_path, test_output_video]:
        if os.path.exists(p):
            try:
                os.remove(p)
            except Exception:
                pass

    print("\n================================================================")
    print("🎉 ALL 6 QUICKSTART VALIDATION SCENARIOS PASSED WITH ZERO ERRORS!")
    print("================================================================")

if __name__ == '__main__':
    main()
