import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
from app import app

client = app.test_client()

print("--- Testing GET /test ---")
res = client.get('/test')
print(f"Status: {res.status_code}")
assert res.status_code == 200, f"Expected 200, got {res.status_code}"
assert b"Test Lyrics" in res.data
print("GET /test PASSED!")

print("--- Testing POST /api/test-scan-videos ---")
# Check config or scan folder with actual videos
scan_res = client.post('/api/test-scan-videos', json={'video_folder': 'outputs-no-lyrics'})
print(f"Status: {scan_res.status_code}")
data = json.loads(scan_res.data)
print(f"Success: {data.get('success')}, Total videos: {data.get('total_videos')}")
assert scan_res.status_code == 200
assert data.get('success') is True
assert data.get('total_videos') > 0
print(f"Scanned {data.get('total_videos')} videos successfully!")
print("POST /api/test-scan-videos PASSED!")

first_video = data['queue'][0]
print(f"--- Testing POST /api/test-lyrics on: {first_video['video_name']} ---")
outputs_before = set(os.listdir('outputs')) if os.path.exists('outputs') else set()

test_lyric_res = client.post('/api/test-lyrics', json={
    'id': first_video['id'],
    'video_path': first_video['video_path']
})
print(f"Status: {test_lyric_res.status_code}")
lyric_data = json.loads(test_lyric_res.data)
print(f"Success: {lyric_data.get('success')}")
print(f"Lyric source: {lyric_data.get('lyric_source')}")
print(f"First line: {lyric_data.get('first_line')}")
print(f"Duration: {lyric_data.get('duration_s')}s, Processing time: {lyric_data.get('processing_time_s')}s")
assert test_lyric_res.status_code == 200
assert lyric_data.get('success') is True

outputs_after = set(os.listdir('outputs')) if os.path.exists('outputs') else set()
new_files = outputs_after - outputs_before
# Verify 0 new MP4 files created in outputs
new_mp4s = [f for f in new_files if f.endswith('.mp4')]
assert len(new_mp4s) == 0, f"Expected 0 new MP4 files, found: {new_mp4s}"
# Verify no temp audio files remain
temp_audios = [f for f in os.listdir('outputs') if f.startswith('temp_test_audio_')]
assert len(temp_audios) == 0, f"Found lingering temp audio: {temp_audios}"
print("Zero video rendering & scratch audio cleanup PASSED!")

print("--- Testing POST /api/test-lyrics with invalid path ---")
err_res = client.post('/api/test-lyrics', json={'video_path': 'non_existent.mp4'})
print(f"Status: {err_res.status_code}")
err_data = json.loads(err_res.data)
assert err_res.status_code == 404
assert err_data.get('success') is False
print("POST /api/test-lyrics error handling PASSED!")

print("ALL TEST SCENARIOS PASSED!")
