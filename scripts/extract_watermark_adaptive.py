import cv2
import numpy as np
import pywt
import os
from pyzbar.pyzbar import decode
from PIL import Image

def extract_watermark_adaptive(watermarked_path, cover_path, keys_path, output_qr_path, block_size=8):
    """Extracts the watermark from a texture-adaptive block-based DWT-SVD watermarked image."""
    watermarked = cv2.imread(watermarked_path)
    cover = cv2.imread(cover_path)
    
    keys = np.load(keys_path)
    keys_U = keys['U']
    keys_S = keys['S']
    keys_V = keys['V']
    keys_alpha = keys['alpha']
    
    B_wm = cv2.split(watermarked)[0]
    B_cov = cv2.split(cover)[0]
    
    LL_wm, _ = pywt.dwt2(B_wm, 'haar')
    LL_cov, _ = pywt.dwt2(B_cov, 'haar')
    
    h, w = LL_wm.shape
    extracted_qr = np.zeros((h, w))
    
    # Block-based SVD extraction
    for i in range(0, h, block_size):
        for j in range(0, w, block_size):
            idx_i, idx_j = i // block_size, j // block_size
            
            block_wm = LL_wm[i:i+block_size, j:j+block_size]
            block_cov = LL_cov[i:i+block_size, j:j+block_size]
            
            _, S_w, _ = np.linalg.svd(block_wm, full_matrices=False)
            _, S_c, _ = np.linalg.svd(block_cov, full_matrices=False)
            
            alpha = keys_alpha[idx_i, idx_j]
            U_q = keys_U[idx_i, idx_j]
            V_q = keys_V[idx_i, idx_j]
            
            # Reverse block embedding math: S_qr = (S_wm - S_cov) / alpha
            S_qr_extracted = (S_w - S_c) / alpha
            
            block_qr = np.dot(U_q, np.dot(np.diag(S_qr_extracted), V_q))
            extracted_qr[i:i+block_size, j:j+block_size] = block_qr
            
    extracted_qr = np.clip(extracted_qr, 0, 255).astype(np.uint8)
    return extracted_qr

if __name__ == "__main__":
    watermarked_img = "data/images/lena_watermarked_adaptive.png"
    original_cover = "data/images/lena.png"
    keys_file = "data/images/extraction_keys_adaptive.npz"
    output_qr = "data/images/extracted_qr_adaptive_clean.png"
    
    # 1. Extract the scrambled block QR image
    extracted_scrambled = extract_watermark_adaptive(watermarked_img, original_cover, keys_file, output_qr)
    
    # 2. Reverse the chaotic map
    from extract_watermark import reverse_chaotic_scramble
    unscrambled_qr = reverse_chaotic_scramble(extracted_scrambled, x0=0.12345, mu=3.9999)
    
    # 3. Clean up edge speckle noise using median blur and binary thresholding
    cleaned_qr = cv2.medianBlur(unscrambled_qr, 3)
    _, cleaned_qr = cv2.threshold(cleaned_qr, 127, 255, cv2.THRESH_BINARY)
    
    cv2.imwrite(output_qr, cleaned_qr)
    
    print("[✓] Adaptive watermark extracted and unscrambled successfully.")
    
    # 4. Decode payload
    decoded_data = decode(Image.open(output_qr))
    if decoded_data:
        print(f"[★] SUCCESS! Decoded Adaptive Payload: {decoded_data[0].data.decode('utf-8')}")
    else:
        print("[✗] Failed to decode adaptive QR code.")