"""
Shared metrics. BOTH tracks import from here; do not re-implement locally.

Imperceptibility : mse, psnr, ssim
Robustness       : ncc, ber, qr_decodes
Security (enc.)  : entropy, hist_chi2_uniform, corr_coeff, npcr_uaci
Concealment      : entropy_diff, hist_chi2_distance, corr_diff
Detectability    : detection_error (P_E)
"""
import numpy as np
from skimage.metrics import structural_similarity

# ---------------- imperceptibility ----------------

def mse(a, b):
    return np.mean((a.astype(np.float64) - b.astype(np.float64)) ** 2)


def psnr(a, b, peak=255.0):
    m = mse(a, b)
    return float("inf") if m == 0 else 10 * np.log10(peak ** 2 / m)


def ssim(a, b):
    """Works for grayscale (H,W) or colour (H,W,3) uint8."""
    if a.ndim == 3:
        return structural_similarity(a, b, channel_axis=2, data_range=255)
    return structural_similarity(a, b, data_range=255)

# ---------------- robustness ----------------

def ncc(w, w_ext):
    """Normalised cross-correlation between original and extracted watermark
    (definition used by the base paper). 1.0 = perfect."""
    w = w.astype(np.float64).ravel()
    e = w_ext.astype(np.float64).ravel()
    den = np.sqrt(np.sum(w ** 2) * np.sum(e ** 2))
    return 0.0 if den == 0 else float(np.sum(w * e) / den)


def ber(bits, bits_ext):
    """Bit error rate between two 0/1 arrays of equal length. 0.0 = perfect."""
    bits = np.asarray(bits).ravel().astype(np.uint8)
    bits_ext = np.asarray(bits_ext).ravel().astype(np.uint8)
    assert bits.size == bits_ext.size, "bit arrays differ in length"
    return float(np.mean(bits != bits_ext))


import cv2

def qr_decodes(qr_img, expected_text):
    detector = cv2.QRCodeDetector()
    data, _, _ = detector.detectAndDecode(qr_img)
    return data == expected_text

# ---------------- encryption security ----------------

def entropy(img, levels=256):
    """Shannon entropy in bits. Ideal: 8 for an encrypted 8-bit image, 1 for binary."""
    p = np.bincount(img.ravel(), minlength=levels) / img.size
    p = p[p > 0]
    return float(-np.sum(p * np.log2(p)))


def hist_chi2_uniform(img, levels=256):
    """Chi-square test of histogram flatness. For 8-bit: PASS if < 293.25
    (255 degrees of freedom, alpha = 0.05)."""
    h = np.bincount(img.ravel(), minlength=levels).astype(np.float64)
    e = img.size / levels
    return float(np.sum((h - e) ** 2 / e))


def corr_coeff(img, direction="h", n=5000, seed=0):
    """Correlation of adjacent pixel pairs. direction in {'h','v','d'}.
    Natural image ~0.9+, good cipher ~0."""
    rng = np.random.default_rng(seed)
    H, W = img.shape[:2]
    dy, dx = {"h": (0, 1), "v": (1, 0), "d": (1, 1)}[direction]
    y = rng.integers(0, H - dy, n)
    x = rng.integers(0, W - dx, n)
    a = img[y, x].astype(np.float64).ravel()
    b = img[y + dy, x + dx].astype(np.float64).ravel()
    if a.std() == 0 or b.std() == 0:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def corr_all(img, n=5000, seed=0):
    return {d: corr_coeff(img, d, n, seed) for d in ("h", "v", "d")}


def npcr_uaci(c1, c2):
    """c1, c2 = ciphertexts of two plaintexts differing in ONE pixel.
    Ideal for 8-bit: NPCR 99.6094 %, UACI 33.4635 %."""
    c1 = c1.astype(np.float64)
    c2 = c2.astype(np.float64)
    npcr = float(np.mean(c1 != c2) * 100)
    uaci = float(np.mean(np.abs(c1 - c2) / 255) * 100)
    return npcr, uaci

# ---------------- concealment (cover vs final image) ----------------

def entropy_diff(cover, stego):
    return entropy(stego) - entropy(cover)


def hist_chi2_distance(cover, stego, levels=256):
    """Distance between two histograms. ~0 means the embedding is invisible
    in the histogram."""
    h1 = np.bincount(cover.ravel(), minlength=levels).astype(np.float64)
    h2 = np.bincount(stego.ravel(), minlength=levels).astype(np.float64)
    den = h1 + h2
    m = den > 0
    return float(0.5 * np.sum((h1[m] - h2[m]) ** 2 / den[m]))


def corr_diff(cover, stego, n=5000, seed=0):
    c, s = corr_all(cover, n, seed), corr_all(stego, n, seed)
    return {d: s[d] - c[d] for d in c}

# ---------------- detectability ----------------

def detection_error(y_true, scores):
    """P_E = min over thresholds of (P_FA + P_MD) / 2.
    y_true: 0 = cover, 1 = stego. scores: higher = more likely stego.
    0.5 = detector is guessing (best for you), 0.0 = perfectly detected."""
    from sklearn.metrics import roc_curve
    fpr, tpr, _ = roc_curve(y_true, scores)
    return float(np.min((fpr + (1 - tpr)) / 2))

# ---------------- reporting ----------------

def mean_std(values):
    v = np.asarray(values, dtype=np.float64)
    v = v[np.isfinite(v)]
    return f"{v.mean():.4f} ± {v.std(ddof=1) if v.size > 1 else 0:.4f}"
