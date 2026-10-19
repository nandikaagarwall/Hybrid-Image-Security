"""Run this after installing. Every line must say PASS before you split up."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np

ok = True
def check(name, cond, detail=""):
    global ok
    ok &= bool(cond)
    print(f"[{'PASS' if cond else 'FAIL'}] {name} {detail}")

# 1. imports
try:
    import cv2, pywt, skimage, scipy, sklearn, Crypto, qrcode, matplotlib
    check("core libraries import", True)
except Exception as e:
    check("core libraries import", False, repr(e))

import cv2

def decode_qr(img):
    detector = cv2.QRCodeDetector()
    data, bbox, _ = detector.detectAndDecode(img)
    return data
from src import config as C, metrics as M
from skimage import data

rng = np.random.default_rng(C.SEED)
nat = data.camera()                                    # natural grayscale test image
noise = rng.integers(0, 256, nat.shape, dtype=np.uint8)  # ideal "cipher"

# 2. metric sanity checks against known values
check("PSNR identical = inf", M.psnr(nat, nat) == float("inf"))
check("SSIM identical = 1", abs(M.ssim(nat, nat) - 1) < 1e-9)
check("NCC identical = 1", abs(M.ncc(nat, nat) - 1) < 1e-9)
check("entropy(random) ~ 8", 7.99 < M.entropy(noise) <= 8, f"({M.entropy(noise):.4f})")
check("entropy(natural) < 7.9", M.entropy(nat) < 7.9, f"({M.entropy(nat):.4f})")
check("corr(natural, h) > 0.85", M.corr_coeff(nat, "h") > 0.85, f"({M.corr_coeff(nat,'h'):.4f})")
check("|corr(random, h)| < 0.05", abs(M.corr_coeff(noise, "h")) < 0.05, f"({M.corr_coeff(noise,'h'):.4f})")
check("chi2(random) < 293.25", M.hist_chi2_uniform(noise) < 293.25, f"({M.hist_chi2_uniform(noise):.1f})")
n2 = rng.integers(0, 256, nat.shape, dtype=np.uint8)
npcr, uaci = M.npcr_uaci(noise, n2)
check("NPCR(two randoms) ~ 99.61", abs(npcr - 99.61) < 0.1, f"({npcr:.4f})")
check("UACI(two randoms) ~ 33.46", abs(uaci - 33.46) < 0.2, f"({uaci:.4f})")
b = rng.integers(0, 2, 1000)
check("BER identical = 0", M.ber(b, b) == 0)
check("BER inverted = 1", M.ber(b, 1 - b) == 1)
y = np.r_[np.zeros(500), np.ones(500)]
check("P_E perfect detector = 0", M.detection_error(y, y) == 0)
check("P_E random detector ~ 0.5", M.detection_error(y, rng.random(1000)) > 0.4)

# 3. QR round trip
try:
    import qrcode
    q = qrcode.QRCode(border=4, box_size=1); q.add_data(C.OWNER_TEXT); q.make(fit=True)
    qr = np.array(q.make_image().convert("L"))
    import cv2
    qr = cv2.resize(qr, (C.QR_SIZE, C.QR_SIZE), interpolation=cv2.INTER_NEAREST)
    check("QR 256x256 generated and decodes", M.qr_decodes(qr, C.OWNER_TEXT), f"(QR version {q.version})")
except Exception as e:
    check("QR round trip", False, repr(e))

# 4. DWT size matches QR size (base paper design)
import pywt
LL, _ = pywt.dwt2(np.zeros((C.IMG_SIZE, C.IMG_SIZE)), C.WAVELET)
check("LL band size == QR size", LL.shape == (C.QR_SIZE, C.QR_SIZE), f"({LL.shape})")

# 5. data folders
from src import io_utils as IO
n_std = len(IO.standard_images())
check("12 standard images in data/standard", n_std == 12, f"(found {n_std})")
n_boss = len(list(C.DATA_BOSS.glob("*.pgm")))
check("BOSSbase present (Person B only, can come later)", n_boss >= C.BOSS_SUBSET, f"(found {n_boss})")
check("RSA keys present", (C.KEYS / "rsa_private.pem").exists(), "(run scripts/make_keys.py once)")

print("\nALL GOOD - you can split up." if ok else "\nFix the FAIL lines first (data/BOSSbase/keys FAILs are expected until you add them).")
