"""End-to-end pipeline used for every paper figure/table.

It only wraps the team's own code (scripts/ and src/), so every number comes
from the same embed / extract / attack functions as run_watermark.py and
run_stego_security.py. Nothing here re-implements the algorithms.

Configs
  A   base paper: global DWT-SVD, alpha = 0.05, blue channel
  A*  base paper with alpha = 0.06 (PSNR matched to B)
  B   texture-adaptive per-block alpha, blue channel
  C   A + hidden layer: AES-256-CBC / RSA-2048 payload, texture-ranked LSB, green channel
"""
import os, sys, tempfile, functools
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
os.chdir(ROOT)

import numpy as np, cv2
from Crypto.PublicKey import RSA

from watermark_prep import generate_qr_code, chaotic_logistic_map_scramble
from embed_watermark import embed_watermark
from embed_watermark_adaptive import embed_watermark_adaptive
import evaluate_watermark as EW
from evaluate_watermark import (extract_config_a, extract_config_b, calculate_psnr,
                                calculate_ssim, calculate_ncc, calculate_ber, test_qr_decodability)
from attacks import apply_noise, apply_jpeg, apply_blur, apply_geometric
from src.stego import calculate_block_variances, BLOCK_SIZE
from src.payload import encrypt_payload, decrypt_payload, bytes_to_bitstream, bitstream_to_bytes

IMAGES = ["airplane", "einstein", "girl", "house", "house2", "lake", "lena",
          "mandrill", "monalisa", "monarch", "peppers", "tree"]
LABEL = {"monarch": "boat"}            # file is mislabelled: it is the fishing-boat image
X0, MU = 0.12345, 3.9999               # same key as run_watermark.py
TEXT = "Author: Pranav, Country: India"
MESSAGE = "Confidential: project record #001. Sharing prohibited."
OUT = ROOT / "paper" / "out"; OUT.mkdir(parents=True, exist_ok=True)
FIG = ROOT / "paper" / "figures"; FIG.mkdir(parents=True, exist_ok=True)
TMP = Path(tempfile.mkdtemp())

# ---- RSA keys: private key is not in the repo, so use a fresh experiment pair ----
KEYDIR = ROOT / "paper" / "keys_experiment"; KEYDIR.mkdir(exist_ok=True)
PUB, PRIV = KEYDIR / "rsa_public.pem", KEYDIR / "rsa_private.pem"
if not PRIV.exists():
    k = RSA.generate(2048)
    PRIV.write_bytes(k.export_key()); PUB.write_bytes(k.publickey().export_key())

# ---- watermark ----
QR = generate_qr_code(TEXT)
SCR, _ = chaotic_logistic_map_scramble(QR, x0=X0, mu=MU)
cv2.imwrite(str(TMP / "scr.png"), SCR)


@functools.lru_cache(maxsize=8)
def _perm(x0, mu, n=256 * 256):
    x, seq = x0, np.empty(n)
    for i in range(n):
        x = mu * x * (1 - x); seq[i] = x
    return np.argsort(np.argsort(seq))


def descramble(img, x0=X0, mu=MU):
    """Same as evaluate_watermark.reverse_chaotic_scramble, with the permutation cached."""
    inv = _perm(x0, mu)
    return np.where(img.ravel()[inv].reshape(img.shape) > 128, 255, 0).astype(np.uint8)


def load(name):
    return cv2.imread(str(ROOT / "data" / "images" / f"{name}.png"))  # BGR


def embed(name, cfg, alpha=None):
    """Returns (marked_bgr, key_path, extract_fn, extract_kwargs)."""
    cover = str(ROOT / "data" / "images" / f"{name}.png")
    if cfg in ("A", "A*", "C") or alpha is not None:
        a = alpha if alpha is not None else (0.06 if cfg == "A*" else 0.05)
        out, kp = TMP / f"{name}_{cfg}_{a}.png", TMP / f"{name}_{cfg}_{a}.npz"
        U, S, V = embed_watermark(cover, str(TMP / "scr.png"), str(out), alpha=a)
        np.savez(kp, U=U, S=S, V=V)
        return cv2.imread(str(out)), str(kp), extract_config_a, {"alpha": a}
    out, kp = TMP / f"{name}_B.png", TMP / f"{name}_B.npz"
    U, S, V, al = embed_watermark_adaptive(cover, str(TMP / "scr.png"), str(out))
    np.savez(kp, U=U, S=S, V=V, alpha=al)
    return cv2.imread(str(out)), str(kp), extract_config_b, {}


