"""Hidden layer (team's texture-ranked LSB from src/stego.py, applied to the GREEN channel),
naive random-LSB baseline, Exp 5 security metrics, preliminary steganalysis, timing."""
import sys, os, time, glob
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
os.chdir(ROOT)
import numpy as np, cv2, pandas as pd
from Crypto.Cipher import AES
from src.stego import calculate_block_variances, BLOCK_SIZE
from src.payload import encrypt_payload, decrypt_payload, bytes_to_bitstream, bitstream_to_bytes
from src import metrics as M
from watermark_prep import generate_qr_code, chaotic_logistic_map_scramble
from evaluate_watermark import reverse_chaotic_scramble, calculate_ber
from attacks import apply_jpeg, apply_noise

IMAGES = ["airplane", "einstein", "girl", "house", "house2", "lake", "lena",
          "mandrill", "monalisa", "peppers", "tree"]          # monarch dropped: duplicate of lake
BPP = [0.05, 0.1, 0.2, 0.3, 0.4]
rng = np.random.default_rng(2026)

# ---------------- embedding (team algorithm, in memory) ----------------
def adaptive_positions(ch):
    pos = []
    for _, r, c in calculate_block_variances(ch):
        for dr in range(BLOCK_SIZE):
            for dc in range(BLOCK_SIZE):
                pos.append((r + dr) * ch.shape[1] + (c + dc))
    return np.array(pos)

def random_positions(ch, seed=7):
    return np.random.default_rng(seed).permutation(ch.size)

def embed(ch, bits, method):
    pos = adaptive_positions(ch) if method == "adaptive" else random_positions(ch)
    out = ch.copy().ravel()
    p = pos[:len(bits)]
    out[p] = (out[p] & 0xFE) | bits
    return out.reshape(ch.shape)

def extract(ch, n, method):
    pos = adaptive_positions(ch) if method == "adaptive" else random_positions(ch)
    return (ch.ravel()[pos[:n]] & 1).astype(np.uint8)

def payload_bits(n_bits):
    """Real AES+RSA encrypted message + length header, padded with random bits to n_bits."""
    blob = encrypt_payload("Confidential: project record #001. Sharing prohibited.")
    bits = np.array(bytes_to_bitstream(blob), dtype=np.uint8)
    if n_bits > bits.size:
        bits = np.concatenate([bits, rng.integers(0, 2, n_bits - bits.size, dtype=np.uint8)])
    return bits[:n_bits], blob

# ---------------- Exp 1 (concealment side) + Exp 3 (capacity) ----------------
rows = []
for name in IMAGES:
    img = cv2.cvtColor(cv2.imread(f"data/images/{name}.png"), cv2.COLOR_BGR2RGB)
    G = img[..., 1]
    for bpp in BPP:
        n = int(bpp * G.size)
        bits, blob = payload_bits(n)
        for method in ["adaptive", "random"]:
            t = time.perf_counter(); Gs = embed(G, bits, method); te = time.perf_counter() - t
            st = img.copy(); st[..., 1] = Gs
            t = time.perf_counter(); ext = extract(Gs, n, method); tx = time.perf_counter() - t
            msg_ok = decrypt_payload(bitstream_to_bytes(list(ext))) .startswith("Confidential")
            bgr = cv2.cvtColor(st, cv2.COLOR_RGB2BGR)
            def ber_after(att):
                a = cv2.cvtColor(att, cv2.COLOR_BGR2RGB)[..., 1]
                return M.ber(bits, extract(a, n, method))
            np.random.seed(1)
            cd = M.corr_diff(G, Gs)
            rows.append(dict(image=name, bpp=bpp, method=method,
                psnr_rgb=M.psnr(img, st), psnr_g=M.psnr(G, Gs), ssim=M.ssim(img, st),
                entropy_diff=M.entropy_diff(G, Gs), chi2_dist=M.hist_chi2_distance(G, Gs),
                corr_diff_h=cd["h"], corr_diff_v=cd["v"], corr_diff_d=cd["d"],
                ber_clean=M.ber(bits, ext), msg_recovered=msg_ok,
                ber_jpeg90=ber_after(apply_jpeg(bgr, 90)),
                ber_gauss001=ber_after(apply_noise(bgr, "gaussian", 0.001)),
                t_embed=te, t_extract=tx))
    print(name, flush=True)
