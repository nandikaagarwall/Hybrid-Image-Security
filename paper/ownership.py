"""Config D: blind block-SVD watermark + RSA-signed ownership certificate.

Why: in Configs A/B the verifier must use the claimant's own U, V matrices to
extract the watermark, so an attacker can bring U, V that turn OUR image into
THEIR QR (false-positive ownership, Zhang & Li 2005). Signing those keys does
not help, because the attacker can sign their own fake keys.

Fix:
 1. Blind extraction. Each QR module bit is carried by the largest singular value
    of a 4x4 block of the blue-channel LL band, using quantisation index modulation
    (QIM). Extraction needs no cover and no U/V, so there is no key that can steer
    the output towards an arbitrary QR.
 2. The bit order is permuted with the logistic map (r, x0), as in the base paper.
 3. The owner signs a certificate (owner text, public-key fingerprint, r, x0, step,
    layout) with RSA-PSS/SHA-256. The QR text carries the same fingerprint.
    A claim is accepted only if: signature valid under the presented public key,
    fingerprint(public key) == fingerprint in certificate, and the QR extracted
    from the image with the certificate's parameters decodes to the certified text.
"""
import json, hashlib
import numpy as np, pywt, cv2, qrcode
from pyzbar.pyzbar import decode as zbar_decode
from Crypto.PublicKey import RSA
from Crypto.Signature import pss
from Crypto.Hash import SHA256

BLK = 8                     # block size in the LL band (256x256 LL -> 1024 blocks = 16x16 image pixels)


def fingerprint(pub: RSA.RsaKey) -> str:
    return hashlib.sha256(pub.export_key("DER")).hexdigest()[:8]


ECC = {"L": qrcode.constants.ERROR_CORRECT_L, "M": qrcode.constants.ERROR_CORRECT_M,
       "Q": qrcode.constants.ERROR_CORRECT_Q, "H": qrcode.constants.ERROR_CORRECT_H}


def qr_modules(text, ecc="M"):
    """QR module grid WITHOUT quiet zone (1 = white). The quiet zone is known, so it is not embedded."""
    q = qrcode.QRCode(version=None, error_correction=ECC[ecc], border=0)
    q.add_data(text); q.make(fit=True)
    return (~np.array(q.modules, dtype=bool)).astype(np.uint8)        # 1 = white, 0 = black (with border)


def modules_to_image(m, size=256):
    return cv2.resize((m * 255).astype(np.uint8), (size, size), interpolation=cv2.INTER_NEAREST)


def logistic_perm(n, x0, r):
    x, s = x0, np.empty(n)
    for i in range(n):
        x = r * x * (1 - x); s[i] = x
    return np.argsort(s)


def _blocks(LL):
    h, w = LL.shape
    return [(i, j) for i in range(0, h, BLK) for j in range(0, w, BLK)]


def embed_D(bgr, modules, x0, r, step, blk=None):
    """Every LL block carries one bit: the QR modules are repeated cyclically to fill all blocks
    (841 modules -> 1024 blocks: 183 modules get a second copy), then the slots are scrambled."""
    global BLK
    BLK = blk or BLK
    B = bgr[..., 0].astype(float)
    LL, det = pywt.dwt2(B, "haar")
    blocks = _blocks(LL); nb = len(blocks); nbit = modules.size
    if nbit > nb:
        raise ValueError(f"QR has {nbit} modules but only {nb} blocks: shorten the QR text")
    bits = np.resize(modules.ravel(), nb)                              # cyclic repetition over all blocks
    perm = logistic_perm(nb, x0, r)
    slot_bits = np.empty(nb, np.uint8); slot_bits[perm] = bits         # scramble positions
    LLw = LL.copy()
    for k, (i, j) in enumerate(blocks):
        U, S, Vt = np.linalg.svd(LL[i:i + BLK, j:j + BLK])
        q = np.floor(S[0] / step)
        S[0] = (q + (0.75 if slot_bits[k] else 0.25)) * step          # QIM
        LLw[i:i + BLK, j:j + BLK] = U @ np.diag(S) @ Vt
    out = bgr.copy()
    out[..., 0] = np.clip(np.round(pywt.idwt2((LLw, det), "haar")), 0, 255).astype(np.uint8)
    return out


