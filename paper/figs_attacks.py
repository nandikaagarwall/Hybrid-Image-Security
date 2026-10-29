import numpy as np, cv2, matplotlib.pyplot as plt
from pipeline import *
from style import save
SHOW = "peppers"
cover = load(SHOW)
show = ["JPEG Q=90", "JPEG Q=70", "Gaussian v=0.01", "Salt&Pepper d=0.01",
        "Avg blur 3x3", "Centre blank 6.25%", "Scaling 0.5x->1x", "Rotation 2 deg"]
fig, ax = plt.subplots(3, len(show), figsize=(7.2, 3.7))
for cfg_i, cfg in enumerate(["A", "B"]):
    img, key, fn, kw = embed(SHOW, cfg)
    for j, an in enumerate(show):
        atk = attack(an, img)
        r, _, clean = extract_wm(atk, cover, key, fn, kw)
        if cfg_i == 0:
            ax[0, j].imshow(cv2.cvtColor(atk, cv2.COLOR_BGR2RGB))
            ax[0, j].set_title(an.replace(" d=", "\nd=").replace(" v=", "\nv=").replace(" Q=", "\nQ=")
                               .replace("Centre blank", "Centre\nblank").replace(" 0.5x", "\n0.5x")
                               .replace(" 2 deg", "\n2°").replace(" 3x3", "\n3×3"), fontsize=6.5)
        a = ax[1 + cfg_i, j]
        a.imshow(clean, cmap="gray", vmin=0, vmax=255, interpolation="nearest")
        a.set_xlabel(f"BER {r['ber']*100:.1f}% {'✓' if r['decodes'] else '✗'}", fontsize=6.5,
                     color="#1f1f1d" if r["decodes"] else "#b3261e")
for a in ax.ravel(): a.set_xticks([]); a.set_yticks([]); a.grid(False)
ax[1, 0].set_ylabel("Config A", fontsize=7.5); ax[2, 0].set_ylabel("Config B", fontsize=7.5)
ax[0, 0].set_ylabel("attacked", fontsize=7.5)
fig.tight_layout(w_pad=0.3, h_pad=1.1); save(fig, "fig05_attack_grid")
print("ok")
