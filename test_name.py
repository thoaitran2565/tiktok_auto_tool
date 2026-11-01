from transformers import VisionEncoderDecoderModel, ViTImageProcessor, AutoTokenizer
import torch
from PIL import Image

# Load mô hình ViT-GPT2 chuyên caption hình ảnh
model = VisionEncoderDecoderModel.from_pretrained("nlpconnect/vit-gpt2-image-captioning")
feature_extractor = ViTImageProcessor.from_pretrained("nlpconnect/vit-gpt2-image-captioning")
tokenizer = AutoTokenizer.from_pretrained("nlpconnect/vit-gpt2-image-captioning")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

# Mở một khung hình (frame) cắt ra từ video bằng OpenCV
image = Image.open("D:\\Ảnh\\Ảnh đã tải\\865727137_122154521373353606_3529035341125491379_n.jpg").convert("RGB")
pixel_values = feature_extractor(images=[image], return_tensors="pt").pixel_values.to(device)

# Sinh caption
output_ids = model.generate(pixel_values, max_length=16, num_beams=4)
caption = tokenizer.decode(output_ids[0], skip_special_tokens=True)

print("AI nhận diện được:", caption)