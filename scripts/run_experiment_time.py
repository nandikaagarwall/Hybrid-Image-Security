import time
import cv2
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import numpy as np
from embed_watermark import embed_watermark
from extract_watermark import extract_watermark
from embed_watermark_adaptive import embed_watermark_adaptive
from extract_watermark_adaptive import extract_watermark_adaptive

def measure_time():
    cover_path = "data/images/lena.png"
    qr_path = "data/images/scrambled_qr.png"
    
    # --- CONFIG A (Base Paper) ---
    start = time.time()
    U_a, S_a, V_a = embed_watermark(cover_path, qr_path, "data/images/temp_a.png", alpha=0.05)
    np.savez("data/images/temp_keys_a.npz", U=U_a, S=S_a, V=V_a)
    embed_time_a = time.time() - start
    
    start = time.time()
    extract_watermark("data/images/temp_a.png", cover_path, "data/images/temp_keys_a.npz", "data/images/temp_qr_a.png", alpha=0.05)
    extract_time_a = time.time() - start
    
    # --- CONFIG B (Texture-Adaptive) ---
    start = time.time()
    U_b, S_b, V_b, alpha_b = embed_watermark_adaptive(cover_path, qr_path, "data/images/temp_b.png")
    np.savez("data/images/temp_keys_b.npz", U=U_b, S=S_b, V=V_b, alpha=alpha_b)
    embed_time_b = time.time() - start
    
    start = time.time()
    extract_watermark_adaptive("data/images/temp_b.png", cover_path, "data/images/temp_keys_b.npz", "data/images/temp_qr_b.png")
    extract_time_b = time.time() - start
    
    print(f"{'Configuration':<15} | {'Embedding Time (s)':<20} | {'Extraction Time (s)'}")
    print("-" * 60)
    print(f"{'Config A':<15} | {embed_time_a:<20.4f} | {extract_time_a:.4f}")
    print(f"{'Config B':<15} | {embed_time_b:<20.4f} | {extract_time_b:.4f}")

if __name__ == "__main__":
    measure_time()