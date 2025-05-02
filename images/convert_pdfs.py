import os
from pdf2image import convert_from_path

# Set your DPI and output folder
DPI = 300
output_dir = "jpg_output"
os.makedirs(output_dir, exist_ok=True)

# Loop over all PDFs in the current directory
for filename in os.listdir("."):
    if filename.endswith(".pdf"):
        base_name = os.path.splitext(filename)[0]
        print(f"Converting {filename}...")
        images = convert_from_path(filename, dpi=DPI)
        for i, img in enumerate(images):
            out_path = os.path.join(output_dir, f"{base_name}_page{i+1}.jpg")
            img.save(out_path, "JPEG")
        print(f"✅ Saved {len(images)} page(s) from {filename}")

