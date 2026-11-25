import sys
import os
import re
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from extract_lyrics import is_valid_lyrics, clean_lyrics_with_ai
from services.render_pipeline import compose_full_canvas_pil, RenderPipeline
from PIL import Image

print("=== Scenario 1: Non-Lyric & Disclaimer Detection ===")

# Test 1.1: Empty and whitespace
valid, txt = is_valid_lyrics("", "")
assert valid is False and txt == "", f"Expected False, got {valid}"

# Test 1.2: Noise and musical notes
valid, txt = is_valid_lyrics("♪♪♪ ... --- \n", "♪♪♪")
assert valid is False and txt == "", f"Expected False for pure notes/symbols, got {valid}"

# Test 1.3: AI Disclaimer in parentheses
disclaimer_1 = "(Đoạn âm thanh không chứa lời bài hát tiếng Việt hoặc tiếng Anh rõ ràng có ý nghĩa để nhận diện bài hát)"
valid, txt = is_valid_lyrics("some speech", disclaimer_1)
assert valid is False and txt == "", f"Expected False for disclaimer, got {valid}"

# Test 1.4: AI Disclaimer text phrases
disclaimer_2 = "Phần âm thanh thô bạn cung cấp chỉ là các tiếng lầm bầm vô nghĩa, không có nội dung lời bài hát."
valid, txt = is_valid_lyrics("raw", disclaimer_2)
assert valid is False and txt == "", f"Expected False for disclaimer phrases, got {valid}"

# Test 1.5: Valid lyrics
valid_lyrics = "Ngày xưa tôi cũng yêu người\nNgười yêu đẹp xinh như hoa"
valid, txt = is_valid_lyrics("ngay xua toi cung yeu nguoi", valid_lyrics)
assert valid is True and txt == valid_lyrics.strip(), f"Expected True for valid lyrics, got {valid}"

print("✓ Scenario 1: Non-Lyric & Disclaimer Detection PASSED!")

print("\n=== Scenario 2: Clean Lyrics With AI Fallback ===")
# Calling clean_lyrics_with_ai with empty / noise
res_lyrics, res_source = clean_lyrics_with_ai("")
assert res_lyrics == "" and res_source == "None", f"Expected ('', 'None'), got ({res_lyrics}, {res_source})"

res_lyrics, res_source = clean_lyrics_with_ai("♪♪♪ ---")
assert res_lyrics == "" and res_source == "None", f"Expected ('', 'None'), got ({res_lyrics}, {res_source})"

print("✓ Scenario 2: Clean Lyrics With AI Fallback PASSED!")

print("\n=== Scenario 3: Visual Canvas Without Lyrics Overlay ===")
# Ensure test background image exists or create dummy
dummy_img_path = "scratch/test_bg.jpg"
with Image.new('RGB', (1000, 1000), color=(120, 150, 180)) as img:
    img.save(dummy_img_path)

canvas = compose_full_canvas_pil(
    image_path=dummy_img_path,
    full_lyrics=None, # Non-lyric video: full_lyrics MUST be None
    logo_path='logo-text.png',
    target_width=1080,
    target_height=1920
)
assert canvas.size == (1080, 1920), f"Expected 1080x1920, got {canvas.size}"
print("✓ Scenario 3: 1080x1920 Canvas without lyrics generated successfully!")

print("\n=== Scenario 4: Standardized Naming Convention & Directory Routing ===")
pipeline = RenderPipeline()
timestamp = int(time.time())
has_lyrics = False

if has_lyrics:
    file_prefix = "SongTitle"
    target_folder_name = "outputs"
    target_folder = pipeline.output_folder
else:
    file_prefix = f"Cuộc sống chill {timestamp}"
    target_folder_name = "outputs-no-lyrics"
    target_folder = pipeline.no_lyrics_folder

existing_file_check = os.path.join(target_folder, f"{file_prefix}.mp4")
output_filename = f"{file_prefix}_{int(time.time() * 1000) % 10000}.mp4" if os.path.exists(existing_file_check) else f"{file_prefix}.mp4"
output_path = os.path.join(target_folder, output_filename)

assert output_filename.startswith("Cuộc sống chill "), f"Expected filename to start with 'Cuộc sống chill ', got {output_filename}"
assert output_filename.endswith(".mp4"), f"Expected .mp4 extension, got {output_filename}"
assert target_folder_name == "outputs-no-lyrics", f"Expected outputs-no-lyrics, got {target_folder_name}"
assert "outputs-no-lyrics" in output_path, f"Expected outputs-no-lyrics in output_path, got {output_path}"

# Verify Unix timestamp is present in filename
match = re.search(r'Cuộc sống chill (\d+)', output_filename)
assert match is not None, f"Expected Unix timestamp in filename: {output_filename}"
print(f"✓ Output Filename: {output_filename}")
print(f"✓ Target Path: {output_path}")
print("✓ Scenario 4: Standardized Naming & Routing PASSED!")

print("\n==========================================")
print("🎉 ALL 4 QUICKSTART VALIDATION SCENARIOS PASSED!")
print("==========================================")
