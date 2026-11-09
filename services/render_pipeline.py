import os
import re
import time
import json
import threading
from datetime import datetime
from typing import Callable, Optional, Dict, Any, List

from moviepy import ImageClip, AudioFileClip, VideoFileClip, ColorClip, CompositeVideoClip
from PIL import Image, ImageEnhance, ImageDraw, ImageFont
import numpy as np

from extract_lyrics import extract_raw_lyrics, clean_lyrics_with_ai, get_first_line
from services.progress_manager import progress_manager
from services.telemetry_manager import telemetry_manager
from services.slideshow_service import SlideshowService
from services.ffmpeg_encoder import FFmpegEncoderService

VIDEOS_DB_FILE = 'videos_db.json'

def create_lyrics_image_pil(text: str, img_width: int = 1080, target_height: int = 1920, font_size: int = 20) -> Image.Image:
    """
    Generate transparent PIL Image containing full lyrics, bounded at max 90% of target video height.
    """
    max_allowed_height = int(target_height * 0.9)
    temp_img_height = 4000
    txt_img = Image.new('RGBA', (img_width, temp_img_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(txt_img)

    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except Exception:
        font = ImageFont.load_default()

    x = 80
    y = 50

    # Draw black stroke border for readability
    for adj_x, adj_y in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        draw.multiline_text((x + adj_x, y + adj_y), text, font=font, fill=(0, 0, 0, 255), spacing=10, align="left")

    # Draw white text fill
    draw.multiline_text((x, y), text, font=font, fill=(255, 255, 255, 255), spacing=10, align="left")

    bbox = draw.multiline_textbbox((x, y), text, font=font, spacing=10)
    text_bottom_y = bbox[3] + 30
    final_height = min(int(text_bottom_y), max_allowed_height)

    return txt_img.crop((0, 0, img_width, final_height))


def create_lyrics_image_transparent(text: str, img_width: int = 1080, target_height: int = 1920, font_size: int = 20) -> np.ndarray:
    return np.array(create_lyrics_image_pil(text, img_width, target_height, font_size))


def compose_full_canvas_pil(
    image_path: str,
    full_lyrics: Optional[str] = None,
    logo_path: str = 'logo-text.png',
    target_width: int = 1080,
    target_height: int = 1920
) -> Image.Image:
    """
    Directly composites complete 1080x1920 vertical canvas in Pillow in ~0.03s:
    1. Black matting background
    2. Centered scaled image with 50% brightness reduction
    3. Logo watermark in upper right
    4. Centered transparent lyrics overlay
    """
    canvas = Image.new('RGB', (target_width, target_height), (0, 0, 0))

    if os.path.exists(image_path):
        with Image.open(image_path) as raw_img:
            pil_img = raw_img.convert("RGB")
            enhancer = ImageEnhance.Brightness(pil_img)
            dark_pil_img = enhancer.enhance(0.5)

            img_w, img_h = dark_pil_img.size
            ratio = min(target_width / img_w, target_height / img_h)
            new_w = int(img_w * ratio)
            new_h = int(img_h * ratio)
            resized_img = dark_pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)

            offset_x = (target_width - new_w) // 2
            offset_y = (target_height - new_h) // 2
            canvas.paste(resized_img, (offset_x, offset_y))

    # Add logo
    if logo_path and os.path.exists(logo_path):
        try:
            with Image.open(logo_path) as logo_raw:
                logo_rgba = logo_raw.convert("RGBA")
                lw, lh = logo_rgba.size
                target_lw = 250
                target_lh = int(lh * (target_lw / lw))
                resized_logo = logo_rgba.resize((target_lw, target_lh), Image.Resampling.LANCZOS)
                pos_x = target_width - target_lw - 100
                pos_y = 260
                canvas.paste(resized_logo, (pos_x, pos_y), mask=resized_logo)
        except Exception as e:
            print(f"⚠️ Logo overlay warning: {e}")

    # Add lyrics
    if full_lyrics and full_lyrics.strip():
        try:
            lyric_pil = create_lyrics_image_pil(full_lyrics, img_width=target_width, target_height=target_height, font_size=20)
            lw, lh = lyric_pil.size
            pos_y = max(0, (target_height - lh) // 2)
            canvas.paste(lyric_pil, (0, pos_y), mask=lyric_pil)
        except Exception as e:
            print(f"⚠️ Lyrics overlay warning: {e}")

    return canvas


def load_video_db() -> list:
    if not os.path.exists(VIDEOS_DB_FILE):
        return []
    try:
        with open(VIDEOS_DB_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for item in data:
                if 'output_folder' not in item:
                    item['output_folder'] = 'outputs'
                if 'has_lyrics' not in item:
                    item['has_lyrics'] = True
            return data
    except Exception:
        return []


def save_video_db(data: list):
    try:
        with open(VIDEOS_DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"⚠️ Error saving video db: {e}")


class RenderPipeline:
    """
    Decoupled video rendering pipeline managing 6 sequential observable stages:
    1. audio_extraction
    2. speech_transcription
    3. lyric_refinement
    4. visual_generation
    5. media_encoding
    6. finalization
    """
    def __init__(self, output_folder: str = 'outputs', no_lyrics_folder: str = 'outputs-no-lyrics'):
        self.output_folder = output_folder
        self.no_lyrics_folder = no_lyrics_folder
        os.makedirs(self.output_folder, exist_ok=True)
        os.makedirs(self.no_lyrics_folder, exist_ok=True)
        self._prefetch_cache: Dict[Any, Dict[str, Any]] = {}
        self._prefetch_threads: Dict[Any, threading.Thread] = {}
        self._prefetch_lock = threading.Lock()

    def get_prefetch_artifact(self, item_id: Any) -> Optional[Dict[str, Any]]:
        with self._prefetch_lock:
            artifact = self._prefetch_cache.get(item_id)
            if artifact and artifact.get('status') == 'ready':
                audio_path = artifact.get('temp_audio_path', '')
                canvas_path = artifact.get('temp_canvas_path', '')
                slide_paths = artifact.get('temp_slide_paths', [])
                audio_ok = os.path.exists(audio_path)
                canvas_ok = os.path.exists(canvas_path) or (bool(slide_paths) and os.path.exists(slide_paths[0]))
                if audio_ok and canvas_ok:
                    return artifact
        return None

    def pop_prefetch_artifact(self, item_id: Any) -> Optional[Dict[str, Any]]:
        with self._prefetch_lock:
            return self._prefetch_cache.pop(item_id, None)

    def clear_prefetch(self, item_id: Optional[Any] = None):
        with self._prefetch_lock:
            if item_id is not None:
                art = self._prefetch_cache.pop(item_id, None)
                if art:
                    self._cleanup_prefetch_files(art)
            else:
                for k, art in list(self._prefetch_cache.items()):
                    self._cleanup_prefetch_files(art)
                self._prefetch_cache.clear()

    def _cleanup_prefetch_files(self, artifact: Dict[str, Any]):
        try:
            ap = artifact.get('temp_audio_path')
            if ap and os.path.exists(ap):
                os.remove(ap)
            cp = artifact.get('temp_canvas_path')
            if cp and os.path.exists(cp):
                os.remove(cp)
            for sp in artifact.get('temp_slide_paths', []):
                if sp and os.path.exists(sp):
                    os.remove(sp)
        except Exception:
            pass

    def pre_fetch_item(
        self,
        item_id: Any,
        video_path: str,
        image_path: str,
        is_multi_image: bool = False,
        image_paths: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Executes Stages 1 to 4 asynchronously for an upcoming queue item:
        - Stage 1: Audio extraction -> temp_audio_<id>.mp3
        - Stage 2: Speech transcription using warm in-memory Whisper singleton
        - Stage 3: Lyric refinement with 15s timeout
        - Stage 4: Pillow canvas generation -> temp_canvas_<id>.png or slide images
        """
        with self._prefetch_lock:
            existing = self._prefetch_cache.get(item_id)
            if existing and existing.get('status') == 'ready':
                audio_path = existing.get('temp_audio_path', '')
                canvas_path = existing.get('temp_canvas_path', '')
                slide_paths = existing.get('temp_slide_paths', [])
                if os.path.exists(audio_path) and (os.path.exists(canvas_path) or (bool(slide_paths) and os.path.exists(slide_paths[0]))):
                    return existing
            self._prefetch_cache[item_id] = {'status': 'in_progress', 'started_at': time.time()}

        video_name = os.path.basename(video_path)
        print(f"\n⚡ [Pre-fetch] Khởi chạy nạp trước B1-4 cho Video #{item_id}: {video_name}")
        temp_audio_path = os.path.join(self.output_folder, f"temp_audio_{item_id}.mp3")
        temp_canvas_path = os.path.join(self.output_folder, f"temp_canvas_{item_id}.png")
        temp_slide_paths: List[str] = []
        stage_durations: Dict[str, float] = {}

        try:
            # Stage 1: Audio Extraction
            s1_start = time.time()
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"Video nguồn không còn tồn tại: {video_path}")

            video_clip_input = VideoFileClip(video_path)
            if video_clip_input.audio is None:
                video_clip_input.close()
                raise ValueError("Video không có âm thanh!")

            audio_duration = float(video_clip_input.audio.duration)
            video_clip_input.audio.write_audiofile(temp_audio_path, codec='mp3', logger=None)
            video_clip_input.close()
            s1_duration = time.time() - s1_start
            stage_durations["audio_extraction"] = s1_duration

            # Stage 2: Whisper Transcription
            s2_start = time.time()
            raw_lyrics = extract_raw_lyrics(video_path) or ""
            s2_duration = time.time() - s2_start
            stage_durations["speech_transcription"] = s2_duration

            # Stage 3: Lyric Refinement
            s3_start = time.time()
            api_start = time.time()
            full_lyrics, lyric_source = clean_lyrics_with_ai(raw_lyrics)
            api_latency_ms = (time.time() - api_start) * 1000.0

            lyric_title = get_first_line(full_lyrics, max_length=100)
            if lyric_title:
                safe_lyric = re.sub(r'[\\/*?:"<>|#]', "", lyric_title).strip()
                file_prefix = safe_lyric if safe_lyric else "CuocSongChill"
            else:
                file_prefix = "CuocSongChill"

            has_lyrics = bool(lyric_source == "AI" and full_lyrics and full_lyrics.strip())
            target_folder_name = "outputs" if has_lyrics else "outputs-no-lyrics"
            target_folder = self.output_folder if has_lyrics else self.no_lyrics_folder

            existing_file_check = os.path.join(target_folder, f"{file_prefix}.mp4")
            output_filename = f"{file_prefix}_{int(time.time()) % 10000}.mp4" if os.path.exists(existing_file_check) else f"{file_prefix}.mp4"
            output_path = os.path.join(target_folder, output_filename)
            s3_duration = time.time() - s3_start
            stage_durations["lyric_refinement"] = s3_duration

            # Stage 4: Visual Generation
            s4_start = time.time()
            target_width = 1080
            target_height = 1920
            canvas_mode = "static"

            if is_multi_image and image_paths and len(image_paths) >= 2:
                canvas_mode = "slideshow"
                for s_idx, sp in enumerate(image_paths):
                    slide_path = os.path.join(self.output_folder, f"temp_slide_{item_id}_{s_idx}.png")
                    with Image.open(sp) as simg:
                        fitted = SlideshowService.fit_image_vertical(simg.convert('RGB'), target_width, target_height)
                        if os.path.exists('logo-text.png'):
                            try:
                                with Image.open('logo-text.png') as logo_raw:
                                    logo_rgba = logo_raw.convert("RGBA")
                                    lw, lh = logo_rgba.size
                                    target_lw = 250
                                    target_lh = int(lh * (target_lw / lw))
                                    resized_logo = logo_rgba.resize((target_lw, target_lh), Image.Resampling.LANCZOS)
                                    fitted.paste(resized_logo, (target_width - target_lw - 100, 260), mask=resized_logo)
                            except Exception:
                                pass
                        if lyric_source == "AI" and full_lyrics:
                            try:
                                lyric_pil = create_lyrics_image_pil(full_lyrics, img_width=target_width, target_height=target_height, font_size=20)
                                lw, lh = lyric_pil.size
                                pos_y = max(0, (target_height - lh) // 2)
                                fitted.paste(lyric_pil, (0, pos_y), mask=lyric_pil)
                            except Exception:
                                pass
                        fitted.save(slide_path, "PNG")
                        temp_slide_paths.append(slide_path)
            else:
                canvas_img = compose_full_canvas_pil(
                    image_path=image_path,
                    full_lyrics=full_lyrics if lyric_source == "AI" else None,
                    logo_path='logo-text.png',
                    target_width=target_width,
                    target_height=target_height
                )
                canvas_img.save(temp_canvas_path, "PNG")

            s4_duration = time.time() - s4_start
            stage_durations["visual_generation"] = s4_duration

            artifact = {
                "status": "ready",
                "item_id": item_id,
                "temp_audio_path": temp_audio_path,
                "audio_duration": audio_duration,
                "raw_lyrics": raw_lyrics,
                "full_lyrics": full_lyrics,
                "lyric_source": lyric_source,
                "has_lyrics": has_lyrics,
                "target_folder_name": target_folder_name,
                "target_folder": target_folder,
                "output_filename": output_filename,
                "output_path": output_path,
                "canvas_mode": canvas_mode,
                "temp_canvas_path": temp_canvas_path,
                "temp_slide_paths": temp_slide_paths,
                "stage_durations": stage_durations,
                "api_latency_ms": api_latency_ms,
                "ready_at": time.time()
            }

            with self._prefetch_lock:
                self._prefetch_cache[item_id] = artifact

            print(f"⚡ [Pre-fetch] Hoàn tất nạp trước cho Video #{item_id}! Sẵn sàng mã hóa.")
            return artifact

        except Exception as ex:
            err_msg = str(ex)
            print(f"⚠️ [Pre-fetch] Lỗi khi nạp trước Video #{item_id}: {err_msg}")
            with self._prefetch_lock:
                self._prefetch_cache[item_id] = {
                    "status": "failed",
                    "item_id": item_id,
                    "error": err_msg
                }
            return {"status": "failed", "item_id": item_id, "error": err_msg}

    def start_prefetch_thread(
        self,
        item_id: Any,
        video_path: str,
        image_path: str,
        is_multi_image: bool = False,
        image_paths: Optional[List[str]] = None
    ) -> threading.Thread:
        """
        Starts pre_fetch_item in a background daemon thread and tracks it.
        """
        with self._prefetch_lock:
            existing_thread = self._prefetch_threads.get(item_id)
            if existing_thread and existing_thread.is_alive():
                return existing_thread

            th = threading.Thread(
                target=self.pre_fetch_item,
                args=(item_id, video_path, image_path, is_multi_image, image_paths),
                daemon=True,
                name=f"prefetch_worker_{item_id}"
            )
            self._prefetch_threads[item_id] = th
            th.start()
            return th

    def render(
        self,
        item_id: Any,
        video_path: str,
        image_path: str,
        progress_callback: Optional[Callable[[str, str, Optional[str]], None]] = None,
        is_multi_image: bool = False,
        image_paths: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Execute full render sequence with granular stage timing and observer updates.
        If item was pre-fetched, reuses prepared artifacts and jumps directly to Stage 5.
        """
        video_name = os.path.basename(video_path)
        input_size_mb = os.path.getsize(video_path) / (1024 * 1024) if os.path.exists(video_path) else 0.0

        stage_durations: Dict[str, float] = {}
        api_latency_ms = 0.0
        start_pipeline_time = time.time()
        temp_audio_path = os.path.join(self.output_folder, f"temp_audio_{item_id}.mp3")
        current_stage = "audio_extraction"

        def notify(stage: str, status: str, err: Optional[str] = None):
            nonlocal current_stage
            current_stage = stage
            progress_manager.update_stage(item_id, stage, status, err)
            if progress_callback:
                progress_callback(stage, status, err)

        try:
            # Check if background pre-fetch is still active; wait up to 30s
            prefetch_thread = None
            with self._prefetch_lock:
                prefetch_thread = self._prefetch_threads.get(item_id)
            if prefetch_thread and prefetch_thread.is_alive():
                print(f"⏳ Đang chờ hoàn tất nạp trước cho Video #{item_id}...")
                prefetch_thread.join(timeout=30)

            prefetched = self.get_prefetch_artifact(item_id)
            pipelined = False

            if prefetched:
                self.pop_prefetch_artifact(item_id)
                pipelined = True
                print(f"⚡ Tái sử dụng dữ liệu nạp trước (Pipelined) cho Video #{item_id}! Bỏ qua B1-4.")
                audio_duration = prefetched['audio_duration']
                temp_audio_path = prefetched['temp_audio_path']
                raw_lyrics = prefetched['raw_lyrics']
                full_lyrics = prefetched['full_lyrics']
                lyric_source = prefetched['lyric_source']
                has_lyrics = prefetched['has_lyrics']
                target_folder_name = prefetched['target_folder_name']
                target_folder = prefetched['target_folder']
                output_filename = prefetched['output_filename']
                output_path = prefetched['output_path']
                canvas_mode = prefetched['canvas_mode']
                temp_canvas_path = prefetched['temp_canvas_path']
                temp_slide_paths = prefetched.get('temp_slide_paths', [])
                stage_durations.update(prefetched.get('stage_durations', {}))
                api_latency_ms = prefetched.get('api_latency_ms', 0.0)

                # Instant progress transition through stages 1 to 4
                notify("audio_extraction", "active")
                notify("audio_extraction", "completed")
                notify("speech_transcription", "active")
                notify("speech_transcription", "completed")
                notify("lyric_refinement", "active")
                notify("lyric_refinement", "completed")
                notify("visual_generation", "active")
                notify("visual_generation", "completed")
            else:
                # -----------------------------------------------------------------
                # STAGE 1: Audio Extraction
                # -----------------------------------------------------------------
                s1_start = time.time()
                notify("audio_extraction", "active")
                print(f"\n[1/6] 🎵 Trích xuất âm thanh: {video_name}")

                if not os.path.exists(video_path):
                    raise FileNotFoundError(f"Video nguồn không còn tồn tại: {video_path}")

                video_clip_input = VideoFileClip(video_path)
                if video_clip_input.audio is None:
                    video_clip_input.close()
                    raise ValueError("Video không có âm thanh!")

                audio_duration = float(video_clip_input.audio.duration)
                video_clip_input.audio.write_audiofile(temp_audio_path, codec='mp3', logger=None)
                video_clip_input.close()

                s1_duration = time.time() - s1_start
                stage_durations["audio_extraction"] = s1_duration
                notify("audio_extraction", "completed")

                # -----------------------------------------------------------------
                # STAGE 2: Speech Transcription (Whisper)
                # -----------------------------------------------------------------
                s2_start = time.time()
                notify("speech_transcription", "active")
                print("[2/6] 🎙️ Nhận diện giọng nói bằng Whisper...")

                raw_lyrics = extract_raw_lyrics(video_path) or ""

                s2_duration = time.time() - s2_start
                stage_durations["speech_transcription"] = s2_duration
                notify("speech_transcription", "completed")

                # -----------------------------------------------------------------
                # STAGE 3: Lyric Refinement (Gemini AI)
                # -----------------------------------------------------------------
                s3_start = time.time()
                notify("lyric_refinement", "active")

                api_call_start = time.time()
                full_lyrics, lyric_source = clean_lyrics_with_ai(raw_lyrics)
                api_latency_ms = (time.time() - api_call_start) * 1000.0

                lyric_title = get_first_line(full_lyrics, max_length=100)
                if lyric_title:
                    safe_lyric = re.sub(r'[\\/*?:"<>|#]', "", lyric_title).strip()
                    file_prefix = safe_lyric if safe_lyric else "CuocSongChill"
                else:
                    file_prefix = "CuocSongChill"

                has_lyrics = bool(lyric_source == "AI" and full_lyrics and full_lyrics.strip())
                target_folder_name = "outputs" if has_lyrics else "outputs-no-lyrics"
                target_folder = self.output_folder if has_lyrics else self.no_lyrics_folder

                existing_file_check = os.path.join(target_folder, f"{file_prefix}.mp4")
                output_filename = f"{file_prefix}_{int(time.time()) % 10000}.mp4" if os.path.exists(existing_file_check) else f"{file_prefix}.mp4"
                output_path = os.path.join(target_folder, output_filename)
                print(f"[3/6] ✨ Xử lý lyrics: \"{file_prefix}\" ({'🎵 Có lyrics' if has_lyrics else '🔇 Không lời'})")

                s3_duration = time.time() - s3_start
                stage_durations["lyric_refinement"] = s3_duration
                notify("lyric_refinement", "completed")

                # -----------------------------------------------------------------
                # STAGE 4: Visual Generation (Pillow Canvas & Overlays)
                # -----------------------------------------------------------------
                s4_start = time.time()
                notify("visual_generation", "active")
                print("[4/6] 🎨 Ghép hình ảnh & canvas lyrics...")

                target_width = 1080
                target_height = 1920
                temp_canvas_path = os.path.join(self.output_folder, f"temp_canvas_{item_id}.png")
                temp_slide_paths = []
                canvas_mode = "static"

                if is_multi_image and image_paths and len(image_paths) >= 2:
                    canvas_mode = "slideshow"
                    print(f"[4/6] 🎬 Ghép slideshow {len(image_paths)} ảnh chuyển động mượt...")
                    for s_idx, sp in enumerate(image_paths):
                        slide_path = os.path.join(self.output_folder, f"temp_slide_{item_id}_{s_idx}.png")
                        with Image.open(sp) as simg:
                            fitted = SlideshowService.fit_image_vertical(simg.convert('RGB'), target_width, target_height)
                            if os.path.exists('logo-text.png'):
                                try:
                                    with Image.open('logo-text.png') as logo_raw:
                                        logo_rgba = logo_raw.convert("RGBA")
                                        lw, lh = logo_rgba.size
                                        target_lw = 250
                                        target_lh = int(lh * (target_lw / lw))
                                        resized_logo = logo_rgba.resize((target_lw, target_lh), Image.Resampling.LANCZOS)
                                        fitted.paste(resized_logo, (target_width - target_lw - 100, 260), mask=resized_logo)
                                except Exception:
                                    pass
                            if lyric_source == "AI" and full_lyrics:
                                try:
                                    lyric_pil = create_lyrics_image_pil(full_lyrics, img_width=target_width, target_height=target_height, font_size=20)
                                    lw, lh = lyric_pil.size
                                    pos_y = max(0, (target_height - lh) // 2)
                                    fitted.paste(lyric_pil, (0, pos_y), mask=lyric_pil)
                                except Exception:
                                    pass
                            fitted.save(slide_path, "PNG")
                            temp_slide_paths.append(slide_path)
                else:
                    canvas_img = compose_full_canvas_pil(
                        image_path=image_path,
                        full_lyrics=full_lyrics if lyric_source == "AI" else None,
                        logo_path='logo-text.png',
                        target_width=target_width,
                        target_height=target_height
                    )
                    canvas_img.save(temp_canvas_path, "PNG")

                s4_duration = time.time() - s4_start
                stage_durations["visual_generation"] = s4_duration
                notify("visual_generation", "completed")

            # -----------------------------------------------------------------
            # STAGE 5: Media Encoding (High-Speed Direct FFmpeg)
            # -----------------------------------------------------------------
            s5_start = time.time()
            notify("media_encoding", "active")
            print("[5/6] 🎬 Mã hóa video siêu tốc bằng FFmpeg...")
            encoder_info = FFmpegEncoderService.probe_best_encoder()
            active_encoder = encoder_info.get('encoder', 'libx264')

            try:
                if canvas_mode == "slideshow" and temp_slide_paths:
                    FFmpegEncoderService.render_slideshow_video(
                        slide_canvas_paths=temp_slide_paths,
                        audio_path=temp_audio_path,
                        output_path=output_path,
                        total_duration=audio_duration
                    )
                else:
                    FFmpegEncoderService.render_static_video(
                        canvas_path=temp_canvas_path,
                        audio_path=temp_audio_path,
                        output_path=output_path,
                        duration=audio_duration
                    )
            except Exception as ffmpeg_err:
                print(f"⚠️ Native FFmpeg error: {ffmpeg_err}, chuyển sang MoviePy fallback...")
                bg_clip = ColorClip(size=(target_width, target_height), color=(0, 0, 0))
                try:
                    bg_clip = bg_clip.with_duration(audio_duration)
                except AttributeError:
                    bg_clip.duration = audio_duration

                if is_multi_image and image_paths and len(image_paths) >= 2:
                    slideshow_clip = SlideshowService.create_slideshow_clip(
                        image_paths=image_paths,
                        total_duration=audio_duration,
                        width=target_width,
                        height=target_height
                    )
                    clips_to_composite = [bg_clip, slideshow_clip]
                else:
                    pil_img = Image.open(image_path).convert("RGB")
                    enhancer = ImageEnhance.Brightness(pil_img)
                    dark_pil_img = enhancer.enhance(0.5)

                    img_array = np.array(dark_pil_img)
                    image_clip = ImageClip(img_array)
                    try:
                        image_clip = image_clip.with_duration(audio_duration)
                    except AttributeError:
                        image_clip.duration = audio_duration

                    img_w, img_h = image_clip.size
                    ratio = min(target_width / img_w, target_height / img_h)
                    new_w = int(img_w * ratio)
                    new_h = int(img_h * ratio)
                    try:
                        image_clip = image_clip.resized(width=new_w, height=new_h)
                    except AttributeError:
                        image_clip.resize((new_w, new_h))
                    try:
                        image_clip = image_clip.with_position(('center', 'center'))
                    except AttributeError:
                        image_clip.position = ('center', 'center')
                    clips_to_composite = [bg_clip, image_clip]

                if os.path.exists('logo-text.png'):
                    try:
                        logo_clip = ImageClip('logo-text.png')
                        try:
                            logo_clip = logo_clip.with_duration(audio_duration)
                        except AttributeError:
                            logo_clip.duration = audio_duration
                        try:
                            logo_clip = logo_clip.resized(width=250)
                        except AttributeError:
                            logo_clip.resize(width=250)
                        try:
                            logo_clip = logo_clip.with_position((target_width - logo_clip.w - 100, 260))
                        except Exception:
                            pass
                        clips_to_composite.append(logo_clip)
                    except Exception as ex:
                        print(f"⚠️ Logo overlay warning: {ex}")

                if lyric_source == "AI" and full_lyrics:
                    try:
                        lyric_array = create_lyrics_image_transparent(full_lyrics, img_width=target_width, font_size=20)
                        lyric_clip = ImageClip(lyric_array)
                        try:
                            lyric_clip = lyric_clip.with_duration(audio_duration)
                        except AttributeError:
                            lyric_clip.duration = audio_duration
                        try:
                            lyric_clip = lyric_clip.with_position(('left', 'center'))
                        except AttributeError:
                            lyric_clip.position = ('left', 'center')
                        clips_to_composite.append(lyric_clip)
                    except Exception as ex:
                        print(f"⚠️ Lyrics overlay warning: {ex}")

                final_clip = CompositeVideoClip(clips_to_composite)
                try:
                    final_clip = final_clip.with_duration(audio_duration)
                except AttributeError:
                    final_clip.duration = audio_duration

                audio_clip = AudioFileClip(temp_audio_path)
                try:
                    final_clip = final_clip.with_audio(audio_clip)
                except AttributeError:
                    final_clip.audio = audio_clip

                final_clip.write_videofile(
                    output_path,
                    fps=24,
                    codec='libx264',
                    audio_codec='aac',
                    preset='ultrafast',
                    threads=4,
                    logger=None
                )
                final_clip.close()
                audio_clip.close()

            s5_duration = time.time() - s5_start
            stage_durations["media_encoding"] = s5_duration
            notify("media_encoding", "completed")

            # -----------------------------------------------------------------
            # STAGE 6: Finalization & Cleanup
            # -----------------------------------------------------------------
            s6_start = time.time()
            notify("finalization", "active")

            if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                raise RuntimeError("File video đầu ra không được tạo thành công hoặc bị rỗng!")

            if os.path.exists(temp_audio_path):
                try:
                    os.remove(temp_audio_path)
                except Exception:
                    pass

            if os.path.exists(temp_canvas_path):
                try:
                    os.remove(temp_canvas_path)
                except Exception:
                    pass

            for sp in temp_slide_paths:
                if os.path.exists(sp):
                    try:
                        os.remove(sp)
                    except Exception:
                        pass

            if os.path.exists(video_path):
                try:
                    os.remove(video_path)
                except Exception:
                    pass

            # Record into videos_db.json
            video_db = load_video_db()
            video_record = {
                'id': f"vid_{int(datetime.now().timestamp() * 1000)}",
                'filename': output_filename,
                'path': os.path.abspath(output_path),
                'output_folder': target_folder_name,
                'has_lyrics': has_lyrics,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'Chờ duyệt'
            }
            video_db.insert(0, video_record)
            save_video_db(video_db)

            s6_duration = time.time() - s6_start
            stage_durations["finalization"] = s6_duration

            total_pipeline_duration = time.time() - start_pipeline_time

            # Record telemetry
            telemetry_manager.record_render(
                video_name=video_name,
                input_duration_s=audio_duration,
                input_size_mb=input_size_mb,
                stage_durations=stage_durations,
                api_latency_ms=api_latency_ms,
                total_duration_s=total_pipeline_duration,
                status="completed",
                encoder_backend=active_encoder,
                pipelined=pipelined,
                speedup_factor=round(180.0 / max(1.0, total_pipeline_duration), 2)
            )

            progress_manager.complete_item(item_id, output_filename)
            notify("finalization", "completed")
            print(f"[6/6] ✅ Hoàn tất: {output_filename} -> {target_folder_name}/ ({int(round(total_pipeline_duration))}s)")

            return {
                "success": True,
                "output_file": output_filename,
                "output_folder": target_folder_name,
                "has_lyrics": has_lyrics,
                "output_path": os.path.abspath(output_path),
                "duration_s": total_pipeline_duration,
                "stage_durations": stage_durations
            }

        except Exception as e:
            err_msg = str(e)
            print(f"❌ Error during stage '{current_stage}': {err_msg}")
            notify(current_stage, "failed", err_msg)
            progress_manager.fail_item(item_id, current_stage, err_msg)

            # Clean up temp audio if created
            if os.path.exists(temp_audio_path):
                try:
                    os.remove(temp_audio_path)
                except Exception:
                    pass

            # Record failed telemetry if audio_duration known
            try:
                total_failed_duration = time.time() - start_pipeline_time
                telemetry_manager.record_render(
                    video_name=video_name,
                    input_duration_s=0.0,
                    input_size_mb=input_size_mb,
                    stage_durations=stage_durations,
                    api_latency_ms=api_latency_ms,
                    total_duration_s=total_failed_duration,
                    status="failed"
                )
            except Exception:
                pass

            return {
                "success": False,
                "error": err_msg,
                "failing_stage": current_stage
            }


# Global shared pipeline instance
render_pipeline = RenderPipeline()

