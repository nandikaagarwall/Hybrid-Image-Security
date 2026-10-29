import numpy as np, cv2, matplotlib.pyplot as plt
from pipeline import *
from style import COL, save
SHOW = "peppers"
rgb = lambda im: cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
cover = load(SHOW)
A, *_ = embed(SHOW, "A"); B, *_ = embed(SHOW, "B")
C, wmC, keyC, fnC, kwC, bitsC, posC = make_C(SHOW, 0.10)
stages = [("Cover", cover), ("Config A", A), ("Config B", B), ("Config C", C)]

# ---------- Fig 1: visual comparison + amplified difference ----------
fig, ax = plt.subplots(2, 4, figsize=(7.2, 4.3))
for j, (t, im) in enumerate(stages):
    ax[0, j].imshow(rgb(im))
    ax[0, j].set_title(t if j == 0 else f"{t}\nPSNR {calculate_psnr(cover, im):.2f} dB · SSIM {calculate_ssim(cover, im):.4f}", fontsize=7.5)
diffs = [("A: |Δ blue| × 10", A, 0, 10), ("B: |Δ blue| × 10", B, 0, 10),
         ("C: |Δ blue| × 10", C, 0, 10), ("C: |Δ green| × 255\n(hidden layer, ±1 only)", C, 1, 255)]
for j, (t, im, ch, k) in enumerate(diffs):
    d = np.abs(im[..., ch].astype(int) - cover[..., ch].astype(int))
    ax[1, j].imshow(np.clip(d * k, 0, 255), cmap="gray", vmin=0, vmax=255); ax[1, j].set_title(t, fontsize=7.5)
for a_ in ax.ravel(): a_.set_xticks([]); a_.set_yticks([]); a_.grid(False)
fig.tight_layout(h_pad=1.2); save(fig, "fig01_visual_comparison")

# ---------- Fig 2: embedded-channel histograms + difference histograms ----------
fig, ax = plt.subplots(3, 3, figsize=(7.2, 6.2), gridspec_kw={"height_ratios": [1, 1, 0.9]})
cols = [("Config A", A, 0, "Blue"), ("Config B", B, 0, "Blue"), ("Config C", C, 1, "Green")]
bins = np.arange(257)
ymax = max(np.bincount(cover[..., c].ravel(), minlength=256).max() for c in (0, 1)) * 1.05
for j, (t, im, ch, cname) in enumerate(cols):
    hc = np.bincount(cover[..., ch].ravel(), minlength=256); hm = np.bincount(im[..., ch].ravel(), minlength=256)
    a = ax[0, j]
    a.fill_between(np.arange(256), hc, step="mid", color="#cfcec8", label="cover")
    a.step(np.arange(256), hm, where="mid", color=COL["A" if ch == 0 else "C"], lw=1, label=t)
    cap = np.sort(np.r_[hc[1:255], hm[1:255]])[-1] * 1.15
    a.set_ylim(0, cap); a.set_xlim(0, 255); a.set_title(f"{t} · {cname.lower()} channel")
    a.legend(loc="upper right", frameon=False)
    # zoom: shows the LSB pairs-of-values effect for C
    z = ax[1, j]; lo = 100
    z.bar(np.arange(lo, lo + 24) - 0.2, hc[lo:lo + 24], 0.4, color="#b9b8b2", label="cover")
    z.bar(np.arange(lo, lo + 24) + 0.2, hm[lo:lo + 24], 0.4, color=COL["A" if ch == 0 else "C"], label=t)
    z.set_title(f"zoom: values {lo}–{lo + 23}"); z.set_xlim(lo - 1, lo + 24)
    d = im[..., ch].astype(int) - cover[..., ch].astype(int)
    h = ax[2, j]; vals, cnt = np.unique(d, return_counts=True)
    h.bar(vals, cnt, 0.8, color=COL["A" if ch == 0 else "C"]); h.set_yscale("log")
    h.set_xlim(*((-30, 30) if ch == 0 else (-3, 3))); h.set_title(f"difference histogram ({cname.lower()})")
    h.set_xlabel("marked − cover"); 
    h.text(0.02, 0.95, f"changed: {np.mean(d != 0) * 100:.1f}% of pixels\nmax |Δ| = {np.abs(d).max()}",
           transform=h.transAxes, va="top", fontsize=7, bbox=dict(fc="white", ec="none", alpha=0.85, pad=1.5))
ax[0, 0].set_ylabel("count"); ax[1, 0].set_ylabel("count"); ax[2, 0].set_ylabel("count (log)")
for a in ax[0]: a.set_xlabel("pixel value")
fig.tight_layout(); save(fig, "fig02_histograms_embedded_channel")

# ---------- Fig 3: scrambling + key sensitivity ----------
wrong = descramble(SCR, x0=X0 + 1e-10)
fig, ax = plt.subplots(1, 4, figsize=(7.2, 2.3))
from src import metrics as Mm
cH = lambda im: Mm.corr_all(im)
panels = [("Plain QR", QR), ("Scrambled QR\n(logistic map, x0 = 0.12345)", SCR),
          ("Descrambled, correct key\nBER = %.3f" % calculate_ber(QR, descramble(SCR)), descramble(SCR)),
          ("Descrambled, x0 + 1e-10\nBER = %.3f" % calculate_ber(QR, wrong), wrong)]
for a, (t, im) in zip(ax, panels):
    a.imshow(im, cmap="gray", vmin=0, vmax=255, interpolation="nearest"); a.set_title(t, fontsize=8)
    c = cH(im); a.set_xlabel(f"r_H {c['h']:.3f}  r_V {c['v']:.3f}  r_D {c['d']:.3f}", fontsize=7)
    a.set_xticks([]); a.set_yticks([]); a.grid(False)
fig.tight_layout(); save(fig, "fig03_scrambling_key_sensitivity")

# ---------- Fig 4: where the hidden bits go ----------
G = wmC[..., 1]; mask = np.zeros(G.size, bool); mask[posC] = True; mask = mask.reshape(G.shape)
fig, ax = plt.subplots(1, 3, figsize=(7.2, 2.6))
ax[0].imshow(G, cmap="gray"); ax[0].set_title("Green channel (after watermark)")
ov = np.dstack([G] * 3).astype(float) / 255 * 0.55; ov[mask] = [0.92, 0.41, 0.2]
ax[1].imshow(ov); ax[1].set_title(f"Texture-ranked positions, 0.10 bpp\n({mask.sum():,} pixels, orange)")
d = (C[..., 1].astype(int) != G.astype(int))
ax[2].imshow(~d, cmap="gray"); ax[2].set_title(f"Pixels actually changed (black)\n{d.sum():,} pixels, each by ±1")
for a in ax: a.set_xticks([]); a.set_yticks([]); a.grid(False)
fig.tight_layout(); save(fig, "fig04_embedding_map")
print("ok")
