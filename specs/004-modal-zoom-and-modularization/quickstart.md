# Quickstart Validation Guide

**Feature**: Modal Image Wheel Zoom & Application Logic Decoupling  
**Date**: 2026-11-04  
**Branch**: `004-modal-zoom-and-modularization`  

## 1. Prerequisites
- Python 3.8+
- Active dependencies installed (`flask`, `moviepy`, `pillow`, `google-genai`)
- Existing directories configured in `config.json`

## 2. Validation Scenarios

### Scenario 1: Wheel Zoom & Pan in Modal Image Picker
1. Launch application or visit `http://127.0.0.1:5000/`.
2. Click **"Quét Thư Mục"** (or ensure queue is loaded).
3. Click on the thumbnail of any queue item in column 2 (Ảnh Ghép Mẫu) to open the curation modal.
4. Hover mouse cursor over the candidate image preview.
5. Scroll mouse wheel **up**:
   - Verify the image zooms in smoothly towards the cursor.
   - Verify the zoom pill badge displays the percentage (e.g. `140%`, `200%`).
   - Verify the background page does **not** scroll.
6. Click and drag the mouse on the enlarged image:
   - Verify the cursor changes to `grabbing` and the image pans along with the cursor.
7. Scroll mouse wheel **down**:
   - Verify the image shrinks back down to its initial fit (minimum 1.0x).
8. Double-click the image:
   - Verify the image instantly resets to 100% scale and center position.

### Scenario 2: Zoom Lifecycle Isolation
1. Zoom an image to `250%`.
2. Click a different thumbnail in the bottom carousel strip.
   - Verify the new candidate image appears at exactly 100% (reset zoom).
3. Click **"Chọn ngẫu nhiên"**:
   - Verify the chosen random image appears at 100% (reset zoom).
4. Close the modal and reopen it:
   - Verify the modal opens at 100% (clean state).

### Scenario 3: Decoupled Python Services Parity
1. Run syntax verification:
   ```powershell
   python -m py_compile services/config_service.py services/scanner_service.py services/queue_service.py app.py
   ```
2. Verify line count of `app.py`:
   - Must be less than 280 lines.
3. Test service imports in Python shell:
   ```python
   from services.config_service import ConfigService
   from services.scanner_service import ScannerService
   from services.queue_service import QueueService
   print("All services loaded cleanly!")
   ```
4. Verify HTTP endpoints `/api/load-folders`, `/api/refresh-queue`, `/api/update-queue`, `/api/random-image` return valid JSON with < 0.05s latency.

