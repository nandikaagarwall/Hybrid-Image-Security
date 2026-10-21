import cv2
import numpy as np
import pywt
import os

def embed_watermark(cover_path, watermark_path, output_path, alpha=0.05):
    """A4: Embeds the scrambled QR code into the Blue channel using DWT-SVD."""
    # Read cover image (BGR format) and watermark (Grayscale)
    cover = cv2.imread(cover_path)
    qr_scrambled = cv2.imread(watermark_path, cv2.IMREAD_GRAYSCALE)
    
    # 1. Extract the Blue Channel
    B, G, R = cv2.split(cover)
    
    # 2. Apply 1-Level Haar DWT to the Blue Channel
    coeffs = pywt.dwt2(B, 'haar')
    LL, (LH, HL, HH) = coeffs
    
    # 3. Apply SVD to the LL subband
    U_cov, S_cov, V_cov = np.linalg.svd(LL, full_matrices=False)
    
    # Ensure watermark matches LL subband dimensions (e.g., 256x256 for a 512x512 image)
    qr_scrambled = cv2.resize(qr_scrambled, (LL.shape[1], LL.shape[0]))
    
    # 4. Apply SVD to the Scrambled Watermark
    U_qr, S_qr, V_qr = np.linalg.svd(qr_scrambled, full_matrices=False)
    
    # 5. Embed the Singular Values
    # Equation: S_new = S_cov + alpha * S_qr
    S_embedded = S_cov + (alpha * S_qr)
    
    # 6. Reconstruct the modified LL subband
    LL_embedded = np.dot(U_cov, np.dot(np.diag(S_embedded), V_cov))
    
    # 7. Apply Inverse DWT to reconstruct the Blue Channel
    B_embedded = pywt.idwt2((LL_embedded, (LH, HL, HH)), 'haar')
    B_embedded = np.clip(B_embedded, 0, 255).astype(np.uint8)
    
    # 8. Merge channels back into a color image and save
    watermarked_img = cv2.merge((B_embedded, G, R))
    cv2.imwrite(output_path, watermarked_img)
    
    # The original SVD components of the QR code act as the secret key for extraction
    return U_qr, S_qr, V_qr

if __name__ == "__main__":
    cover_img = "data/images/lena.png"
    scrambled_qr = "data/images/scrambled_qr.png"
    output_img = "data/images/lena_watermarked.png"
    
    if not os.path.exists(cover_img) or not os.path.exists(scrambled_qr):
        print("[✗] Error: Ensure lena.png and scrambled_qr.png exist in data/images/")
    else:
        # Embed the watermark with a fixed strength (alpha)
        U_key, S_key, V_key = embed_watermark(cover_img, scrambled_qr, output_img, alpha=0.05)
        
        # Save the cryptographic extraction keys to a file
        np.savez("data/images/extraction_keys.npz", U=U_key, S=S_key, V=V_key)
        
        print("[✓] Watermark successfully embedded into Blue channel.")
        print("[✓] Watermarked image saved as lena_watermarked.png.")
        print("[✓] Extraction keys saved as extraction_keys.npz.")