import os
import random
import threading
import webbrowser
from flask import Flask, render_template, request, jsonify, send_from_directory
from moviepy import ImageClip, AudioFileClip, VideoFileClip, ColorClip, CompositeVideoClip
from PIL import Image, ImageEnhance
import numpy as np

app = Flask(__name__)

OUTPUT_FOLDER = 'outputs'
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

session_data = {
    'image_folder': '',
    'video_folder': '',
    'queue': []
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/load-folders', methods=['POST'])
def load_folders():
    data = request.json
    img_folder = data.get('image_folder', '').strip()
    vid_folder = data.get('video_folder', '').strip()

    if not img_folder or not vid_folder or not os.path.isdir(img_folder) or not os.path.isdir(vid_folder):
        return jsonify({'success': False, 'error': 'Đường dẫn thư mục không hợp lệ hoặc không tồn tại!'}), 400

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
        # 1. Trích xuất audio từ video gốc
        video_clip_input = VideoFileClip(vid_path)
        if video_clip_input.audio is None:
            video_clip_input.close()
            return jsonify({'success': False, 'error': 'Video không có âm thanh!'}), 400

        temp_audio_path = os.path.join(app.config['OUTPUT_FOLDER'], f'temp_audio_{item_id}.mp3')
        video_clip_input.audio.write_audiofile(temp_audio_path, codec='mp3', logger=None)
        audio_duration = video_clip_input.audio.duration
        video_clip_input.close()

        # 2. Định dạng video dọc cho điện thoại (1080x1920)
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

        # 3. Xử lý ảnh nền: Giảm độ sáng 20% bằng PIL
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

        # 4. Thêm Logo vào góc trên bên phải (logo-text.png)
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

            # Fit chiều rộng logo tầm 250px
            try:
                logo_clip = logo_clip.resized(width=250)
            except AttributeError:
                try:
                    logo_clip = logo_clip.resize(width=250)
                except Exception:
                    pass

            try:
                logo_clip = logo_clip.with_position((target_width - logo_clip.w - 50, 50))
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

        # 5. Gắn âm thanh vào video
        audio_clip = AudioFileClip(temp_audio_path)
        try:
            final_clip = final_clip.with_audio(audio_clip)
        except AttributeError:
            try:
                final_clip = final_clip.set_audio(audio_clip)
            except AttributeError:
                final_clip.audio = audio_clip

        output_filename = f"rendered_{os.path.splitext(target_item['video_name'])[0]}.mp4"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

        # 6. Render với tốc độ tối ưu (veryfast + multi-threading)
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

        return jsonify({'success': True, 'output_file': output_filename})

    except Exception as e:
        target_item['status'] = 'Lỗi'
        return jsonify({'success': False, 'error': str(e)}), 500

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
    """Tự động mở trình duyệt sau khi server khởi động xong 1.2 giây"""
    webbrowser.open_new('http://127.0.0.1:5000/')

if __name__ == '__main__':
    # Tạo luồng mở trình duyệt tự động
    threading.Timer(1.2, open_browser).start()
    
    # Chạy Flask Server
    app.run(debug=False, port=5000)