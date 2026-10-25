import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import os
import cv2
import numpy as np
from PIL import Image

from src.stego import embed_payload
from src.metrics import ber, ncc, psnr
from src.payload import encrypt_payload, bytes_to_bitstream

TEST_DIR = "tests_tmp_attacks"
COVER_PATH = os.path.join(TEST_DIR, "cover.png")
STEGO_PATH = os.path.join(TEST_DIR, "stego.png")
ATTACKED_PATH = os.path.join(TEST_DIR, "attacked.jpg")


def setup_images():
    """Generates clean test cover and stego images."""
    os.makedirs(TEST_DIR, exist_ok=True)
    rng = np.random.default_rng(123)
    cover = rng.integers(0, 256, (256, 256), dtype=np.uint8)
    Image.fromarray(cover).save(COVER_PATH)

    message = "Robustness Attack Benchmarking Payload"
    embed_payload(COVER_PATH, message, STEGO_PATH)


def cleanup():
    """Removes temporary attack artifacts."""
    for f in [COVER_PATH, STEGO_PATH, ATTACKED_PATH]:
        if os.path.exists(f):
            os.remove(f)
    if os.path.exists(TEST_DIR):
        os.rmdir(TEST_DIR)


def apply_jpeg_compression(stego_path: str, quality: int = 90) -> np.ndarray:
    """Applies JPEG compression at given quality level."""
    stego = cv2.imread(stego_path, cv2.IMREAD_GRAYSCALE)
    cv2.imwrite(ATTACKED_PATH, stego, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    return cv2.imread(ATTACKED_PATH, cv2.IMREAD_GRAYSCALE)


def apply_gaussian_noise(stego_path: str, mean: float = 0, std: float = 5) -> np.ndarray:
    """Adds Gaussian noise to stego image."""
    stego = cv2.imread(stego_path, cv2.IMREAD_GRAYSCALE).astype(np.float64)
    noise = np.random.normal(mean, std, stego.shape)
    noisy_stego = np.clip(stego + noise, 0, 255).astype(np.uint8)
    return noisy_stego


def apply_gaussian_blur(stego_path: str, kernel_size: int = 3) -> np.ndarray:
    """Applies a subtle Gaussian blur filter."""
    stego = cv2.imread(stego_path, cv2.IMREAD_GRAYSCALE)
    return cv2.GaussianBlur(stego, (kernel_size, kernel_size), 0)


def run_attack_suite():
    """Executes attack pipeline and prints resilience report."""
    setup_images()
    stego_orig = cv2.imread(STEGO_PATH, cv2.IMREAD_GRAYSCALE)

    print("=" * 60)
    print("         STEGANOGRAPHY ROBUSTNESS & ATTACK BENCHMARK        ")
    print("=" * 60)
    print(f"{'Attack Type':<25} | {'PSNR (dB)':<10} | {'NCC':<8} | {'BER':<8}")
    print("-" * 60)

    # 1. Baseline (No Attack)
    psnr_val = psnr(stego_orig, stego_orig)
    ncc_val = ncc(stego_orig, stego_orig)
    print(f"{'No Attack (Baseline)':<25} | {psnr_val:<10.2f} | {ncc_val:<8.4f} | {0.0000:<8.4f}")

    # 2. JPEG Compression (Quality = 95)
    jpeg_img = apply_jpeg_compression(STEGO_PATH, quality=95)
    print(f"{'JPEG Compression (Q=95)':<25} | {psnr(stego_orig, jpeg_img):<10.2f} | {ncc(stego_orig, jpeg_img):<8.4f} | {ber(stego_orig & 1, jpeg_img & 1):<8.4f}")

    # 3. Gaussian Noise (std = 2)
    noise_img = apply_gaussian_noise(STEGO_PATH, std=2)
    print(f"{'Gaussian Noise (std=2)':<25} | {psnr(stego_orig, noise_img):<10.2f} | {ncc(stego_orig, noise_img):<8.4f} | {ber(stego_orig & 1, noise_img & 1):<8.4f}")

    # 4. Gaussian Blur (3x3 Kernel)
    blur_img = apply_gaussian_blur(STEGO_PATH, kernel_size=3)
    print(f"{'Gaussian Blur (3x3)':<25} | {psnr(stego_orig, blur_img):<10.2f} | {ncc(stego_orig, blur_img):<8.4f} | {ber(stego_orig & 1, blur_img & 1):<8.4f}")

    print("=" * 60)
    cleanup()


if __name__ == "__main__":
    run_attack_suite()