def extract_wm(attacked, cover, key, fn, kw):
    ex = fn(attacked, cover, key, **kw)
    clean = descramble(ex)
    return dict(ncc=calculate_ncc(SCR, ex), ber=calculate_ber(QR, clean),
                decodes=bool(test_qr_decodability(clean))), ex, clean


# ---- hidden layer (same algorithm as run_stego_security.py) ----
def adaptive_positions(ch):
    pos = []
    for _, r, c in calculate_block_variances(ch):
        for dr in range(BLOCK_SIZE):
            for dc in range(BLOCK_SIZE):
                pos.append((r + dr) * ch.shape[1] + (c + dc))
    return np.array(pos)


def random_positions(ch, seed=7):
    return np.random.default_rng(seed).permutation(ch.size)


def payload_bits(n_bits=None, seed=2026):
    blob = encrypt_payload(MESSAGE, str(PUB))
    bits = np.array(bytes_to_bitstream(blob), dtype=np.uint8)
    if n_bits and n_bits > bits.size:
        pad = np.random.default_rng(seed).integers(0, 2, n_bits - bits.size, dtype=np.uint8)
        bits = np.concatenate([bits, pad])
    return bits


def lsb_embed(ch, bits, method="adaptive"):
    pos = adaptive_positions(ch) if method == "adaptive" else random_positions(ch)
    out = ch.copy().ravel(); p = pos[:len(bits)]
    out[p] = (out[p] & 0xFE) | bits
    return out.reshape(ch.shape), p


def lsb_extract(ch, n, method="adaptive"):
    pos = adaptive_positions(ch) if method == "adaptive" else random_positions(ch)
    return (ch.ravel()[pos[:n]] & 1).astype(np.uint8)


def recover_message(bits):
    try:
        return decrypt_payload(bitstream_to_bytes(list(bits)), str(PRIV))
    except Exception:
        return None


def make_C(name, bpp=0.10, method="adaptive"):
    """Config C: watermark A in blue, then encrypted payload in green LSBs (BGR index 1)."""
    wm, key, fn, kw = embed(name, "A")
    n = int(bpp * 512 * 512)
    bits = payload_bits(n)
    G, pos = lsb_embed(wm[..., 1], bits, method)
    st = wm.copy(); st[..., 1] = G
    return st, wm, key, fn, kw, bits, pos


# ---- attacks: the run_watermark.py suite + base-paper translation ----
def translate(im, px=2):
    M = np.float32([[1, 0, px], [0, 1, px]])
    return cv2.warpAffine(im, M, (im.shape[1], im.shape[0]))


ATTACKS = {
    "No attack": lambda im: im.copy(),
    "JPEG Q=90": lambda im: apply_jpeg(im, 90),
    "JPEG Q=70": lambda im: apply_jpeg(im, 70),
    "JPEG Q=50": lambda im: apply_jpeg(im, 50),
    "Gaussian v=0.001": lambda im: apply_noise(im, "gaussian", 0.001),
    "Gaussian v=0.01": lambda im: apply_noise(im, "gaussian", 0.01),
    "Salt&Pepper d=0.01": lambda im: apply_noise(im, "sp", 0.01),
    "Avg blur 3x3": lambda im: apply_blur(im, 3),
    "Centre blank 6.25%": lambda im: apply_geometric(im, "cropping"),
    "Scaling 0.5x->1x": lambda im: apply_geometric(im, "scaling"),
    "Rotation 2 deg": lambda im: apply_geometric(im, "rotation"),
    "Translation 2 px": lambda im: translate(im, 2),
}


def attack(name, im):
    np.random.seed(2026)                    # same seeding as run_watermark.py
    return ATTACKS[name](im)
