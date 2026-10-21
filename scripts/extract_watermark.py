import cv2
import numpy as np
import pywt
import os
from pyzbar.pyzbar import decode
from PIL import Image

def extract_watermark(watermarked_path, cover_path, keys_path, output_qr_path, alpha=0.05):
    """A5: Extracts the watermark using DWT-SVD and the cryptographic keys."""
    # 1. Load images and extraction keys
    watermarked = cv2.imread(watermarked_path)
    cover = cv2.imread(cover_path)
    keys = np.load(keys_path)
    U_qr, V_qr = keys['U'], keys['V']
    
    # 2. Extract Blue Channels & apply 1-Level Haar DWT
    B_wm = cv2.split(watermarked)[0]
    B_cov = cv2.split(cover)[0]
    
    LL_wm, _ = pywt.dwt2(B_wm, 'haar')
    LL_cov, _ = pywt.dwt2(B_cov, 'haar')
    
    # 3. Apply SVD to both LL subbands
    _, S_wm, _ = np.linalg.svd(LL_wm, full_matrices=False)
    _, S_cov, _ = np.linalg.svd(LL_cov, full_matrices=False)
    
    # 4. Reverse the embedding math to find the QR's singular values
    # S_embedded = S_cov + (alpha * S_qr)  =>  S_qr_extracted = (S_wm - S_cov) / alpha
    S_qr_extracted = (S_wm - S_cov) / alpha
    
    # 5. Reconstruct the scrambled QR image using the original U and V keys
    extracted_scrambled_qr = np.dot(U_qr, np.dot(np.diag(S_qr_extracted), V_qr))
    extracted_scrambled_qr = np.clip(extracted_scrambled_qr, 0, 255).astype(np.uint8)
    
    return extracted_scrambled_qr

def reverse_chaotic_scramble(scrambled_image, x0=0.12345, mu=3.9999):
    """Reverses the Chaotic Logistic Map to reveal the readable QR code."""
    h, w = scrambled_image.shape
    num_pixels = h * w
    
    # Re-generate the exact same chaotic sequence used during embedding
    chaotic_seq = np.zeros(num_pixels)
    x = x0
    for i in range(num_pixels):
        x = mu * x * (1 - x)
        chaotic_seq[i] = x
        
    # Get the original sorting indices, then find their inverse to unscramble
    sort_indices = np.argsort(chaotic_seq)
    unscramble_indices = np.argsort(sort_indices)
    
    # Flatten, un-scramble, and reshape
    flat_scrambled = scrambled_image.flatten()
    unscrambled_flat = flat_scrambled[unscramble_indices]
    
    # Apply a sharp binary threshold to clean up any noise from the math
    unscrambled_image = unscrambled_flat.reshape((h, w))
    unscrambled_image = np.where(unscrambled_image > 128, 255, 0).astype(np.uint8)
    
    return unscrambled_image

if __name__ == "__main__":
    watermarked_img = "data/images/lena_watermarked.png"
    original_cover = "data/images/lena.png"
    keys_file = "data/images/extraction_keys.npz"
    output_qr = "data/images/extracted_qr_clean.png"
    
    # 1. Extract the scrambled image
    extracted_scrambled = extract_watermark(watermarked_img, original_cover, keys_file, output_qr, alpha=0.05)
    
    # 2. Reverse the chaotic math
    clean_qr = reverse_chaotic_scramble(extracted_scrambled, x0=0.12345, mu=3.9999)
    cv2.imwrite(output_qr, clean_qr)
    print("[✓] Watermark extracted and unscrambled successfully.")
    
    # 3. Decode the QR code to prove it works
    decoded_data = decode(Image.open(output_qr))
    if decoded_data:
        print(f"[★] SUCCESS! Decoded Payload: {decoded_data[0].data.decode('utf-8')}")
    else:
        print("[✗] Failed to decode QR code. Image might be too noisy.")