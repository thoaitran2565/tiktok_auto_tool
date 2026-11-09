# Quickstart Validation Guide

**Feature**: Multi-Image Video Slideshow with Smooth Transitions  
**Date**: 2026-11-04  
**Branch**: `005-multi-image-slideshow`  

## 1. Prerequisites
- Python 3.8+ with MoviePy 2.0+ and Pillow installed.
- Sample video directory and image directory configured in `config.json`.

## 2. Validation Scenarios

### Scenario 1: Multi-Image Toggle & Stepper Controls
1. Open web application (`http://127.0.0.1:5000/`).
2. Click **"Quét Thư Mục"**.
3. In Column 2 of any queue row, click the switch **"Nhiều ảnh"**:
   - Verify the toggle flips to ON.
   - Verify the count defaults to **10 ảnh**.
   - Verify 10 distinct random images are assigned.
4. Click the `+` button twice:
   - Verify count increases to **12 ảnh**.
5. Click the `-` button three times:
   - Verify count decreases to **9 ảnh**.
6. Refresh queue via **"Làm Mới"**:
   - Verify the multi-image toggle and count remain preserved.

### Scenario 2: Multi-Image Curation Modal
1. Click on the multi-image gallery pill / button for that video.
2. Verify the modal opens displaying the ordered gallery of 9 photos with slot numbers (1 to 9).
3. Click **"Đổi ngẫu nhiên bộ ảnh"**:
   - Verify all 9 slots receive a fresh set of random images.
4. Click **"Đổi ảnh"** on slot #2:
   - Select another photo from the carousel strip and confirm.
   - Verify slot #2 updates with the chosen photo.
5. Click **"Xóa"** on slot #5:
   - Verify count updates to 8 ảnh and slot #5 is removed.
6. Click **"Xác nhận áp dụng"**:
   - Verify changes reflect back on the main queue table.

### Scenario 3: End-to-End Slideshow Video Rendering
1. Click **"Bắt Đầu Render"** (or trigger single render on the configured multi-image item).
2. Wait for rendering to complete (stage 1 through stage 6).
3. Click **"Xem video"**:
   - Verify video plays smoothly at $1080 \times 1920$ resolution.
   - Verify background transitions between images via a smooth right-to-left slide motion.
   - Verify lyrics and logo overlay remain steady, readable, and uninterrupted during transitions.
   - Verify the entire slideshow duration matches the audio track with zero abrupt stops.

