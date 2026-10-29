"""Final paper figures: base scheme (A) vs PROPOSED (Config D watermark + AES/RSA hidden layer).
Writes paper/final/F*.png|pdf. Reads paper/out/*.csv; recomputes images for the showcase image."""
import shutil
import numpy as np, pandas as pd, cv2, matplotlib.pyplot as plt
from run_ownership_cfg import *
from style import save as _save
from src import metrics as Mm
from base_paper import MEAN_NCC
FINAL = ROOT / "paper" / "final"
CA, CP, GREY = "#2a78d6", "#7a5cd6", "#6b6b66"
LA, LP = "Base scheme (A)", "Proposed"
def save(fig, stem):
    fig.savefig(FINAL / f"{stem}.png"); fig.savefig(FINAL / f"{stem}.pdf"); plt.close(fig)
rgb = lambda im: cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
SHOW = "peppers"; cover = load(SHOW)
A, keyA, fnA, kwA = embed(SHOW, "A")
D = O.embed_D(cover, m_own, X0_OWN, R_OWN, STEP, BLKD)
bits = payload_bits(int(0.10 * 512 * 512)); G, _ = lsb_embed(D[..., 1], bits, "adaptive")
P = D.copy(); P[..., 1] = G

# F1 visual quality
fig, ax = plt.subplots(2, 3, figsize=(7.2, 5.0))
for j, (t, im) in enumerate([("Cover", cover), (LA, A), (LP, P)]):
    ax[0, j].imshow(rgb(im))
    ax[0, j].set_title(t if j == 0 else f"{t}\nPSNR {calculate_psnr(cover, im):.2f} dB · SSIM {calculate_ssim(cover, im):.4f}", fontsize=7.5)
for j, (t, im, ch, k) in enumerate([("A: |Δ blue| × 10", A, 0, 10), ("Proposed: |Δ blue| × 10\n(watermark)", P, 0, 10),
                                    ("Proposed: |Δ green| × 255\n(hidden message, ±1 only)", P, 1, 255)]):
    d = np.abs(im[..., ch].astype(int) - cover[..., ch].astype(int))
    ax[1, j].imshow(np.clip(d * k, 0, 255), cmap="gray", vmin=0, vmax=255); ax[1, j].set_title(t, fontsize=7.5)
for a in ax.ravel(): a.set_xticks([]); a.set_yticks([]); a.grid(False)
fig.tight_layout(h_pad=1.0); save(fig, "F01_visual_quality")

# F2 histograms of the embedded channels
fig, ax = plt.subplots(3, 3, figsize=(7.2, 6.2), gridspec_kw={"height_ratios": [1, 1, 0.9]})
for j, (t, im, ch, c) in enumerate([("A · blue", A, 0, CA), ("Proposed · blue", P, 0, CP), ("Proposed · green", P, 1, "#eda100")]):
    hc = np.bincount(cover[..., ch].ravel(), minlength=256); hm = np.bincount(im[..., ch].ravel(), minlength=256)
    a = ax[0, j]; a.fill_between(np.arange(256), hc, step="mid", color="#cfcec8", label="cover")
    a.step(np.arange(256), hm, where="mid", color=c, lw=1, label="marked"); a.legend(frameon=False, loc="upper right")
    a.set_ylim(0, np.sort(np.r_[hc[1:255], hm[1:255]])[-1] * 1.15); a.set_xlim(0, 255); a.set_title(t); a.set_xlabel("pixel value")
    z = ax[1, j]; lo = 100
    z.bar(np.arange(lo, lo + 24) - 0.2, hc[lo:lo + 24], 0.4, color="#b9b8b2"); z.bar(np.arange(lo, lo + 24) + 0.2, hm[lo:lo + 24], 0.4, color=c)
    z.set_title(f"zoom: values {lo}–{lo + 23}"); z.set_xlim(lo - 1, lo + 24)
    d = im[..., ch].astype(int) - cover[..., ch].astype(int); v, n = np.unique(d, return_counts=True)
    h = ax[2, j]; h.bar(v, n, 0.8, color=c); h.set_yscale("log"); h.set_xlim(*((-30, 30) if ch == 0 else (-3, 3)))
    h.set_title("difference histogram"); h.set_xlabel("marked − cover")
    h.text(0.02, 0.95, f"changed: {np.mean(d != 0) * 100:.1f}% of pixels\nmax |Δ| = {np.abs(d).max()}", transform=h.transAxes,
           va="top", fontsize=7, bbox=dict(fc="white", ec="none", alpha=0.85, pad=1.5))
ax[0, 0].set_ylabel("count"); ax[1, 0].set_ylabel("count"); ax[2, 0].set_ylabel("count (log)")
fig.tight_layout(); save(fig, "F02_histograms")