pd.DataFrame(rows).to_csv("out/exp1_3_stego.csv", index=False)

# ---------------- Exp 5: security metrics ----------------
sec = []
X0, MU = 0.12345, 3.9999
qr = generate_qr_code("Author: Pranav, Country: India")
scr, _ = chaotic_logistic_map_scramble(qr, x0=X0, mu=MU)
def secrow(label, im):
    c = M.corr_all(im)
    return dict(item=label, entropy=M.entropy(im), chi2=M.hist_chi2_uniform(im),
                corr_h=c["h"], corr_v=c["v"], corr_d=c["d"])
sec.append(secrow("Plain QR (watermark)", qr))
sec.append(secrow("Scrambled QR (logistic map)", scr))
# NPCR/UACI for scrambling: change one pixel of the QR
qr2 = qr.copy(); qr2[128, 128] = 255 - qr2[128, 128]
scr2, _ = chaotic_logistic_map_scramble(qr2, x0=X0, mu=MU)
npcr_s, uaci_s = M.npcr_uaci(scr, scr2)
# AES payload as an image: 256x256 bytes of ciphertext, fixed key/IV for the differential test
key = bytes(range(32)); iv = bytes(range(16))
plain = (b"Confidential project record. " * 3000)[:65536]
ct = AES.new(key, AES.MODE_CBC, iv).encrypt(plain)
ct_img = np.frombuffer(ct, np.uint8).reshape(256, 256)
sec.append(secrow("AES-256-CBC ciphertext (payload)", ct_img))
sec.append(secrow("Plaintext payload (as bytes)", np.frombuffer(plain, np.uint8).reshape(256, 256)))
p_first = bytearray(plain); p_first[0] ^= 1
p_last = bytearray(plain); p_last[-1] ^= 1
c_first = np.frombuffer(AES.new(key, AES.MODE_CBC, iv).encrypt(bytes(p_first)), np.uint8)
c_last = np.frombuffer(AES.new(key, AES.MODE_CBC, iv).encrypt(bytes(p_last)), np.uint8)
ct_flat = np.frombuffer(ct, np.uint8)
npcr_f, uaci_f = M.npcr_uaci(ct_flat, c_first)
npcr_l, uaci_l = M.npcr_uaci(ct_flat, c_last)
# Key sensitivity
k2 = bytearray(key); k2[0] ^= 1
dec_wrong = np.frombuffer(AES.new(bytes(k2), AES.MODE_CBC, iv).decrypt(ct), np.uint8)
aes_wrong_diff = float(np.mean(dec_wrong != np.frombuffer(plain, np.uint8)) * 100)
unscr_wrong = reverse_chaotic_scramble(scr, x0=X0 + 1e-10, mu=MU)
unscr_right = reverse_chaotic_scramble(scr, x0=X0, mu=MU)
diff = dict(npcr_scramble=npcr_s, uaci_scramble=uaci_s,
            npcr_aes_first_byte=npcr_f, uaci_aes_first_byte=uaci_f,
            npcr_aes_last_byte=npcr_l, uaci_aes_last_byte=uaci_l,
            aes_wrongkey_bytes_differ_pct=aes_wrong_diff,
            logistic_wrong_x0_ber=calculate_ber(qr, unscr_wrong),
            logistic_right_x0_ber=calculate_ber(qr, unscr_right))
pd.DataFrame(sec).to_csv("out/exp5_security.csv", index=False)
pd.Series(diff).to_csv("out/exp5_differential.csv")
print(pd.DataFrame(sec).round(4)); print(pd.Series(diff).round(4))

