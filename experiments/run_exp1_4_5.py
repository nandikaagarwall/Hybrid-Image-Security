import os
import sys
import time
import numpy as np
import cv2
from PIL import Image
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.payload import encrypt_payload, decrypt_payload
from src.stego import embed_payload, extract_payload
from src.metrics import (
    entropy,
    hist_chi2_uniform,
    corr_all,
    npcr_uaci,
    entropy_diff,
    hist_chi2_distance,
    corr_diff,
    mse,
    psnr,
    ssim,
    ber,
    ncc,
)

EXP_DIR = "exp_tmp"
COVER_PATH = os.path.join(EXP_DIR, "exp_cover.png")
STEGO_PATH = os.path.join(EXP_DIR, "exp_stego.png")
ATTACK_JPEG_PATH = os.path.join(EXP_DIR, "exp_stego_jpeg.jpg")


def setup_environment():
    os.makedirs(EXP_DIR, exist_ok=True)
    rng = np.random.default_rng(2026)
    # Generate 512x512 textured test image
    cover = rng.integers(0, 256, (512, 512), dtype=np.uint8)
    Image.fromarray(cover).save(COVER_PATH)


def cleanup():
    for f in [COVER_PATH, STEGO_PATH, ATTACK_JPEG_PATH]:
        if os.path.exists(f):
            os.remove(f)
    if os.path.exists(EXP_DIR):
        os.rmdir(EXP_DIR)


def run_experiment_4_execution_time(message: str):
    print("\n" + "=" * 60)
    print("          EXPERIMENT 4: EXECUTION TIME BENCHMARK          ")
    print("=" * 60)

    # 1. Encryption Runtime
    t0 = time.perf_counter()
    raw_payload = encrypt_payload(message)
    t_enc = (time.perf_counter() - t0) * 1000

    # 2. Stego Embedding Runtime
    t0 = time.perf_counter()
    embed_payload(COVER_PATH, message, STEGO_PATH)
    t_embed = (time.perf_counter() - t0) * 1000

    # 3. Stego Extraction & Decryption Runtime
    t0 = time.perf_counter()
    extracted_msg = extract_payload(STEGO_PATH)
    t_extract = (time.perf_counter() - t0) * 1000

    # 4. Decryption-only Runtime
    t0 = time.perf_counter()
    decrypt_payload(raw_payload)
    t_dec = (time.perf_counter() - t0) * 1000

    print(f"  AES-RSA Encryption Time        : {t_enc:.2f} ms")
    print(f"  Steganographic Embedding Time  : {t_embed:.2f} ms")
    print(f"  Extraction & Decryption Time   : {t_extract:.2f} ms")
    print(f"  Standalone Decryption Time     : {t_dec:.2f} ms")
    print(f"  Total Pipeline Time (Embed+Ext): {(t_embed + t_extract):.2f} ms")
    
    assert message == extracted_msg, "Payload mismatch!"


def run_experiment_5_encryption_security(message: str):
    print("\n" + "=" * 60)
    print("          EXPERIMENT 5: ENCRYPTION SECURITY METRICS       ")
    print("=" * 60)

    payload1 = encrypt_payload(message)
    # Create single character difference for NPCR/UACI test
    payload2 = encrypt_payload(message[:-1] + ("!" if message[-1] != "!" else "?"))

    arr1 = np.frombuffer(payload1, dtype=np.uint8)
    arr2 = np.frombuffer(payload2[: len(payload1)], dtype=np.uint8)

    # Convert to 2D matrix for correlation testing
    side = int(np.ceil(np.sqrt(len(arr1))))
    padded = np.pad(arr1, (0, side * side - len(arr1)), mode="constant")
    img_payload = padded.reshape((side, side))

    ent_val = entropy(img_payload)
    chi2_val = hist_chi2_uniform(img_payload)
    corrs = corr_all(img_payload)
    npcr_val, uaci_val = npcr_uaci(arr1, arr2)

    print(f"  Payload Shannon Entropy        : {ent_val:.4f} bits (Ideal ~8.0)")
    print(f"  Histogram Chi-Square Flatness  : {chi2_val:.4f} (Pass < 293.25)")
    print(f"  Pixel Correlation (Horizontal) : {corrs['h']:.4f} (Ideal ~0.0)")
    print(f"  Pixel Correlation (Vertical)   : {corrs['v']:.4f} (Ideal ~0.0)")
    print(f"  Pixel Correlation (Diagonal)   : {corrs['d']:.4f} (Ideal ~0.0)")
    print(f"  NPCR (Pixel Change Rate)       : {npcr_val:.4f} % (Ideal 99.6094%)")
    print(f"  UACI (Average Intensity Diff)  : {uaci_val:.4f} % (Ideal 33.4635%)")


def run_experiment_1_concealment_and_robustness():
    print("\n" + "=" * 60)
    print("      EXPERIMENT 1: CONCEALMENT QUALITY & ROBUSTNESS       ")
    print("=" * 60)

    cover = cv2.imread(COVER_PATH, cv2.IMREAD_GRAYSCALE)
    stego = cv2.imread(STEGO_PATH, cv2.IMREAD_GRAYSCALE)

    m_mse = mse(cover, stego)
    m_psnr = psnr(cover, stego)
    m_ssim = ssim(cover, stego)
    m_ent_diff = entropy_diff(cover, stego)
    m_chi2 = hist_chi2_distance(cover, stego)
    m_corr_diff = corr_diff(cover, stego)

    print("--- 1. Concealment Quality ---")
    print(f"  MSE                            : {m_mse:.6f}")
    print(f"  PSNR                           : {m_psnr:.2f} dB")
    print(f"  SSIM                           : {m_ssim:.4f}")
    print(f"  Entropy Difference             : {m_ent_diff:.6f}")
    print(f"  Histogram Chi-Square Distance  : {m_chi2:.6f}")
    print(f"  Correlation Diff (H, V, D)    : H={m_corr_diff['h']:.4f}, V={m_corr_diff['v']:.4f}, D={m_corr_diff['d']:.4f}")

    print("\n--- 2. Hidden-Message Attack Robustness ---")
    # Apply JPEG compression Q=95 attack
    cv2.imwrite(ATTACK_JPEG_PATH, stego, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    stego_jpeg = cv2.imread(ATTACK_JPEG_PATH, cv2.IMREAD_GRAYSCALE)

    ber_val = ber(stego & 1, stego_jpeg & 1)
    ncc_val = ncc(stego, stego_jpeg)

    print(f"  JPEG (Q=95) Normalized Cross-Corr (NCC) : {ncc_val:.4f}")
    print(f"  JPEG (Q=95) Bit Error Rate (BER)       : {ber_val:.4f}")


def main():
    setup_environment()
    test_msg = "Comprehensive Benchmarking Payload for Experiments 1, 4, and 5 - Year 2026."

    run_experiment_4_execution_time(test_msg)
    run_experiment_5_encryption_security(test_msg)
    run_experiment_1_concealment_and_robustness()

    cleanup()
    print("\n[+] Experiments 1, 4, and 5 completed successfully!")


if __name__ == "__main__":
    main()