# F3 adjacent-pixel correlation, cover vs proposed
rng = np.random.default_rng(2026); N = 3000; Hh, Ww = cover.shape[:2]
ys, xs = rng.integers(0, Hh - 1, N), rng.integers(0, Ww - 1, N)
fig, ax = plt.subplots(3, 4, figsize=(7.2, 5.6), sharex=True, sharey=True)
cols = [("Cover · blue", cover, 0, GREY), ("Proposed · blue\n(watermark)", P, 0, CP), ("Cover · green", cover, 1, GREY), ("Proposed · green\n(hidden message)", P, 1, "#eda100")]
for i, (dn, (dy, dx)) in enumerate({"Horizontal": (0, 1), "Vertical": (1, 0), "Diagonal": (1, 1)}.items()):
    for j, (t, im, ch, c) in enumerate(cols):
        X = im[..., ch].astype(float); r = np.corrcoef(X[:Hh - dy, :Ww - dx].ravel(), X[dy:, dx:].ravel())[0, 1]
        a = ax[i, j]; a.scatter(X[ys, xs], X[ys + dy, xs + dx], s=1.5, color=c, alpha=0.5, linewidths=0, rasterized=True)
        a.text(0.04, 0.95, f"r = {r:.4f}", transform=a.transAxes, va="top", fontsize=7.5, bbox=dict(fc="white", ec="none", alpha=0.85, pad=1.2))
        a.set_xlim(0, 255); a.set_ylim(0, 255); a.set_xticks([0, 128, 255]); a.set_yticks([0, 128, 255])
        if i == 0: a.set_title(t, fontsize=8)
        if j == 0: a.set_ylabel(f"{dn}\nneighbour value", fontsize=8)
        if i == 2: a.set_xlabel("pixel value", fontsize=8)
fig.tight_layout(w_pad=0.6, h_pad=0.6); save(fig, "F03_pixel_correlation")

# F4 scrambling + key sensitivity (proposed)
nb = 1024; reps = nb // m_own.size; nslot = reps * m_own.size
perm = O.logistic_perm(nslot, X0_OWN, R_OWN)
slot = np.full(nb, 0.5); sb = np.empty(nslot); sb[perm] = np.tile(m_own.ravel(), reps); slot[:nslot] = sb
right = O.extract_D(P, m_own.shape, X0_OWN, R_OWN, STEP, BLKD)
wrong = O.extract_D(P, m_own.shape, X0_OWN + 1e-10, R_OWN, STEP, BLKD)
fig, ax = plt.subplots(1, 4, figsize=(7.2, 2.4))
for a, (im, t) in zip(ax, [(m_own, f"Watermark QR ({m_own.shape[0]}×{m_own.shape[1]} modules)\n\"{O.qr_text(m_own)}\""),
                           (slot.reshape(32, 32), "Scrambled bit layout\n(one cell = one 8×8 LL block)"),
                           (right, f"Extracted, correct key\nBER {np.mean(right != m_own) * 100:.1f}% · decodes"),
                           (wrong, f"Extracted, x0 + 1e−10\nBER {np.mean(wrong != m_own) * 100:.1f}% · {'decodes' if O.qr_text(wrong) else 'no QR'}")]):
    a.imshow(im, cmap="gray", vmin=0, vmax=1, interpolation="nearest"); a.set_title(t, fontsize=6.8)
    a.set_xticks([]); a.set_yticks([]); a.grid(False)
fig.tight_layout(); save(fig, "F04_scrambling_key_sensitivity")

# F5 attack grid
show = ["JPEG Q=70", "JPEG Q=50", "Gaussian v=0.01", "Salt&Pepper d=0.01", "Avg blur 3x3", "Centre blank 6.25%", "Scaling 0.5x->1x", "Translation 2 px"]
lab = lambda s: (s.replace(" Q=", "\nQ=").replace(" v=", "\nv=").replace(" d=", "\nd=").replace("Centre blank", "Centre\nblank")
                  .replace(" 0.5x", "\n0.5x").replace(" 3x3", "\n3×3").replace(" 2 px", "\n2 px"))
fig, ax = plt.subplots(3, len(show), figsize=(7.2, 3.8))
for j, an in enumerate(show):
    atkP = attack(an, P); ax[0, j].imshow(rgb(atkP)); ax[0, j].set_title(lab(an), fontsize=6.5)
    r, _, cA = extract_wm(attack(an, A), cover, keyA, fnA, kwA)
    ax[1, j].imshow(cA, cmap="gray", vmin=0, vmax=255, interpolation="nearest")
    ax[1, j].set_xlabel(f"{'✓' if r['decodes'] else '✗'} BER {r['ber']*100:.1f}%", fontsize=6.5, color="#1f1f1d" if r["decodes"] else "#b3261e")
    t, mm = O.extract_and_decode(atkP, m_own.shape, X0_OWN, R_OWN, STEP, BLKD)
    ax[2, j].imshow(mm, cmap="gray", vmin=0, vmax=1, interpolation="nearest")
    ax[2, j].set_xlabel(f"{'✓' if t else '✗'} BER {np.mean(mm != m_own)*100:.1f}%", fontsize=6.5, color="#1f1f1d" if t else "#b3261e")
for a in ax.ravel(): a.set_xticks([]); a.set_yticks([]); a.grid(False)
ax[0, 0].set_ylabel("attacked\n(proposed)", fontsize=7); ax[1, 0].set_ylabel(LA, fontsize=7); ax[2, 0].set_ylabel(LP, fontsize=7)
fig.tight_layout(w_pad=0.3, h_pad=1.1); save(fig, "F05_attack_grid")

