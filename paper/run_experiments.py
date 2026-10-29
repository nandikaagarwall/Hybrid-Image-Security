"""Runs every experiment behind the paper figures; writes CSVs to paper/out/."""
import time
import numpy as np, pandas as pd, cv2
from pipeline import *
from src import metrics as M

def chan_psnr(a, b):  # BGR order -> report R,G,B
    return {f"psnr_{c}": calculate_psnr(a[..., i], b[..., i]) for c, i in (("R", 2), ("G", 1), ("B", 0))}

# ---------- 1. imperceptibility + robustness for A, A*, B, C ----------
rows, imp = [], []
for name in IMAGES:
    cover = load(name)
    for cfg in ["A", "A*", "B", "C"]:
        t = time.perf_counter()
        if cfg == "C":
            img, wm, key, fn, kw, bits, _ = make_C(name, 0.10)
        else:
            img, key, fn, kw = embed(name, cfg)
        te = time.perf_counter() - t
        imp.append(dict(config=cfg, image=LABEL.get(name, name), psnr=calculate_psnr(cover, img),
                        ssim=calculate_ssim(cover, img), **chan_psnr(cover, img), t_embed=te))
        for an in ATTACKS:
            atk = attack(an, img)
            t = time.perf_counter()
            r, _, _ = extract_wm(atk, cover, key, fn, kw)
            r.update(config=cfg, image=LABEL.get(name, name), attack=an,
                     psnr=calculate_psnr(cover, atk), ssim=calculate_ssim(cover, atk),
                     t_extract=time.perf_counter() - t)
            if cfg == "C":
                ext = lsb_extract(atk[..., 1], len(bits))
                r["payload_ber"] = M.ber(bits, ext)
                r["msg_ok"] = recover_message(ext) == MESSAGE
            rows.append(r)
    print(name, flush=True)
pd.DataFrame(rows).to_csv(OUT / "robustness.csv", index=False)
pd.DataFrame(imp).to_csv(OUT / "imperceptibility.csv", index=False)

# ---------- 2. attack-strength sweeps (A, A*, B) ----------
SWEEPS = {
    "jpeg": ([100, 90, 80, 70, 60, 50, 40, 30], lambda im, q: apply_jpeg(im, q)),
    "gaussian": ([0.0005, 0.001, 0.002, 0.005, 0.01, 0.02], lambda im, v: apply_noise(im, "gaussian", v)),
    "saltpepper": ([0.005, 0.01, 0.02, 0.05, 0.1], lambda im, d: apply_noise(im, "sp", d)),
}
sw = []
for name in IMAGES:
    cover = load(name)
    for cfg in ["A", "A*", "B"]:
        img, key, fn, kw = embed(name, cfg)
        for sname, (levels, f) in SWEEPS.items():
            for lv in levels:
                np.random.seed(2026)
                r, _, _ = extract_wm(f(img, lv), cover, key, fn, kw)
                sw.append(dict(config=cfg, image=name, sweep=sname, level=lv, **r))
    print("sweep", name, flush=True)
pd.DataFrame(sw).to_csv(OUT / "sweeps.csv", index=False)

# ---------- 3. alpha trade-off (global alpha) ----------
al = []
for name in IMAGES:
    cover = load(name)
    for a in [0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.10, 0.15]:
        img, key, fn, kw = embed(name, "A", alpha=a)
        for an in ["JPEG Q=70", "Gaussian v=0.01", "Salt&Pepper d=0.01"]:
            r, _, _ = extract_wm(attack(an, img), cover, key, fn, kw)
            al.append(dict(image=name, alpha=a, psnr=calculate_psnr(cover, img), attack=an, **r))
    print("alpha", name, flush=True)
pd.DataFrame(al).to_csv(OUT / "alpha_tradeoff.csv", index=False)

# ---------- 4. baseline: what does extraction give on an image that was never marked? ----------
bl = []
for name in IMAGES:
    cover = load(name)
    _, key, fn, kw = embed(name, "A")
    r, _, _ = extract_wm(apply_jpeg(cover, 90), cover, key, fn, kw)
    bl.append(dict(image=name, **r))
pd.DataFrame(bl).to_csv(OUT / "unmarked_baseline.csv", index=False)
print("done")
