import numpy as np
import qrcode
from PIL import Image
import cv2


def generate_qr_code(payload_text="Author: YourName, Country: YourCountry", size=(256, 256)):
    """A1: Generates a binary QR code from text."""
    qr = qrcode.QRCode(version=1, box_size=10, border=1)
    qr.add_data(payload_text)
    qr.make(fit=True)
    
    # Create image and resize to target dimension (e.g., 256x256)
    img_qr = qr.make_image(fill_color="black", back_color="white").convert('L')
    img_qr = img_qr.resize(size, Image.Resampling.NEAREST)
    
    # Convert to binary numpy array (0 and 255)
    qr_array = np.array(img_qr)
    qr_array = np.where(qr_array > 128, 255, 0).astype(np.uint8)
    return qr_array

def chaotic_logistic_map_scramble(image_array, x0=0.5, mu=3.999):
    """A3: Scrambles the QR code using a Chaotic Logistic Map."""
    h, w = image_array.shape
    num_pixels = h * w
    
    # Generate the chaotic sequence
    chaotic_seq = np.zeros(num_pixels)
    x = x0
    for i in range(num_pixels):
        x = mu * x * (1 - x)
        chaotic_seq[i] = x
        
    # Get sorting indices to create a permutation map
    sort_indices = np.argsort(chaotic_seq)
    
    # Flatten the image, apply permutation, and reshape back
    flat_image = image_array.flatten()
    scrambled_flat = flat_image[sort_indices]
    scrambled_image = scrambled_flat.reshape((h, w))
    
    return scrambled_image, sort_indices

if __name__ == "__main__":
    # 1. Generate the original QR Code
    qr_code = generate_qr_code("Author: Pranav, Country: India")
    cv2.imwrite("data/images/original_qr.png", qr_code)
    print("[✓] Original QR Code generated and saved.")

    # 2. Scramble it using CLM
    # Note: In your actual project, x0 and mu should come from config.py
    scrambled_qr, key_indices = chaotic_logistic_map_scramble(qr_code, x0=0.12345, mu=3.9999)
    cv2.imwrite("data/images/scrambled_qr.png", scrambled_qr)
    print("[✓] Scrambled QR Code generated and saved.")