import numpy as np, matplotlib.pyplot as plt
from pipeline import *
from style import COL, save
SHOW = "peppers"
cover = load(SHOW)
C, *_ = make_C(SHOW, 0.10)
rng = np.random.default_rng(2026)
N = 3000
dirs = {"Horizontal": (0, 1), "Vertical": (1, 0), "Diagonal": (1, 1)}
cols = [("Cover · blue", cover, 0, COL["cover"]), ("Config C · blue\n(watermark layer)", C, 0, COL["A"]),
        ("Cover · green", cover, 1, COL["cover"]), ("Config C · green\n(hidden layer)", C, 1, COL["C"])]
H, W = cover.shape[:2]
ys, xs = rng.integers(0, H - 1, N), rng.integers(0, W - 1, N)   # same positions in every panel
fig, ax = plt.subplots(3, 4, figsize=(7.2, 5.6), sharex=True, sharey=True)
for i, (dn, (dy, dx)) in enumerate(dirs.items()):
    for j, (t, im, ch, c) in enumerate(cols):
        X = im[..., ch].astype(float)
        a_all, b_all = X[:H - dy, :W - dx].ravel(), X[dy:, dx:].ravel()
        r = np.corrcoef(a_all, b_all)[0, 1]                         # r over ALL pixel pairs
        a = ax[i, j]
        a.scatter(X[ys, xs], X[ys + dy, xs + dx], s=1.5, color=c if c != COL["cover"] else "#6b6b66",
                  alpha=0.5, linewidths=0, rasterized=True)
        a.text(0.04, 0.95, f"r = {r:.4f}", transform=a.transAxes, va="top", fontsize=7.5,
               bbox=dict(fc="white", ec="none", alpha=0.85, pad=1.2))
        a.set_xlim(0, 255); a.set_ylim(0, 255); a.set_xticks([0, 128, 255]); a.set_yticks([0, 128, 255])
        if i == 0: a.set_title(t, fontsize=8)
        if j == 0: a.set_ylabel(f"{dn}\nneighbour value", fontsize=8)
        if i == 2: a.set_xlabel("pixel value", fontsize=8)
fig.tight_layout(w_pad=0.6, h_pad=0.6); save(fig, "fig10_adjacent_pixel_correlation")
print("ok")
