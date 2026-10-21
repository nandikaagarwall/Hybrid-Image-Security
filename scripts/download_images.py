import os
import urllib.request
import io
from PIL import Image

OUTPUT_DIR = os.path.join("data", "images")
os.makedirs(OUTPUT_DIR, exist_ok=True)

MISSING_URLS = {
    "monarch.png": "https://upload.wikimedia.org/wikipedia/commons/1/17/Monarch_Butterfly_Danaus_plexippus_Male_2664px.jpg",
    "einstein.png": "https://upload.wikimedia.org/wikipedia/commons/d/d3/Albert_Einstein_Head.jpg",
    "monalisa.png": "https://upload.wikimedia.org/wikipedia/commons/e/ec/Mona_Lisa%2C_by_Leonardo_da_Vinci%2C_from_C2RMF_retouched.jpg"
}

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

for filename, url in MISSING_URLS.items():
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            data = resp.read()
            img = Image.open(io.BytesIO(data)).convert('RGB')
            img = img.resize((512, 512), Image.Resampling.LANCZOS)
            img.save(os.path.join(OUTPUT_DIR, filename), format="PNG")
            print(f"[✓] {filename} fixed and saved.")
    except Exception as e:
        print(f"[✗] Failed {filename}: {e}")