def _soft_bits(bgr, nslots, step):
    LL, _ = pywt.dwt2(bgr[..., 0].astype(float), "haar")
    blocks = _blocks(LL)[:nslots]
    frac = np.array([(np.linalg.svd(LL[i:i + BLK, j:j + BLK], compute_uv=False)[0] % step) / step for i, j in blocks])
    # blind drift correction: both QIM centres (0.25, 0.75) coincide after doubling the phase,
    # so the circular mean of 2*frac estimates any common shift (e.g. noise raising sigma_1)
    ang = np.angle(np.mean(np.exp(1j * 2 * np.pi * 2 * frac)))           # = pi at zero drift
    drift = ((ang - np.pi) / (2 * np.pi)) / 2
    drift = (drift + 0.25) % 0.5 - 0.25
    return np.cos(2 * np.pi * (frac - drift - 0.75))


def extract_D(bgr, shape, x0, r, step, blk=None, prefilter=None):
    """Blind: uses only the image and the certificate parameters."""
    global BLK
    BLK = blk or BLK
    if prefilter == "median":
        bgr = cv2.medianBlur(bgr, 3)
    nbit = shape[0] * shape[1]; nb = len(_blocks(np.zeros((256, 256))))
    raw = _soft_bits(bgr, nb, step)
    perm = logistic_perm(nb, x0, r)
    soft = np.bincount(np.arange(nb) % nbit, weights=raw[perm], minlength=nbit)   # unscramble, combine copies
    return (soft > 0).astype(np.uint8).reshape(shape)


def _unshift(bgr, dy, dx):
    """Undo a translation by (dy, dx) pixels (edge-replicated)."""
    if dy == 0 and dx == 0:
        return bgr
    M = np.float32([[1, 0, -dx], [0, 1, -dy]])
    return cv2.warpAffine(bgr, M, (bgr.shape[1], bgr.shape[0]), borderMode=cv2.BORDER_REPLICATE)


SHIFTS = sorted(((dy, dx) for dy in range(-4, 5) for dx in range(-4, 5)), key=lambda t: abs(t[0]) + abs(t[1]))


def extract_and_decode(bgr, shape, x0, r, step, blk=None, search_shift=True):
    """Decoder: plain image, then a 3x3 median-filtered copy (impulse noise); if neither
    decodes, re-synchronise the block grid by trying shifts of up to 4 px."""
    for dy, dx in (SHIFTS if search_shift else [(0, 0)]):
        im = _unshift(bgr, dy, dx)
        for pf in (None, "median"):
            m = extract_D(im, shape, x0, r, step, blk, pf)
            t = qr_text(m)
            if t is not None:
                return t, m
    return None, extract_D(bgr, shape, x0, r, step, blk)


def qr_text(modules):
    img = modules_to_image(modules, 10 * modules.shape[0])
    img = cv2.copyMakeBorder(img, 40, 40, 40, 40, cv2.BORDER_CONSTANT, value=255)
    d = zbar_decode(img)
    return d[0].data.decode("utf-8", "replace") if d else None


# ---------------- certificate ----------------
def make_certificate(priv: RSA.RsaKey, owner, x0, r, step, shape, block=None):
    body = dict(owner=owner, pk_fingerprint=fingerprint(priv.publickey()), x0=x0, r=r,
                step=step, block=block or BLK, qr_shape=list(shape), scheme="D-blockSVD-QIM-v1")
    msg = json.dumps(body, sort_keys=True).encode()
    sig = pss.new(priv).sign(SHA256.new(msg))
    return dict(body=body, signature=sig.hex())


def owner_qr_text(owner, pub):
    return f"{owner} | pk:{fingerprint(pub)}"


def verify_claim(image_bgr, cert, pub: RSA.RsaKey):
    """Returns (accepted, reason)."""
    body = cert["body"]
    try:
        pss.new(pub).verify(SHA256.new(json.dumps(body, sort_keys=True).encode()), bytes.fromhex(cert["signature"]))
    except (ValueError, TypeError):
        return False, "signature invalid"
    if fingerprint(pub) != body["pk_fingerprint"]:
        return False, "key fingerprint mismatch"
    txt, _ = extract_and_decode(image_bgr, tuple(body["qr_shape"]), body["x0"], body["r"], body["step"], body["block"])
    if txt is None:
        return False, "no QR in image"
    if txt != owner_qr_text(body["owner"], pub):
        return False, "QR text does not match certificate"
    return True, "accepted"
