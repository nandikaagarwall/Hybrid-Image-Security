import cv2
import numpy as np
import pywt
import os

def calculate_texture_alpha(block, alpha_min=0.01, alpha_max=0.15):
    """Calculates adaptive alpha based on spatial variance of the block."""
    var = np.var(block)
    # Normalize variance (5000 is a typical upper bound for wavelet subband variance)
    norm_var = min(var / 5000.0, 1.0)
    return alpha_min + (alpha_max - alpha_min) * norm_var

def embed_watermark_adaptive(cover_path, watermark_path, output_path, block_size=8):
    """Config B: Texture-adaptive block-based DWT-SVD embedding."""
    cover = cv2.imread(cover_path)
    qr_scrambled = cv2.imread(watermark_path, cv2.IMREAD_GRAYSCALE)
    
    B, G, R = cv2.split(cover)
    
    # 1. 1-Level Haar DWT on Blue Channel
    coeffs = pywt.dwt2(B, 'haar')
    LL, (LH, HL, HH) = coeffs
    
    qr_scrambled = cv2.resize(qr_scrambled, (LL.shape[1], LL.shape[0]))
    h, w = LL.shape
    LL_embedded = np.zeros_like(LL)
    
    # Storage for block-based keys
    grid_h, grid_w = h // block_size, w // block_size
    keys_U = np.zeros((grid_h, grid_w, block_size, block_size))
    keys_S = np.zeros((grid_h, grid_w, block_size))
    keys_V = np.zeros((grid_h, grid_w, block_size, block_size))
    keys_alpha = np.zeros((grid_h, grid_w))
    
    # 2. Block-based SVD embedding
    for i in range(0, h, block_size):
        for j in range(0, w, block_size):
            block_cov = LL[i:i+block_size, j:j+block_size]
            block_qr = qr_scrambled[i:i+block_size, j:j+block_size]
            
            # Calculate dynamic strength
            alpha = calculate_texture_alpha(block_cov)
            
            # SVD on both blocks
            U_c, S_c, V_c = np.linalg.svd(block_cov, full_matrices=False)
            U_q, S_q, V_q = np.linalg.svd(block_qr, full_matrices=False)
            
            # Embed
            S_emb = S_c + (alpha * S_q)
            block_emb = np.dot(U_c, np.dot(np.diag(S_emb), V_c))
            
            # Save back to LL
            LL_embedded[i:i+block_size, j:j+block_size] = block_emb
            
            # Store keys for this block
            idx_i, idx_j = i // block_size, j // block_size
            keys_U[idx_i, idx_j], keys_S[idx_i, idx_j], keys_V[idx_i, idx_j] = U_q, S_q, V_q
            keys_alpha[idx_i, idx_j] = alpha

    # 3. Inverse DWT
    B_embedded = pywt.idwt2((LL_embedded, (LH, HL, HH)), 'haar')
    B_embedded = np.clip(B_embedded, 0, 255).astype(np.uint8)
    
    # 4. Save Image and Keys
    watermarked_img = cv2.merge((B_embedded, G, R))
    cv2.imwrite(output_path, watermarked_img)
    
    return keys_U, keys_S, keys_V, keys_alpha

if __name__ == "__main__":
    cover_img = "data/images/lena.png"
    scrambled_qr = "data/images/scrambled_qr.png"
    output_img = "data/images/lena_watermarked_adaptive.png"
    
    U, S, V, alphas = embed_watermark_adaptive(cover_img, scrambled_qr, output_img)
    np.savez("data/images/extraction_keys_adaptive.npz", U=U, S=S, V=V, alpha=alphas)
    
    print("[✓] Texture-Adaptive Watermark embedded successfully.")
    print(f"[i] Average Alpha (Strength) used: {np.mean(alphas):.4f}")