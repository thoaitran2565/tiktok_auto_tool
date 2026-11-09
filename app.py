import os
import threading
import webbrowser
from flask import Flask, render_template, request, jsonify, send_from_directory

from services.config_service import ConfigService
from services.scanner_service import ScannerService
from services.queue_service import QueueService
from services.progress_manager import progress_manager
from services.telemetry_manager import telemetry_manager
from services.render_pipeline import (
    render_pipeline,
    load_video_db,
    save_video_db
)

app = Flask(__name__)

OUTPUT_FOLDER = 'outputs'
OUTPUT_NO_LYRICS_FOLDER = 'outputs-no-lyrics'
DATA_FOLDER = 'data'

os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_NO_LYRICS_FOLDER, exist_ok=True)
os.makedirs(DATA_FOLDER, exist_ok=True)
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['OUTPUT_NO_LYRICS_FOLDER'] = OUTPUT_NO_LYRICS_FOLDER

# Khởi tạo thư mục phiên từ cấu hình đã lưu nếu có
_init_img, _init_vid = ConfigService.get_configured_folders()
if _init_img or _init_vid:
    QueueService.set_session_folders(_init_img, _init_vid)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/manage')
def manage():
    return render_template('manage.html')


@app.route('/api/get-config', methods=['GET'])
def get_config():
    config = ConfigService.load_config()
    return jsonify({'success': True, 'config': config})


@app.route('/api/load-folders', methods=['POST'])
def load_folders():
    data = request.json or {}
    img_folder = data.get('image_folder', '')
    vid_folder = data.get('video_folder', '')

    success, error_msg, payload = QueueService.init_queue_from_folders(img_folder, vid_folder)
    if not success:
        return jsonify({'success': False, 'error': error_msg}), 400

    return jsonify({'success': True, **payload})


@app.route('/api/refresh-queue', methods=['POST'])
def refresh_queue():
    success, error_msg, payload = QueueService.refresh_queue_state()
    if not success:
        return jsonify({'success': False, 'error': error_msg}), 400

    return jsonify({'success': True, **payload})


@app.route('/api/update-queue', methods=['POST'])
def update_queue():
    data = request.json or {}
    item_id = data.get('id')
    new_image_name = data.get('image_name')
    is_multi_image = data.get('is_multi_image')
    image_count = data.get('image_count')
    image_list = data.get('image_list')

    success, error_msg = QueueService.update_item_image(
        item_id=item_id,
        image_name=new_image_name,
        is_multi_image=is_multi_image,
        image_count=image_count,
        image_list=image_list
    )
    if not success:
        return jsonify({'success': False, 'error': error_msg}), 400

    item = QueueService.get_item(item_id)
    return jsonify({
        'success': True,
        'item': {
            'id': item_id,
            'image_name': item.get('image_name', '') if item else '',
            'is_multi_image': item.get('is_multi_image', False) if item else False,
            'image_count': item.get('image_count', 10) if item else 10,
            'image_list': item.get('image_list', []) if item else []
        }
    })


@app.route('/api/toggle-multi-image', methods=['POST'])
def toggle_multi_image():
    data = request.json or {}
    item_id = data.get('id')
    enabled = bool(data.get('enabled', data.get('is_multi_image', False)))
    success, error_msg, payload = QueueService.toggle_multi_image(item_id, enabled)
    if not success:
        return jsonify({'success': False, 'error': error_msg}), 400
    return jsonify({'success': True, **payload})


@app.route('/api/update-multi-count', methods=['POST'])
def update_multi_count():
    data = request.json or {}
    item_id = data.get('id')
    if 'delta' in data:
        item = QueueService.get_item(item_id)
        current = int(item.get('image_count', 10)) if item else 10
        count = current + int(data.get('delta', 0))
    else:
        count = int(data.get('count', 10))
    success, error_msg, payload = QueueService.update_multi_image_count(item_id, count)
    if not success:
        return jsonify({'success': False, 'error': error_msg}), 400
    return jsonify({'success': True, **payload})


@app.route('/api/reroll-multi-images', methods=['POST'])
def reroll_multi_images():
    data = request.json or {}
    item_id = data.get('id')
    success, error_msg, payload = QueueService.reroll_multi_images(item_id)
    if not success:
        return jsonify({'success': False, 'error': error_msg}), 400
    return jsonify({'success': True, **payload})


@app.route('/api/random-images-batch', methods=['POST'])
def get_random_images_batch():
    data = request.json or {}
    count = int(data.get('count', 10))
    exclude = data.get('exclude', [])

    img_folder, _ = QueueService.get_session_folders()
    if not img_folder:
        img_folder, _ = ConfigService.get_configured_folders()

    if not img_folder or not os.path.isdir(img_folder):
        return jsonify({'success': False, 'error': 'Chưa chọn thư mục ảnh hợp lệ!'}), 400

    images = ScannerService.get_random_images_batch(img_folder, count=count, exclude=exclude)
    return jsonify({'success': True, 'images': images})


