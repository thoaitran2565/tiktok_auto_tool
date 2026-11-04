import os
import json
import random
import threading
import webbrowser
from datetime import datetime
import re
from flask import Flask, render_template, request, jsonify, send_from_directory
from moviepy import ImageClip, AudioFileClip, VideoFileClip, ColorClip, CompositeVideoClip
from PIL import Image, ImageEnhance, ImageDraw, ImageFont # Cập nhật thêm ImageDraw, ImageFont nếu chưa có
import numpy as np
from extract_lyrics import process_video_to_perfect_lyrics

app = Flask(__name__)

OUTPUT_FOLDER = 'outputs'
CONFIG_FILE = 'config.json'
VIDEOS_DB_FILE = 'videos_db.json'

os.makedirs(OUTPUT_FOLDER, exist_ok=True)
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# Khởi tạo các file JSON nếu chưa tồn tại
if not os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump({'image_folder': '', 'video_folder': ''}, f, ensure_ascii=False, indent=4)

if not os.path.exists(VIDEOS_DB_FILE):
    with open(VIDEOS_DB_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f, ensure_ascii=False, indent=4)

session_data = {
    'image_folder': '',
    'video_folder': '',
    'queue': []
}



def create_lyrics_image_transparent(text, img_width=1080, target_height=1920, font_size=20):
    """
    Tạo ảnh chứa toàn bộ lyrics trong suốt, giới hạn chiều cao tối đa 90% video.
    Nếu lyrics dài vượt quá ngưỡng thì cắt bớt phần cuối, giữ nguyên phần đầu.
    """
    # Chiều cao tối đa cho phép bằng 90% chiều cao video (1920 * 0.9 = 1728px)
    max_allowed_height = int(target_height * 0.9)
    
    # Bước 1: Tạo một ảnh tạm có chiều cao lớn (ví dụ 4000px) để đo và vẽ trọn vẹn mọi dòng text dài
    temp_img_height = 4000
    txt_img = Image.new('RGBA', (img_width, temp_img_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(txt_img)
    
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()
        
    x = 80  # Cách lề trái 80px
    y = 50  # Khoảng cách từ đỉnh khung xuống dòng đầu tiên
    
    # Vẽ viền đen xung quanh chữ trắng để tạo hiệu ứng nổi trên nền video
    for adj_x, adj_y in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        draw.multiline_text((x + adj_x, y + adj_y), text, font=font, fill=(0, 0, 0, 255), spacing=10, align="left")
    
    # Vẽ chữ trắng chính giữa đè lên trên
    draw.multiline_text((x, y), text, font=font, fill=(255, 255, 255, 255), spacing=10, align="left")
    
    # Bước 2: Đo kích thước thực tế của khối text vừa vẽ
    bbox = draw.multiline_textbbox((x, y), text, font=font, spacing=10)
    text_bottom_y = bbox[3] + 30  # Cộng thêm một khoảng đệm an toàn phía dưới
    
    # Bước 3: Cắt (crop) ảnh lại theo đúng chiều cao thực tế hoặc giới hạn tối đa 90%
    final_height = min(int(text_bottom_y), max_allowed_height)
    
    cropped_img = txt_img.crop((0, 0, img_width, final_height))
    
    return np.array(cropped_img)

def load_video_db():
    try:
        with open(VIDEOS_DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []

def save_video_db(data):
    with open(VIDEOS_DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/manage')
def manage():
    return render_template('manage.html')

@app.route('/api/get-config', methods=['GET'])
def get_config():
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return jsonify({'success': True, 'config': config})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/load-folders', methods=['POST'])
def load_folders():
    data = request.json
    img_folder = data.get('image_folder', '').strip()
    vid_folder = data.get('video_folder', '').strip()

    if not img_folder or not vid_folder or not os.path.isdir(img_folder) or not os.path.isdir(vid_folder):
        return jsonify({'success': False, 'error': 'Đường dẫn thư mục không hợp lệ hoặc không tồn tại!'}), 400

    # Lưu lại đường dẫn đầu vào cho lần sau
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump({'image_folder': img_folder, 'video_folder': vid_folder}, f, ensure_ascii=False, indent=4)

    session_data['image_folder'] = img_folder
    session_data['video_folder'] = vid_folder

    image_extensions = ('.png', '.jpg', '.jpeg', '.webp')
    video_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.webm')

    images = [os.path.join(img_folder, f) for f in os.listdir(img_folder) if f.lower().endswith(image_extensions)]
    # Dùng os.scandir để quét cực nhanh
    videos = [
    os.path.join(vid_folder, entry.name) 
    for entry in os.scandir(vid_folder) 
    if entry.is_file() and entry.name.lower().endswith(video_extensions)
    ]
    videos.sort()

    if not images:
        return jsonify({'success': False, 'error': 'Thư mục ảnh không chứa file ảnh nào!'}), 400
    if not videos:
        return jsonify({'success': False, 'error': 'Thư mục video không chứa file video nào!'}), 400

    videos.sort()

    queue = []
    for idx, vid_path in enumerate(videos):
        rand_image = random.choice(images)
        queue.append({
            'id': idx,
            'video_path': vid_path,
            'video_name': os.path.basename(vid_path),
            'image_path': rand_image,
            'image_name': os.path.basename(rand_image),
            'status': 'Chờ render',
            'output_file': ''
        })

    session_data['queue'] = queue

    return jsonify({
        'success': True,
        'available_images': [os.path.basename(img) for img in images],
        'queue': [{
            'id': item['id'],
            'video_name': item['video_name'],
            'image_name': item['image_name'],
            'status': item['status']
        } for item in queue]
    })

@app.route('/api/update-queue', methods=['POST'])
def update_queue():
    data = request.json
    item_id = data.get('id')
    new_image_name = data.get('image_name')

    img_folder = session_data['image_folder']
    new_image_path = os.path.join(img_folder, new_image_name)

    if not os.path.exists(new_image_path):
        return jsonify({'success': False, 'error': 'Ảnh không tồn tại!'}), 400

    for item in session_data['queue']:
        if item['id'] == item_id:
            item['image_path'] = new_image_path
            item['image_name'] = new_image_name
            return jsonify({'success': True})

    return jsonify({'success': False, 'error': 'Không tìm thấy!'}), 404

@app.route('/api/render-single', methods=['POST'])
def render_single():
    data = request.json
    item_id = data.get('id')

    target_item = None
    for item in session_data['queue']:
        if item['id'] == item_id:
            target_item = item
            break

    if not target_item:
        return jsonify({'success': False, 'error': 'Không tìm thấy video trong hàng đợi!'}), 404

    vid_path = target_item['video_path']
    img_path = target_item['image_path']

    if not os.path.exists(vid_path):
        return jsonify({'success': False, 'error': 'Video nguồn không còn tồn tại!'}), 400

    try:
        video_clip_input = VideoFileClip(vid_path)
        if video_clip_input.audio is None:
            video_clip_input.close()
            return jsonify({'success': False, 'error': 'Video không có âm thanh!'}), 400

        temp_audio_path = os.path.join(app.config['OUTPUT_FOLDER'], f'temp_audio_{item_id}.mp3')
        video_clip_input.audio.write_audiofile(temp_audio_path, codec='mp3', logger=None)
        audio_duration = video_clip_input.audio.duration
        video_clip_input.close()

        target_width = 1080
        target_height = 1920

        # --- BƯỚC 1: TRÍCH XUẤT LYRICS TRƯỚC KHI RENDER ---
        lyric_result = process_video_to_perfect_lyrics(vid_path, max_length=100)
        lyric_title = lyric_result.get("first_line", "").strip()     # Dùng làm tên file
        full_lyrics = lyric_result.get("full_lyrics", "").strip()    # Dùng để dán lên video
        lyric_source = lyric_result.get("source", "Original")
        
        print(f"🎵 Đã nhận diện lyrics (Nguồn: {lyric_source}): {lyric_title}")

        # --- BƯỚC 2: XỬ LÝ TÊN FILE ---
        if lyric_title:
            safe_lyric = re.sub(r'[\\/*?:"<>|#]', "", lyric_title)
            safe_lyric = safe_lyric.strip()
            file_prefix = safe_lyric
        else:
            file_prefix = "CuocSongChill"

        output_filename = f"{file_prefix}.mp4"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

        # --- BƯỚC 3: DỰNG HÌNH NỀN & ẢNH ---
        bg_clip = ColorClip(size=(target_width, target_height), color=(0, 0, 0))
        try:
            bg_clip = bg_clip.with_duration(audio_duration)
        except AttributeError:
            bg_clip.duration = audio_duration

        pil_img = Image.open(img_path).convert("RGB")
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

        # --- BƯỚC 4: NẾU NGUỒN TỪ AI MODEL THÌ THÊM LYRICS LÊN VIDEO ---
        if lyric_source == "AI" and full_lyrics:
            try:
                lyric_array = create_lyrics_image_transparent(full_lyrics, img_width=target_width, font_size=20)
                lyric_clip = ImageClip(lyric_array)
                
                try:
                    lyric_clip = lyric_clip.with_duration(audio_duration)
                except AttributeError:
                    lyric_clip.duration = audio_duration
                
                # Cỡ chữ nhỏ, đặt ở góc trái (left) và canh giữa chiều dọc (center)
                try:
                    lyric_clip = lyric_clip.with_position(('left', 'center'))
                except AttributeError:
                    lyric_clip.position = ('left', 'center')
                    
                clips_to_composite.append(lyric_clip)
                print("✨ Đã chèn lyrics AI lên video (Góc trái, canh giữa dọc, không nền).")
            except Exception as ex:
                print(f"⚠️ Lỗi khi chèn lyrics lên video: {ex}")

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
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)

        os.remove(vid_path)
        target_item['status'] = 'Hoàn thành'
        target_item['output_file'] = output_filename

        absolute_output_path = os.path.abspath(output_path)

        video_db = load_video_db()
        new_video_record = {
            'id': f"vid_{int(datetime.now().timestamp() * 1000)}",
            'filename': output_filename,
            'path': absolute_output_path,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'Chờ duyệt'
        }
        video_db.insert(0, new_video_record)
        save_video_db(video_db)

        return jsonify({'success': True, 'output_file': output_filename})

    except Exception as e:
        target_item['status'] = 'Lỗi'
        return jsonify({'success': False, 'error': str(e)}), 500

# API Lấy danh sách video từ JSON
@app.route('/api/get-videos-db', methods=['GET'])
def get_videos_db():
    db = load_video_db()
    return jsonify({'success': True, 'videos': db})

# API Cập nhật trạng thái video
@app.route('/api/update-video-status', methods=['POST'])
def update_video_status():
    data = request.json
    video_id = data.get('id')
    new_status = data.get('status')

    db = load_video_db()
    updated = False
    for item in db:
        if item['id'] == video_id:
            item['status'] = new_status
            updated = True
            break

    if updated:
        save_video_db(db)
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Không tìm thấy video!'}), 404

@app.route('/media/image-by-name/<filename>')
def get_image_by_name(filename):
    img_folder = session_data.get('image_folder', '')
    if img_folder:
        full_path = os.path.join(img_folder, filename)
        if os.path.exists(full_path):
            return send_from_directory(img_folder, filename)
    return "", 404

@app.route('/media/video')
def get_video():
    path = request.args.get('path')
    if path and os.path.exists(path):
        return send_from_directory(os.path.dirname(path), os.path.basename(path))
    return "", 404

@app.route('/outputs/<path:filename>')
def get_output_video(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename, as_attachment=True)

def open_browser():
    webbrowser.open_new('http://127.0.0.1:5000/')

# API Cập nhật hàng loạt trạng thái sang "Đã duyệt" cho các video "Chờ duyệt"
@app.route('/api/approve-all-pending', methods=['POST'])
def approve_all_pending():
    db = load_video_db()
    count = 0
    for item in db:
        if item.get('status') == 'Chờ duyệt':
            item['status'] = 'Đã duyệt'
            count += 1

    if count > 0:
        save_video_db(db)
    
    return jsonify({'success': True, 'approved_count': count})

if __name__ == '__main__':
    threading.Timer(1.2, open_browser).start()
    app.run(debug=False, port=5000)