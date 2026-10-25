import os
import sys
import numpy as np
import cv2
from PIL import Image
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.stego import embed_payload, extract_payload
from src.metrics import psnr, ssim, ber

EXP_DIR = "exp_tmp_capacity"
COVER_PATH = os.path.join(EXP_DIR, "cover.png")
STEGO_PATH = os.path.join(EXP_DIR, "stego.png")


def run_experiment_3():
    os.makedirs(EXP_DIR, exist_ok=True)
    rng = np.random.default_rng(42)

    # 512x512 Cover Image (Total pixels = 262,144)
    img_h, img_w = 512, 512
    total_pixels = img_h * img_w
    cover = rng.integers(0, 256, (img_h, img_w), dtype=np.uint8)
    Image.fromarray(cover).save(COVER_PATH)

    bpp_rates = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40]

    print("=" * 65)
    print("     EXPERIMENT 3: CAPACITY VS. QUALITY TRADE-OFF (0.05 - 0.40 bpp) ")
    print("=" * 65)
    print(f"{'Capacity (bpp)':<15} | {'Payload (bits)':<15} | {'PSNR (dB)':<12} | {'BER':<8}")
    print("-" * 65)

    for bpp in bpp_rates:
        target_bits = int(total_pixels * bpp)

        # Generate payload string of appropriate length (8 bits per char)
        chars_needed = max(1, target_bits // 8)
        message = "X" * chars_needed

        try:
            embed_payload(COVER_PATH, message, STEGO_PATH)

            cover_img = cv2.imread(COVER_PATH, cv2.IMREAD_GRAYSCALE)
            stego_img = cv2.imread(STEGO_PATH, cv2.IMREAD_GRAYSCALE)

            m_psnr = psnr(cover_img, stego_img)

            # Extract & verify zero BER under standard condition
            recovered_msg = extract_payload(STEGO_PATH)
            bit_err = 0.0 if recovered_msg == message else 1.0

            print(f"{bpp:<15.2f} | {target_bits:<15} | {m_psnr:<12.2f} | {bit_err:<8.4f}")

        except Exception as e:
            print(f"{bpp:<15.2f} | {target_bits:<15} | Error: {e}")

    print("=" * 65)

    for f in [COVER_PATH, STEGO_PATH]:
        if os.path.exists(f):
            os.remove(f)
    if os.path.exists(EXP_DIR):
        os.rmdir(EXP_DIR)


if __name__ == "__main__":
    run_experiment_3()