import os
import json
import random
import threading
import webbrowser
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from moviepy import ImageClip, AudioFileClip, VideoFileClip, ColorClip, CompositeVideoClip
from PIL import Image, ImageEnhance
import numpy as np

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

def generate_ai_caption(video_filename):
    """
    Tạo caption thu hút (có thể thay thế hoặc tích hợp API AI như Gemini/OpenAI ở đây).
    Hiện tại dùng bộ từ khóa bắt trend kết hợp tên gốc để tạo sự đa dạng và hấp dẫn.
    """
    # Lấy tên gốc bỏ phần mở rộng và thay thế dấu gạch bằng khoảng trắng
    base_name = os.path.splitext(video_filename)[0]
    base_name = re.sub(r'[_.-]', ' ', base_name).strip()
    
    # Danh sách tiền tố bắt trend (Bạn có thể gọi API AI thay cho đoạn ngẫu nhiên này)
    trending_vibes = [
        "Xuhuong", "Cucchill", "Meman", "Sieupham", 
        "Docquyen", "Trending", "Gocnhin", "Hoamyle"
    ]
    
    prefix = random.choice(trending_vibes)
    caption = f"{prefix}_{base_name}"
    return caption

def sanitize_filename(text):
    """
    Loại bỏ các ký tự đặc biệt không hợp lệ trong tên file hệ điều hành 
    (như \, /, :, *, ?, ", <, >, |) và giới hạn độ dài.
    """
    # Xóa dấu tiếng Việt (tùy chọn, giúp tên file gọn gàng không lỗi font hệ thống)
    # Hoặc giữ nguyên và chỉ lọc các ký tự cấm:
    safe_text = re.sub(r'[\\/*?:"<>|#]', "", text)
    # Thay khoảng trắng bằng dấu gạch dưới
    safe_text = safe_text.strip().replace(" ", "_")
    # Giới hạn độ dài tối đa 50 ký tự cho tên file đẹp mắt
    return safe_text[:50]

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
    videos = [os.path.join(vid_folder, f) for f in os.listdir(vid_folder) if f.lower().endswith(video_extensions)]

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

        bg_clip = ColorClip(size=(target_width, target_height), color=(0, 0, 0))
        try:
            bg_clip = bg_clip.with_duration(audio_duration)
        except AttributeError:
            try:
                bg_clip = bg_clip.set_duration(audio_duration)
            except AttributeError:
                bg_clip.duration = audio_duration

        pil_img = Image.open(img_path).convert("RGB")
        enhancer = ImageEnhance.Brightness(pil_img)
        dark_pil_img = enhancer.enhance(0.5) # Giảm 50% độ sáng
        
        img_array = np.array(dark_pil_img)
        image_clip = ImageClip(img_array)
        
        try:
            image_clip = image_clip.with_duration(audio_duration)
        except AttributeError:
            try:
                image_clip = image_clip.set_duration(audio_duration)
            except AttributeError:
                image_clip.duration = audio_duration

        img_w, img_h = image_clip.size
        ratio = min(target_width / img_w, target_height / img_h)
        new_w = int(img_w * ratio)
        new_h = int(img_h * ratio)

        try:
            image_clip = image_clip.resized(width=new_w, height=new_h)
        except AttributeError:
            try:
                image_clip = image_clip.resize((new_w, new_h))
            except Exception:
                pass

        try:
            image_clip = image_clip.with_position(('center', 'center'))
        except AttributeError:
            try:
                image_clip = image_clip.set_position(('center', 'center'))
            except AttributeError:
                image_clip.position = ('center', 'center')

        clips_to_composite = [bg_clip, image_clip]
        logo_path = 'logo-text.png'

        if os.path.exists(logo_path):
            logo_clip = ImageClip(logo_path)
            try:
                logo_clip = logo_clip.with_duration(audio_duration)
            except AttributeError:
                try:
                    logo_clip = logo_clip.set_duration(audio_duration)
                except AttributeError:
                    logo_clip.duration = audio_duration

            try:
                logo_clip = logo_clip.resized(width=250)
            except AttributeError:
                try:
                    logo_clip = logo_clip.resize(width=250)
                except Exception:
                    pass

            try:
                # Cách lề phải 90px và lề trên 90px
                logo_clip = logo_clip.with_position((target_width - logo_clip.w - 100, 220))
            except Exception:
                pass

            clips_to_composite.append(logo_clip)

        final_clip = CompositeVideoClip(clips_to_composite)
        
        try:
            final_clip = final_clip.with_duration(audio_duration)
        except AttributeError:
            try:
                final_clip = final_clip.set_duration(audio_duration)
            except AttributeError:
                final_clip.duration = audio_duration

        audio_clip = AudioFileClip(temp_audio_path)
        try:
            final_clip = final_clip.with_audio(audio_clip)
        except AttributeError:
            try:
                final_clip = final_clip.set_audio(audio_clip)
            except AttributeError:
                final_clip.audio = audio_clip

        # Tên file theo định dạng đơn giản hóa mới
        now = datetime.now()
        year_month = now.strftime("%Y.%m")
        timestamp_str = int(now.timestamp() * 1000)
        
        output_filename = f"CuocSongChill - {year_month}.{timestamp_str}.mp4"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

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

        # --- LƯU ĐƯỜNG DẪN TUYỆT ĐỐI ĐẦY ĐỦ VÀO JSON ---
        absolute_output_path = os.path.abspath(output_path)

        # Ghi thông tin video thành phẩm mới vào file videos_db.json (Mặc định: Chờ duyệt)
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