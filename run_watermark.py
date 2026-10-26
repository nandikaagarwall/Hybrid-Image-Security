"""Real measurements for Config A (base paper) and Config B (adaptive) on the 12 images.
Uses the team's own embed/extract/attack code unchanged."""
import sys, os, time, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
os.chdir(ROOT)
import numpy as np, cv2, pandas as pd
from watermark_prep import generate_qr_code, chaotic_logistic_map_scramble
from embed_watermark import embed_watermark
from embed_watermark_adaptive import embed_watermark_adaptive
from evaluate_watermark import (extract_config_a, extract_config_b, reverse_chaotic_scramble,
                                calculate_psnr, calculate_ssim, calculate_ncc, calculate_ber,
                                test_qr_decodability)
from attacks import apply_noise, apply_jpeg, apply_blur, apply_geometric

IMAGES = ["airplane", "einstein", "girl", "house", "house2", "lake", "lena",
          "mandrill", "monalisa", "monarch", "peppers", "tree"]
X0, MU = 0.12345, 3.9999
TEXT = "Author: Pranav, Country: India"
tmp = Path(tempfile.mkdtemp())

qr = generate_qr_code(TEXT)
scr, _ = chaotic_logistic_map_scramble(qr, x0=X0, mu=MU)
cv2.imwrite(str(tmp / "scr.png"), scr)

ATTACKS = {
    "No attack": lambda im: im.copy(),
    "JPEG Q=90": lambda im: apply_jpeg(im, 90),
    "JPEG Q=70": lambda im: apply_jpeg(im, 70),
    "JPEG Q=50": lambda im: apply_jpeg(im, 50),
    "Gaussian v=0.001": lambda im: apply_noise(im, "gaussian", 0.001),
    "Gaussian v=0.01": lambda im: apply_noise(im, "gaussian", 0.01),
    "Salt&Pepper d=0.01": lambda im: apply_noise(im, "sp", 0.01),
    "Avg blur 3x3": lambda im: apply_blur(im, 3),
    "Crop 25% (centre)": lambda im: apply_geometric(im, "cropping"),
    "Scaling 0.5x->1x": lambda im: apply_geometric(im, "scaling"),
    "Rotation 2 deg": lambda im: apply_geometric(im, "rotation"),
}

def embed_A(name, alpha):
    out = tmp / f"{name}_A_{alpha}.png"; keys = tmp / f"{name}_A_{alpha}.npz"
    t = time.perf_counter()
    U, S, V = embed_watermark(f"data/images/{name}.png", str(tmp / "scr.png"), str(out), alpha=alpha)
    te = time.perf_counter() - t
    np.savez(keys, U=U, S=S, V=V)
    return cv2.imread(str(out)), str(keys), te

def embed_B(name):
    out = tmp / f"{name}_B.png"; keys = tmp / f"{name}_B.npz"
    t = time.perf_counter()
    U, S, V, a = embed_watermark_adaptive(f"data/images/{name}.png", str(tmp / "scr.png"), str(out))
    te = time.perf_counter() - t
    np.savez(keys, U=U, S=S, V=V, alpha=a)
    return cv2.imread(str(out)), str(keys), te, float(a.mean())

def evaluate(cfg, name, cover, wm, keys, extract_fn, alpha_kw, t_embed, rows):
    for an, fn in ATTACKS.items():
        np.random.seed(2026)
        atk = fn(wm)
        t = time.perf_counter()
        ex = extract_fn(atk, cover, keys, **alpha_kw)
        clean = reverse_chaotic_scramble(ex, x0=X0, mu=MU)
        t_ext = time.perf_counter() - t
        rows.append(dict(config=cfg, image=name, attack=an,
                         psnr=calculate_psnr(cover, atk), ssim=calculate_ssim(cover, atk),
                         ncc=calculate_ncc(scr, ex), ber=calculate_ber(qr, clean),
                         decodes=bool(test_qr_decodability(clean)),
                         t_embed=t_embed, t_extract=t_ext))

rows, alphas_b = [], []
for name in IMAGES:
    cover = cv2.imread(f"data/images/{name}.png")
    wmA, kA, tA = embed_A(name, 0.05)
    evaluate("A (base, a=0.05)", name, cover, wmA, kA, extract_config_a, {"alpha": 0.05}, tA, rows)
    wmB, kB, tB, ab = embed_B(name)
    alphas_b.append(ab)
    evaluate("B (adaptive)", name, cover, wmB, kB, extract_config_b, {}, tB, rows)
    print(name, "done", flush=True)

df = pd.DataFrame(rows)
df.to_csv("out/exp1_watermark.csv", index=False)
print("mean adaptive alpha:", np.mean(alphas_b))

# ---- equal-quality comparison: find alpha for Config A that matches Config B's mean PSNR ----
psnrB = df[(df.config == "B (adaptive)") & (df.attack == "No attack")].psnr.mean()
best = None
for a in [0.06, 0.08, 0.10, 0.12, 0.15, 0.2, 0.25, 0.3]:
    ps = []
    for name in IMAGES:
        cover = cv2.imread(f"data/images/{name}.png")
        wm, _, _ = embed_A(name, a)
        ps.append(calculate_psnr(cover, wm))
    m = np.mean(ps); print("alpha", a, "PSNR", m)
    if best is None or abs(m - psnrB) < abs(best[1] - psnrB):
        best = (a, m)
print("PSNR B:", psnrB, "-> matched alpha", best)
rows2 = []
for name in IMAGES:
    cover = cv2.imread(f"data/images/{name}.png")
    wm, k, t = embed_A(name, best[0])
    evaluate(f"A* (base, a={best[0]})", name, cover, wm, k, extract_config_a, {"alpha": best[0]}, t, rows2)
pd.DataFrame(rows2).to_csv("out/exp1_watermark_matched.csv", index=False)

# ---- sanity check: false-positive ownership (known SVD watermark flaw) ----
qr2 = generate_qr_code("Author: Attacker, Country: Nowhere")
scr2, _ = chaotic_logistic_map_scramble(qr2, x0=X0, mu=MU)
U2, S2, V2 = np.linalg.svd(scr2.astype(float), full_matrices=False)
k2 = tmp / "attacker.npz"; np.savez(k2, U=U2, S=S2, V=V2)
fp = []
for name in IMAGES:
    cover = cv2.imread(f"data/images/{name}.png")
    wm, kA, _ = embed_A(name, 0.05)
    # (1) attacker's own U,V applied to OUR watermarked image
    ex = extract_config_a(wm, cover, str(k2), alpha=0.05)
    c = reverse_chaotic_scramble(ex, x0=X0, mu=MU)
    # (2) our keys applied to an image that was NEVER watermarked (only JPEG-90 of the cover)
    ex0 = extract_config_a(apply_jpeg(cover, 90), cover, kA, alpha=0.05)
    c0 = reverse_chaotic_scramble(ex0, x0=X0, mu=MU)
    fp.append(dict(image=name,
                   attacker_ncc=calculate_ncc(scr2, ex), attacker_ber=calculate_ber(qr2, c),
                   attacker_decodes=bool(test_qr_decodability(c)),
                   unmarked_ncc=calculate_ncc(scr, ex0), unmarked_ber=calculate_ber(qr, c0),
                   unmarked_decodes=bool(test_qr_decodability(c0))))
pd.DataFrame(fp).to_csv("out/sanity_false_positive.csv", index=False)
print(pd.DataFrame(fp))
