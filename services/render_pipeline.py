import os
import re
import time
import json
from datetime import datetime
from typing import Callable, Optional, Dict, Any

from moviepy import ImageClip, AudioFileClip, VideoFileClip, ColorClip, CompositeVideoClip
from PIL import Image, ImageEnhance, ImageDraw, ImageFont
import numpy as np

from extract_lyrics import extract_raw_lyrics, clean_lyrics_with_ai, get_first_line
from services.progress_manager import progress_manager
from services.telemetry_manager import telemetry_manager

VIDEOS_DB_FILE = 'videos_db.json'

def create_lyrics_image_transparent(text: str, img_width: int = 1080, target_height: int = 1920, font_size: int = 20) -> np.ndarray:
    """
    Generate transparent image containing full lyrics, bounded at max 90% of target video height.
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

    cropped_img = txt_img.crop((0, 0, img_width, final_height))
    return np.array(cropped_img)


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

    def render(
        self,
        item_id: Any,
        video_path: str,
        image_path: str,
        progress_callback: Optional[Callable[[str, str, Optional[str]], None]] = None
    ) -> Dict[str, Any]:
        """
        Execute full render sequence with granular stage timing and observer updates.
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

            bg_clip = ColorClip(size=(target_width, target_height), color=(0, 0, 0))
            try:
                bg_clip = bg_clip.with_duration(audio_duration)
            except AttributeError:
                bg_clip.duration = audio_duration

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
            logo_path = 'logo-text.png'
            if os.path.exists(logo_path):
                try:
                    logo_clip = ImageClip(logo_path)
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

            s4_duration = time.time() - s4_start
            stage_durations["visual_generation"] = s4_duration
            notify("visual_generation", "completed")

            # -----------------------------------------------------------------
            # STAGE 5: Media Encoding (MoviePy / FFmpeg)
            # -----------------------------------------------------------------
            s5_start = time.time()
            notify("media_encoding", "active")
            print("[5/6] 🎬 Ghép video & mã hóa MP4 (libx264/aac)...")

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
                preset='veryfast',
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
                os.remove(temp_audio_path)

            if os.path.exists(video_path):
                os.remove(video_path)

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
                status="completed"
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

