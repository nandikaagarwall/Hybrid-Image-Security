import os
import cv2
import numpy as np
import pywt
from PIL import Image
from pyzbar.pyzbar import decode
from skimage.metrics import structural_similarity as ssim

# Import your attacks
from attacks import apply_noise, apply_jpeg, apply_blur, apply_geometric

# ==========================================
# METRICS FUNCTIONS
# ==========================================
def calculate_psnr(img1, img2):
    mse = np.mean((img1.astype(np.float64) - img2.astype(np.float64)) ** 2)
    if mse == 0:
        return 100.0
    return 20 * np.log10(255.0 / np.sqrt(mse))

def calculate_ssim(img1, img2):
    # Channel-wise SSIM for color images
    return ssim(img1, img2, channel_axis=2, data_range=255)

def calculate_ncc(orig, extr):
    orig = orig.astype(np.float64)
    extr = extr.astype(np.float64)
    numerator = np.sum(orig * extr)
    denominator = np.sqrt(np.sum(orig ** 2) * np.sum(extr ** 2))
    if denominator == 0:
        return 0.0
    return numerator / denominator

def calculate_ber(orig_qr, extr_qr):
    # Binary bit error rate on the un-scrambled binary QR
    b_orig = (orig_qr > 128).astype(np.uint8)
    b_extr = (extr_qr > 128).astype(np.uint8)
    errors = np.sum(b_orig != b_extr)
    total_bits = b_orig.size
    return errors / total_bits

# ==========================================
# EXTRACTION LOGIC FOR BENCHMARKING
# ==========================================
def reverse_chaotic_scramble(scrambled_image, x0=0.12345, mu=3.9999):
    h, w = scrambled_image.shape
    num_pixels = h * w
    chaotic_seq = np.zeros(num_pixels)
    x = x0
    for i in range(num_pixels):
        x = mu * x * (1 - x)
        chaotic_seq[i] = x
        
    sort_indices = np.argsort(chaotic_seq)
    unscramble_indices = np.argsort(sort_indices)
    flat_scrambled = scrambled_image.flatten()
    unscrambled = flat_scrambled[unscramble_indices].reshape((h, w))
    return np.where(unscrambled > 128, 255, 0).astype(np.uint8)

def extract_config_a(attacked_img, cover_img, keys_path, alpha=0.05):
    keys = np.load(keys_path)
    U_qr, V_qr = keys['U'], keys['V']
    
    B_atk = cv2.split(attacked_img)[0]
    B_cov = cv2.split(cover_img)[0]
    
    LL_atk, _ = pywt.dwt2(B_atk, 'haar')
    LL_cov, _ = pywt.dwt2(B_cov, 'haar')
    
    _, S_atk, _ = np.linalg.svd(LL_atk, full_matrices=False)
    _, S_cov, _ = np.linalg.svd(LL_cov, full_matrices=False)
    
    S_extracted = (S_atk - S_cov) / alpha
    scrambled_qr = np.dot(U_qr, np.dot(np.diag(S_extracted), V_qr))
    return np.clip(scrambled_qr, 0, 255).astype(np.uint8)

def extract_config_b(attacked_img, cover_img, keys_path, block_size=8):
    keys = np.load(keys_path)
    keys_U = keys['U']
    keys_V = keys['V']
    keys_alpha = keys['alpha']
    
    B_atk = cv2.split(attacked_img)[0]
    B_cov = cv2.split(cover_img)[0]
    
    LL_atk, _ = pywt.dwt2(B_atk, 'haar')
    LL_cov, _ = pywt.dwt2(B_cov, 'haar')
    
    h, w = LL_atk.shape
    scrambled_qr = np.zeros((h, w))
    
    for i in range(0, h, block_size):
        for j in range(0, w, block_size):
            idx_i, idx_j = i // block_size, j // block_size
            block_atk = LL_atk[i:i+block_size, j:j+block_size]
            block_cov = LL_cov[i:i+block_size, j:j+block_size]
            
            _, S_w, _ = np.linalg.svd(block_atk, full_matrices=False)
            _, S_c, _ = np.linalg.svd(block_cov, full_matrices=False)
            
            alpha = keys_alpha[idx_i, idx_j]
            U_q = keys_U[idx_i, idx_j]
            V_q = keys_V[idx_i, idx_j]
            
            S_qr_extracted = (S_w - S_c) / alpha
            block_qr = np.dot(U_q, np.dot(np.diag(S_qr_extracted), V_q))
            scrambled_qr[i:i+block_size, j:j+block_size] = block_qr
            
    return np.clip(scrambled_qr, 0, 255).astype(np.uint8)

