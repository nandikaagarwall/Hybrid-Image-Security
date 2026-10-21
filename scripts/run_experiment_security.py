import cv2
import numpy as np

def calculate_entropy(img):
    p = np.bincount(img.ravel(), minlength=256) / img.size
    p = p[p > 0]
    return -np.sum(p * np.log2(p))

def calculate_correlation(img, direction="h", n=3000, seed=42):
    rng = np.random.default_rng(seed)
    h, w = img.shape
    dy, dx = {"h": (0, 1), "v": (1, 0), "d": (1, 1)}[direction]
    y = rng.integers(0, h - dy, n)
    x = rng.integers(0, w - dx, n)
    a = img[y, x].astype(np.float64)
    b = img[y + dy, x + dx].astype(np.float64)
    return np.corrcoef(a, b)[0, 1]

def calculate_chi2(img):
    h = np.bincount(img.ravel(), minlength=256)
    expected = img.size / 256.0
    return np.sum((h - expected) ** 2 / expected)

if __name__ == "__main__":
    plain_qr = cv2.imread("data/images/original_qr.png", cv2.IMREAD_GRAYSCALE)
    scrambled_qr = cv2.imread("data/images/scrambled_qr.png", cv2.IMREAD_GRAYSCALE)
    
    metrics = [
        ("Original QR (Plain)", plain_qr),
        ("Scrambled QR (CLM)", scrambled_qr)
    ]
    
    print(f"{'Image Type':<22} | {'Entropy':<8} | {'Chi-Square':<12} | {'Corr (H)':<9} | {'Corr (V)':<9} | {'Corr (D)'}")
    print("-" * 75)
    
    for name, img in metrics:
        ent = calculate_entropy(img)
        chi2 = calculate_chi2(img)
        corr_h = calculate_correlation(img, "h")
        corr_v = calculate_correlation(img, "v")
        corr_d = calculate_correlation(img, "d")
        print(f"{name:<22} | {ent:<8.4f} | {chi2:<12.2f} | {corr_h:<9.4f} | {corr_v:<9.4f} | {corr_d:.4f}")