# ---------------- Exp 2 (preliminary): steganalysis on image patches ----------------
def spam686(X, T=3):
    X = X.astype(np.int32)
    def dirs(A):
        return {"r": (A[:, :-1] - A[:, 1:]), "l": (A[:, 1:] - A[:, :-1]),
                "d": (A[:-1, :] - A[1:, :]), "u": (A[1:, :] - A[:-1, :]),
                "rd": (A[:-1, :-1] - A[1:, 1:]), "lu": (A[1:, 1:] - A[:-1, :-1]),
                "ld": (A[:-1, 1:] - A[1:, :-1]), "ru": (A[1:, :-1] - A[:-1, 1:])}
    def markov2(D, shift):
        D = np.clip(D, -T, T) + T
        dy, dx = shift
        H, W = D.shape
        a = D[:H - 2 * dy, :W - 2 * dx] if dx >= 0 else D[:H - 2 * dy, -2 * dx:]
        b = D[dy:H - dy, dx:W - dx] if dx >= 0 else D[dy:H - dy, -dx:W + dx]
        c = D[2 * dy:, 2 * dx:] if dx >= 0 else D[2 * dy:, :W + 2 * dx]
        k = 2 * T + 1
        idx = (a * k + b) * k + c
        cnt = np.bincount(idx.ravel(), minlength=k ** 3).reshape(k, k, k).astype(float)
        den = cnt.sum(axis=2, keepdims=True); den[den == 0] = 1
        return (cnt / den).ravel()
    d = dirs(X)
    sh = {"r": (0, 1), "l": (0, 1), "d": (1, 0), "u": (1, 0), "rd": (1, 1), "lu": (1, 1), "ld": (1, -1), "ru": (1, -1)}
    m = {k: markov2(v, sh[k]) for k, v in d.items()}
    F1 = (m["r"] + m["l"] + m["d"] + m["u"]) / 4
    F2 = (m["rd"] + m["lu"] + m["ld"] + m["ru"]) / 4
    return np.concatenate([F1, F2])

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GroupShuffleSplit
sources = [f"data/images/{n}.png" for n in IMAGES] + sorted(glob.glob("data/standard/*"))
patches, groups = [], []
P = 128
for gi, f in enumerate(sources):
    im = cv2.imread(f)
    if im is None: continue
    g = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)[..., 1]
    for r in range(0, g.shape[0] - P + 1, P):
        for c in range(0, g.shape[1] - P + 1, P):
            patches.append(g[r:r + P, c:c + P].copy()); groups.append(gi)
groups = np.array(groups)
print("patches:", len(patches), "from", len(set(groups)), "images", flush=True)
cover_f = np.array([spam686(p) for p in patches])
det = []
for bpp in [0.1, 0.2, 0.4]:
    for method in ["adaptive", "random"]:
        stego_f = []
        for p in patches:
            n = int(bpp * p.size)
            stego_f.append(spam686(embed(p, rng.integers(0, 2, n, dtype=np.uint8), method)))
        X = np.vstack([cover_f, np.array(stego_f)]); y = np.r_[np.zeros(len(patches)), np.ones(len(patches))]
        gg = np.r_[groups, groups]
        pes = []
        for split in range(5):
            tr, te = next(GroupShuffleSplit(1, test_size=0.4, random_state=split).split(X, y, gg))
            clf = RandomForestClassifier(300, random_state=split, n_jobs=-1).fit(X[tr], y[tr])
            pes.append(M.detection_error(y[te], clf.predict_proba(X[te])[:, 1]))
        det.append(dict(bpp=bpp, method=method, pe_mean=np.mean(pes), pe_std=np.std(pes, ddof=1),
                        n_cover=len(patches)))
        print(det[-1], flush=True)
pd.DataFrame(det).to_csv("out/exp2_steganalysis_prelim.csv", index=False)