def test_qr_decodability(qr_img):
    # Try direct decode
    decoded = decode(qr_img)
    if decoded:
        return True
    # Try Otsu threshold
    blurred = cv2.GaussianBlur(qr_img, (3, 3), 0)
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    decoded = decode(thresh)
    return True if decoded else False

# ==========================================
# MAIN EXPERIMENT RUNNER
# ==========================================
if __name__ == "__main__":
    cover = cv2.imread("data/images/lena.png")
    wm_a = cv2.imread("data/images/lena_watermarked.png")
    wm_b = cv2.imread("data/images/lena_watermarked_adaptive.png")
    orig_qr = cv2.imread("data/images/original_qr.png", cv2.IMREAD_GRAYSCALE)
    scrambled_ref = cv2.imread("data/images/scrambled_qr.png", cv2.IMREAD_GRAYSCALE)
    
    keys_a = "data/images/extraction_keys.npz"
    keys_b = "data/images/extraction_keys_adaptive.npz"

    # Standard attack suite from the project scope
    attacks = {
        "No Attack": lambda img: img.copy(),
        "JPEG (Q=90)": lambda img: apply_jpeg(img, quality=90),
        "JPEG (Q=70)": lambda img: apply_jpeg(img, quality=70),
        "JPEG (Q=50)": lambda img: apply_jpeg(img, quality=50),
        "Gaussian Noise (v=0.001)": lambda img: apply_noise(img, "gaussian", 0.001),
        "Gaussian Noise (v=0.01)": lambda img: apply_noise(img, "gaussian", 0.01),
        "Salt & Pepper (d=0.01)": lambda img: apply_noise(img, "sp", 0.01),
        "Average Blur (3x3)": lambda img: apply_blur(img, kernel_size=3),
        "Cropping (25%)": lambda img: apply_geometric(img, "cropping"),
        "Scaling (0.5x -> 1x)": lambda img: apply_geometric(img, "scaling"),
    }

    print(f"{'Attack':<26} | {'Config':<8} | {'PSNR':<7} | {'SSIM':<7} | {'NCC':<7} | {'BER':<7} | {'Decodes?'}")
    print("-" * 80)

    for attack_name, attack_fn in attacks.items():
        for config_name, wm_img, extract_fn, key_file in [
            ("Config A", wm_a, extract_config_a, keys_a),
            ("Config B", wm_b, extract_config_b, keys_b)
        ]:
            # 1. Apply Attack
            attacked = attack_fn(wm_img)
            
            # 2. Image Fidelity vs Clean Cover
            psnr = calculate_psnr(cover, attacked)
            ssim_val = calculate_ssim(cover, attacked)
            
            # 3. Extract scrambled watermark
            extr_scrambled = extract_fn(attacked, cover, key_file)
            
            # 4. Measure scrambled NCC
            scrambled_ref_resized = cv2.resize(scrambled_ref, (extr_scrambled.shape[1], extr_scrambled.shape[0]))
            ncc = calculate_ncc(scrambled_ref_resized, extr_scrambled)
            
            # 5. Unscramble & Measure BER + Decodability
            clean_qr = reverse_chaotic_scramble(extr_scrambled)
            orig_qr_resized = cv2.resize(orig_qr, (clean_qr.shape[1], clean_qr.shape[0]))
            ber = calculate_ber(orig_qr_resized, clean_qr)
            can_decode = test_qr_decodability(clean_qr)
            
            decode_str = "[PASS]" if can_decode else "[FAIL]"
            print(f"{attack_name:<26} | {config_name:<8} | {psnr:<7.2f} | {ssim_val:<7.4f} | {ncc:<7.4f} | {ber:<7.4f} | {decode_str}")
        print("-" * 80)