# F6 decodability vs attack strength
swA = pd.read_csv(OUT / "sweeps.csv"); swA = swA[swA.config == "A"]; swP = pd.read_csv(OUT / "final_sweeps_P.csv")
fig, ax = plt.subplots(1, 3, figsize=(7.2, 2.6), sharey=True)
for a, (s, xl, inv) in zip(ax, [("jpeg", "JPEG quality factor", True), ("gaussian", "Gaussian noise variance", False), ("saltpepper", "Salt & pepper density", False)]):
    for d, c, m, l in [(swA, CA, "o", LA), (swP, CP, "D", LP)]:
        g = d[d.sweep == s].groupby("level").decodes.mean() * 100
        a.plot(g.index, g.values, color=c, marker=m, ms=5, label=l)
    a.set_xlabel(xl); a.set_ylim(-4, 104)
    if inv: a.invert_xaxis()
    else: a.set_xscale("log")
ax[0].set_ylabel("QR decodable (% of 12 images)")
h, l = ax[0].get_legend_handles_labels(); fig.legend(h, l, ncol=2, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.05))
fig.tight_layout(); save(fig, "F06_robustness_vs_strength")

# F7 imperceptibility-robustness trade-off
alA = pd.read_csv(OUT / "alpha_tradeoff.csv"); trP = pd.read_csv(OUT / "final_step_tradeoff_P.csv")
fig, ax = plt.subplots(1, 3, figsize=(7.2, 2.7), sharey=True)
for a, an in zip(ax, ["JPEG Q=70", "Gaussian v=0.01", "Salt&Pepper d=0.01"]):
    gA = alA[alA.attack == an].groupby("alpha").agg(psnr=("psnr", "mean"), ok=("decodes", "mean"))
    gP = trP[trP.attack == an].groupby("step").agg(psnr=("psnr", "mean"), ok=("decodes", "mean"))
    a.plot(gA.psnr, gA.ok * 100, color=CA, marker="o", ms=4.5, label=LA + " (varying α)")
    a.plot(gP.psnr, gP.ok * 100, color=CP, marker="D", ms=4.5, label=LP + " (varying QIM step)")
    a.axvline(40, color="#b9b8b2", lw=0.8, ls=":"); a.invert_xaxis(); a.set_title(an); a.set_xlabel("PSNR (dB)  ← more visible")
ax[0].set_ylabel("QR decodable (% of 12 images)"); ax[0].set_ylim(-4, 104)
h, l = ax[0].get_legend_handles_labels(); fig.legend(h, l, ncol=2, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.06))
fig.tight_layout(); save(fig, "F07_tradeoff")

# F8 hidden layer, F9 ownership: produced earlier from the same data
shutil.copy(FIG / "fig08_hidden_layer.png", FINAL / "F08_hidden_layer.png"); shutil.copy(FIG / "fig08_hidden_layer.pdf", FINAL / "F08_hidden_layer.pdf")
shutil.copy(FIG / "fig11_ownership_attack.png", FINAL / "F09_ownership_attack.png"); shutil.copy(FIG / "fig11_ownership_attack.pdf", FINAL / "F09_ownership_attack.pdf")

# F10 comparison with the base paper
rA = pd.read_csv(OUT / "robustness.csv"); rA = rA[rA.config == "A"]; rP = pd.read_csv(OUT / "final_robustness_P.csv")
atks = list(MEAN_NCC); x = np.arange(len(atks)); w = 0.27
fig, ax = plt.subplots(2, 1, figsize=(7.2, 4.6), sharex=True)
ax[0].bar(x - w, [MEAN_NCC[a] for a in atks], w * 0.92, color="#4a4a46", hatch="//", edgecolor="white", lw=0, label="Base paper (as reported)")
ax[0].bar(x, [rA.groupby("attack").ncc.mean()[a] for a in atks], w * 0.92, color=CA, label="Base scheme, our reproduction (A)")
ax[0].bar(x + w, [rP.groupby("attack").ncc.mean()[a] for a in atks], w * 0.92, color=CP, label=LP)
ax[0].set_ylim(0.3, 1.02); ax[0].set_ylabel("NCC (mean, 12 images)")
ax[0].legend(ncol=3, frameon=False, fontsize=7, loc="lower left", bbox_to_anchor=(0, 1.0))
ax[1].bar(x - w / 2, [rA.groupby("attack").decodes.sum()[a] for a in atks], w * 0.92, color=CA)
ax[1].bar(x + w / 2, [rP.groupby("attack").decodes.sum()[a] for a in atks], w * 0.92, color=CP)
ax[1].set_ylabel("QR decodable (of 12)"); ax[1].set_ylim(0, 13)
ax[1].text(-0.45, 12.3, "base paper does not report decodability", fontsize=7, color="#6b6b66")
ax[1].set_xticks(x); ax[1].set_xticklabels([a.replace(" ", "\n", 1) for a in atks], fontsize=7)
fig.tight_layout(); save(fig, "F10_comparison_base_paper")
print("figures ok")