@app.route('/api/random-image', methods=['GET'])
def get_random_image():
    img_folder, _ = QueueService.get_session_folders()
    if not img_folder:
        img_folder, _ = ConfigService.get_configured_folders()

    if not img_folder or not os.path.isdir(img_folder):
        return jsonify({'success': False, 'error': 'Chưa chọn thư mục ảnh hợp lệ!'}), 400

    chosen = ScannerService.get_random_image(img_folder)
    if not chosen:
        return jsonify({'success': False, 'error': 'Thư mục không có ảnh hợp lệ!'}), 400

    return jsonify({'success': True, 'image_name': chosen})


@app.route('/api/render-single', methods=['POST'])
def render_single():
    data = request.json or {}
    item_id = data.get('id')

    target_item = QueueService.get_item(item_id)
    if not target_item:
        return jsonify({'success': False, 'error': 'Không tìm thấy video trong hàng đợi!'}), 404

    vid_path = target_item.get('video_path', '')
    img_path = target_item.get('image_path', '')

    if not os.path.exists(vid_path):
        return jsonify({'success': False, 'error': 'Video nguồn không còn tồn tại!'}), 400

    # Đo thời lượng thực tế tức thì trước khi render
    dur_s = target_item.get('duration_s')
    if not dur_s or dur_s <= 0:
        dur_s = ScannerService.probe_single_video_duration(vid_path)
        target_item['duration_s'] = dur_s

    size_mb = os.path.getsize(vid_path) / (1024 * 1024) if os.path.exists(vid_path) else 0.0
    target_item['size_mb'] = round(size_mb, 2)
    initial_estimate = telemetry_manager.predict_duration(dur_s, size_mb)

    # Khởi tạo theo dõi tiến độ
    progress_manager.init_item(item_id, target_item['video_name'], initial_estimate)
    target_item['status'] = 'Đang render'

    is_multi = bool(target_item.get('is_multi_image'))
    img_list = target_item.get('image_list', [])
    img_folder, _ = QueueService.get_session_folders()
    if not img_folder:
        img_folder, _ = ConfigService.get_configured_folders()
    multi_paths = []
    if is_multi and img_list and img_folder:
        multi_paths = [os.path.join(img_folder, img) for img in img_list if os.path.exists(os.path.join(img_folder, img))]

    result = render_pipeline.render(
        item_id,
        vid_path,
        img_path,
        is_multi_image=(is_multi and len(multi_paths) >= 2),
        image_paths=multi_paths
    )

    if result.get('success'):
        target_item['status'] = 'Hoàn thành'
        target_item['is_locked'] = True
        target_item['output_file'] = result.get('output_file')
        target_item['output_folder'] = result.get('output_folder', 'outputs')
        target_item['has_lyrics'] = result.get('has_lyrics', True)
        folder = target_item['output_folder']
        video_url = f"/{folder}/{result.get('output_file')}"
        return jsonify({
            'success': True,
            'output_file': result.get('output_file'),
            'output_folder': folder,
            'has_lyrics': target_item['has_lyrics'],
            'video_url': video_url,
            'is_locked': True
        })
    else:
        target_item['status'] = 'Lỗi'
        return jsonify({
            'success': False,
            'error': result.get('error', 'Lỗi không xác định'),
            'failing_stage': result.get('failing_stage')
        }), 500


@app.route('/api/render-progress', methods=['GET'])
def get_render_progress():
    item_id = request.args.get('id', type=int)
    summary, prog = QueueService.get_progress_summary(item_id)
    return jsonify({
        'success': True,
        'queue_summary': summary,
        'progress': prog
    })


@app.route('/api/render-predictions', methods=['GET'])
def get_render_predictions():
    return jsonify(QueueService.get_render_predictions())


@app.route('/api/render-telemetry', methods=['GET'])
def get_render_telemetry():
    limit = request.args.get('limit', 10, type=int)
    profile = telemetry_manager.get_model_profile()
    all_records = telemetry_manager.load_records()
    recent = all_records[-limit:] if limit > 0 else all_records
    recent.reverse()
    return jsonify({
        'success': True,
        'model_profile': profile,
        'recent_records': recent
    })


@app.route('/api/get-videos-db', methods=['GET'])
def get_videos_db():
    db = load_video_db()
    return jsonify({'success': True, 'videos': db})


@app.route('/api/update-video-status', methods=['POST'])
def update_video_status():
    data = request.json or {}
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


@app.route('/media/image-by-name/<filename>')
def get_image_by_name(filename):
    img_folder, _ = QueueService.get_session_folders()
    if not img_folder:
        img_folder, _ = ConfigService.get_configured_folders()

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


@app.route('/outputs-no-lyrics/<path:filename>')
def get_output_no_lyrics_video(filename):
    return send_from_directory(app.config['OUTPUT_NO_LYRICS_FOLDER'], filename)


@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename, as_attachment=True)


@app.route('/download/no-lyrics/<filename>')
def download_no_lyrics_file(filename):
    return send_from_directory(app.config['OUTPUT_NO_LYRICS_FOLDER'], filename, as_attachment=True)


def open_browser():
    webbrowser.open_new('http://127.0.0.1:5000/')


if __name__ == '__main__':
    threading.Timer(1.2, open_browser).start()
    app.run(debug=False, port=5000)
