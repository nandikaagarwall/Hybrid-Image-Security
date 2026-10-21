import cv2
from pyzbar.pyzbar import decode
from PIL import Image

# Load your extracted adaptive QR
qr_path = "data/images/extracted_qr_adaptive_clean.png"
img = cv2.imread(qr_path, cv2.IMREAD_GRAYSCALE)

# Apply a gentle blur to smooth out the isolated black speckles
blurred = cv2.GaussianBlur(img, (3, 3), 0)

# Use Otsu's automatic thresholding
_, thresh_otsu = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

# Alternatively, try adaptive thresholding
thresh_adaptive = cv2.adaptiveThreshold(
    blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
    cv2.THRESH_BINARY, 11, 2
)

# Test decoding both
decoded_otsu = decode(thresh_otsu)
decoded_adaptive = decode(thresh_adaptive)

if decoded_otsu:
    print(f"[★] SUCCESS with Otsu Thresholding! Payload: {decoded_otsu[0].data.decode('utf-8')}")
    cv2.imwrite("data/images/extracted_qr_adaptive_fixed.png", thresh_otsu)
elif decoded_adaptive:
    print(f"[★] SUCCESS with Adaptive Thresholding! Payload: {decoded_adaptive[0].data.decode('utf-8')}")
    cv2.imwrite("data/images/extracted_qr_adaptive_fixed.png", thresh_adaptive)
else:
    print("[✗] Still unable to auto-decode. Let's inspect the contrast.")
    cv2.imwrite("data/images/extracted_qr_adaptive_fixed.png", thresh_otsu)