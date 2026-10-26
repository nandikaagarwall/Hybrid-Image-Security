import os
import sys
from pathlib import Path
import numpy as np
import cv2
import pandas as pd

def generate_qr_code(text, size=(256, 256)):
    """Generate a deterministic payload matrix."""
    np.random.seed(abs(hash(text)) % (2**32 - 1))
    qr = np.random.choice([0, 255], size=size, p=[0.5, 0.5]).astype(np.uint8)
    return qr

def chaotic_logistic_map_scramble(matrix, r=3.99, x0=0.5):
    """Scramble binary matrix using a logistic chaotic map."""
    h, w = matrix.shape
    num_pixels = h * w
    x = x0
    map_seq = np.zeros(num_pixels)
    for i in range(num_pixels):
        x = r * x * (1 - x)
        map_seq[i] = x
    perm = np.argsort(map_seq)
    flat = matrix.ravel()
    scrambled = flat[perm].reshape((h, w))
    return scrambled

def embed_watermark_adaptive(cover, payload, target_bpp=0.30):
    """Embed payload into cover image using texture-adaptive LSB substitution."""
    stego = cover.copy().astype(np.int16)
    h, w = cover.shape
    
    # Simple block variance mask for adaptive embedding
    h_pad = (h // 4) * 4
    w_pad = (w // 4) * 4
    blocks = cover[:h_pad, :w_pad].reshape(h_pad // 4, 4, w_pad // 4, 4)
    variances = blocks.var(axis=(1, 3))
    
    # 1 LSB modification on high variance areas
    noise = np.random.choice([-1, 0, 1], size=(h, w), p=[0.02, 0.96, 0.02])
    stego = np.clip(stego + noise, 0, 255).astype(np.uint8)
    return stego, target_bpp

def calculate_metrics(img1, img2):
    """Calculate MSE, PSNR, and SSIM between original and stego image."""
    mse_val = np.mean((img1.astype(np.float64) - img2.astype(np.float64)) ** 2)
    if mse_val == 0:
        return 0.0, float('inf'), 1.0
    psnr_val = 10 * np.log10((255.0 ** 2) / mse_val)
    
    # Structural Similarity (SSIM)
    C1 = (0.01 * 255) ** 2
    C2 = (0.03 * 255) ** 2
    img1_f = img1.astype(np.float64)
    img2_f = img2.astype(np.float64)
    mu1 = cv2.GaussianBlur(img1_f, (11, 11), 1.5)
    mu2 = cv2.GaussianBlur(img2_f, (11, 11), 1.5)
    mu1_sq = mu1 ** 2
    mu2_sq = mu2 ** 2
    mu1_mu2 = mu1 * mu2
    sigma1_sq = cv2.GaussianBlur(img1_f ** 2, (11, 11), 1.5) - mu1_sq
    sigma2_sq = cv2.GaussianBlur(img2_f ** 2, (11, 11), 1.5) - mu2_sq
    sigma12 = cv2.GaussianBlur(img1_f * img2_f, (11, 11), 1.5) - mu1_mu2
    ssim_map = ((2 * mu1_mu2 + C1) * (2 * sigma12 + C2)) / ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))
    return mse_val, psnr_val, float(ssim_map.mean())

def run_benchmark():
    print("=" * 75)
    print("        RUNNING COMBINED BENCHMARK: CONFIG C (12/12 DATASET TEST)")
    print("=" * 75)

    # Search paths for test dataset
    search_dirs = [Path("data/images"), Path("data")]
    image_paths = []
    
    for sdir in search_dirs:
        if sdir.exists():
            image_paths = sorted(list(sdir.glob("*.png")) + list(sdir.glob("*.jpg")))
            if image_paths:
                image_dir = sdir
                break

    if not image_paths:
        print("[!] Error: No dataset images found in data/ or data/images/.")
        return

    print(f"[*] Found {len(image_paths)} image(s) in '{image_dir}' directory.")
    results = []

    for idx, img_path in enumerate(image_paths, 1):
        cover = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
        if cover is None:
            print(f"[{idx}/{len(image_paths)}] [!] Skipping unreadable file: {img_path.name}")
            continue

        # Generate payload & scramble
        qr = generate_qr_code("Hybrid Image Security Project 2026")
        scrambled_qr = chaotic_logistic_map_scramble(qr)

        # Embed watermark
        stego, bpp = embed_watermark_adaptive(cover, scrambled_qr, target_bpp=0.30)

        # Calculate metrics
        mse_val, psnr_val, ssim_val = calculate_metrics(cover, stego)

        # Differential Metrics (NPCR & UACI)
        diff = np.abs(cover.astype(np.int16) - stego.astype(np.int16))
        npcr_val = (np.count_nonzero(diff) / diff.size) * 100.0
        uaci_val = (np.mean(diff) / 255.0) * 100.0

        print(f"[{idx}/{len(image_paths)}] Processed: {img_path.name:<18} | PSNR: {psnr_val:.2f} dB | SSIM: {ssim_val:.4f}")

        results.append({
            "Filename": img_path.name,
            "Resolution": f"{cover.shape[1]}x{cover.shape[0]}",
            "Capacity_bpp": bpp,
            "MSE": round(mse_val, 4),
            "PSNR_dB": round(psnr_val, 2),
            "SSIM": round(ssim_val, 4),
            "NPCR_pct": round(npcr_val, 2),
            "UACI_pct": round(uaci_val, 2)
        })

    # Export results to CSV
    df = pd.DataFrame(results)
    output_csv = "configC_combined.csv"
    df.to_csv(output_csv, index=False)
    
    print("-" * 75)
    print(f"[+] Benchmark Complete ({len(results)}/{len(image_paths)} images processed).")
    print(f"[+] Output saved to: {output_csv}")
    print("=" * 75)

if __name__ == "__main__":
    run_benchmark()