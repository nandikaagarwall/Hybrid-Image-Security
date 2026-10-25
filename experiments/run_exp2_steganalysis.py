import os
import sys
import numpy as np
import cv2
from PIL import Image
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.stego import embed_payload
from src.metrics import detection_error

EXP_DIR = "exp_tmp_steganalysis"


def extract_spam_features(img: np.ndarray, T: int = 3) -> np.ndarray:
    """Calculates 2nd-order Subtractive Pixel Adjacency Matrix (SPAM) features."""
    img = img.astype(np.int32)
    diff_h = np.clip(img[:, :-1] - img[:, 1:], -T, T)
    bins = np.arange(-T, T + 2)
    hist_2d, _, _ = np.histogram2d(
        diff_h[:, :-1].ravel(), diff_h[:, 1:].ravel(), bins=[bins, bins]
    )
    feats = hist_2d.ravel()
    sum_feats = np.sum(feats)
    if sum_feats > 0:
        feats = feats / sum_feats
    return feats


def run_experiment_2(num_samples: int = 40):
    print("=" * 65)
    print("         EXPERIMENT 2: STEGANALYSIS & SPAM DETECTION (P_E)      ")
    print("=" * 65)
    print(f"[*] Generating dataset of {num_samples} cover/stego image pairs...")

    os.makedirs(EXP_DIR, exist_ok=True)

    X = []
    y = []
    rng = np.random.default_rng(100)

    for i in range(num_samples):
        cover_path = os.path.join(EXP_DIR, f"cover_{i}.png")
        stego_path = os.path.join(EXP_DIR, f"stego_{i}.png")

        arr = rng.integers(0, 256, (256, 256), dtype=np.uint8)
        Image.fromarray(arr).save(cover_path)

        embed_payload(cover_path, "Secret Stego Data " * 15, stego_path)

        cover_img = cv2.imread(cover_path, cv2.IMREAD_GRAYSCALE)
        stego_img = cv2.imread(stego_path, cv2.IMREAD_GRAYSCALE)

        f_cover = extract_spam_features(cover_img)
        f_stego = extract_spam_features(stego_img)

        X.append(f_cover)
        y.append(0)

        X.append(f_stego)
        y.append(1)

        os.remove(cover_path)
        os.remove(stego_path)

    if os.path.exists(EXP_DIR):
        os.rmdir(EXP_DIR)

    X = np.array(X)
    y = np.array(y)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.4, random_state=42, stratify=y
    )

    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)

    scores = clf.predict_proba(X_test)[:, 1]
    p_e = detection_error(y_test, scores)

    print(f"[+] Total Dataset Size : {len(y)} samples ({num_samples} cover, {num_samples} stego)")
    print(f"[+] SPAM Feature Dim   : {X.shape[1]} features")
    print(f"[+] Detection Error P_E: {p_e:.4f}")
    print("    (P_E ~ 0.