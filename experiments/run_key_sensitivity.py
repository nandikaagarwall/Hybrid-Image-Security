import os
import sys
import numpy as np
import cv2
from pathlib import Path
from Crypto.Cipher import AES

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.payload import encrypt_payload
from src.metrics import mse, psnr

EXP_DIR = "exp_tmp_sensitivity"
COVER_PATH = os.path.join(EXP_DIR, "cover.png")
DIFF_STEGO_PATH = os.path.join(EXP_DIR, "diff_cover_stego.png")
DIFF_WRONG_KEY_PATH = os.path.join(EXP_DIR, "diff_wrong_key.png")


def run_key_sensitivity_experiment():
    os.makedirs(EXP_DIR, exist_ok=True)
    
    print("=" * 65)
    print("      EXPERIMENT 6: KEY SENSITIVITY & DIFFERENCE SUBTRACTION   ")
    print("=" * 65)

    # 1. Setup a test image and random AES keys
    rng = np.random.default_rng(2026)
    cover_img = rng.integers(0, 256, (256, 256), dtype=np.uint8)
    cv2.imwrite(COVER_PATH, cover_img)

    # Define Correct Key (K1) and Slightly Modified Key (K2 - 1 bit flipped)
    key_k1 = b"12345678901234567890123456789012"  # 32-byte AES key
    key_k2 = bytearray(key_k1)
    key_k2[0] ^= 1  # Flip a single bit in the key
    key_k2 = bytes(key_k2)
    iv = b"1234567890123456"

    # 2. Encrypt cover image bytes using Key K1
    padded_len = (cover_img.size // 16 + 1) * 16
    flat_bytes = cover_img.tobytes()
    padded_bytes = flat_bytes + b"\x00" * (padded_len - len(flat_bytes))

    cipher1 = AES.new(key_k1, AES.MODE_CBC, iv)
    enc_k1 = cipher1.encrypt(padded_bytes)
    enc_img_k1 = np.frombuffer(enc_k1[:cover_img.size], dtype=np.uint8).reshape(cover_img.shape)

    # 3. Decrypt with Correct Key (K1) vs Decrypt with Wrong Key (K2)
    dec_cipher1 = AES.new(key_k1, AES.MODE_CBC, iv)
    dec_k1 = np.frombuffer(dec_cipher1.decrypt(enc_k1)[:cover_img.size], dtype=np.uint8).reshape(cover_img.shape)

    dec_cipher2 = AES.new(key_k2, AES.MODE_CBC, iv)
    dec_k2 = np.frombuffer(dec_cipher2.decrypt(enc_k1)[:cover_img.size], dtype=np.uint8).reshape(cover_img.shape)

    # 4. Perform Image Subtractions
    # Subtraction A: Decrypted (Correct Key) - Decrypted (Wrong Key)
    diff_wrong_key = cv2.absdiff(dec_k1, dec_k2)
    cv2.imwrite(DIFF_WRONG_KEY_PATH, diff_wrong_key)

    # Subtraction B: Cover Image vs Stego Image (LSB modification residual)
    stego_img = cover_img.copy()
    stego_img.flat[:1000] ^= 1  # Simulate LSB modification
    diff_stego = cv2.absdiff(cover_img, stego_img) * 255  # Scaled for visibility
    cv2.imwrite(DIFF_STEGO_PATH, diff_stego)

    # 5. Calculate Metrics
    mse_wrong_key = mse(dec_k1, dec_k2)
    psnr_wrong_key = psnr(dec_k1, dec_k2)
    diff_mean = np.mean(diff_wrong_key)

    print("--- 1. Key Sensitivity Subtraction (Key K1 vs Key K2 [1-bit flip]) ---")
    print(f"  Mean Difference Intensity   : {diff_mean:.2f} (Ideal ~127.5 for pure noise)")
    print(f"  MSE (Original vs Wrong Key): {mse_wrong_key:.4f}")
    print(f"  PSNR (Original vs Wrong Key): {psnr_wrong_key:.2f} dB (Extremely low PSNR proves complete failure to decrypt)")
    
    print("\n--- 2. Differential Visual Subtraction Saved ---")
    print(f"  Saved Wrong Key Difference Image : {DIFF_WRONG_KEY_PATH}")
    print(f"  Saved Stego Residual Image       : {DIFF_STEGO_PATH}")
    print("=" * 65)

    # Cleanup temporary output folder
    for f in [COVER_PATH, DIFF_WRONG_KEY_PATH, DIFF_STEGO_PATH]:
        if os.path.exists(f):
            os.remove(f)
    if os.path.exists(EXP_DIR):
        os.rmdir(EXP_DIR)


if __name__ == "__main__":
    run_key_sensitivity_experiment()