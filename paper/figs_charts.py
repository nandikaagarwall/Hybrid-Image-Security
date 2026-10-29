import numpy as np, pandas as pd, matplotlib.pyplot as plt
from pipeline import OUT, ROOT
from style import COL, MRK, NAME, save

# ---------- Fig 6: BER vs attack strength ----------
sw = pd.read_csv(OUT / "sweeps.csv")
fig, ax = plt.subplots(1, 3, figsize=(7.2, 2.6), sharey=True)
spec = [("jpeg", "JPEG quality factor", True), ("gaussian", "Gaussian noise variance", False),
        ("saltpepper", "Salt & pepper density", False)]
for a, (s, xl, inv) in zip(ax, spec):
    d = sw[sw.sweep == s]
    for cfg in ["A", "A*", "B"]:
        g = d[d.config == cfg].groupby("level").ber.agg(["mean", "std"]) * 100
        a.errorbar(g.index, g["mean"], yerr=g["std"], color=COL[cfg], marker=MRK[cfg], ms=5,
                   capsize=2, elinewidth=0.8, label=NAME[cfg])
    a.set_xlabel(xl)
    if inv: a.invert_xaxis()
    else: a.set_xscale("log")
    a.axhline(50, color="#8a8a85", lw=0.8, ls=":"); 
ax[0].text(98, 51.5, "random guess (50%)", fontsize=7, color="#6b6b66")
ax[0].set_ylabel("Watermark BER (%) — mean ± SD, 12 images"); ax[0].set_ylim(-2, 58)
h, l = ax[0].get_legend_handles_labels()
fig.legend(h, l, ncol=3, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.06))
fig.tight_layout(); save(fig, "fig06_ber_vs_attack_strength")

# ---------- Fig 7: alpha trade-off ----------
al = pd.read_csv(OUT / "alpha_tradeoff.csv")
fig, ax = plt.subplots(1, 2, figsize=(7.2, 2.8))
g = al.groupby(["alpha", "attack"]).agg(psnr=("psnr", "mean"), ber=("ber", "mean"), ok=("decodes", "mean")).reset_index()
tc = {"JPEG Q=70": "#2a78d6", "Gaussian v=0.01": "#eb6834", "Salt&Pepper d=0.01": "#1baf7a"}
tm = {"JPEG Q=70": "o", "Gaussian v=0.01": "s", "Salt&Pepper d=0.01": "^"}
for at, d in g.groupby("attack"):
    ax[0].plot(d.psnr, d.ber * 100, color=tc[at], marker=tm[at], ms=5, label=at)
    ax[1].plot(d.alpha, d.ok * 100, color=tc[at], marker=tm[at], ms=5, label=at)
for _, r in g[g.attack == "JPEG Q=70"].iterrows():
    ax[0].annotate(f"α={r.alpha:g}", (r.psnr, r.ber * 100), textcoords="offset points", xytext=(3, 4), fontsize=6.5, color="#4a4a46")
ax[0].invert_xaxis(); ax[0].set_xlabel("PSNR of marked image (dB)  ← more visible"); ax[0].set_ylabel("Watermark BER (%)")
ax[0].set_title("Imperceptibility vs robustness (global α)")
ax[1].axvline(0.05, color="#8a8a85", ls=":", lw=0.8); ax[1].text(0.052, 4, "base paper α", fontsize=7, color="#6b6b66")
ax[1].set_xlabel("embedding strength α"); ax[1].set_ylabel("QR decodable (% of 12 images)"); ax[1].set_ylim(-3, 103)
ax[1].set_title("Decodability vs α"); ax[1].legend(frameon=False, loc="center right", bbox_to_anchor=(1, 0.5))
fig.tight_layout(); save(fig, "fig07_alpha_tradeoff")

# ---------- Fig 8: hidden layer: capacity, RS, SPAM ----------
st = pd.read_csv(ROOT / "exp1_3_stego.csv")
rs = pd.read_csv(OUT / "steganalysis_rs_chi2.csv")
pe = pd.read_csv(ROOT / "exp2_steganalysis_prelim.csv")
fig, ax = plt.subplots(1, 3, figsize=(7.2, 2.6))
lab = {"adaptive": "texture-ranked (ours)", "random": "random LSB"}
for m in ["adaptive", "random"]:
    g = st[st.method == m].groupby("bpp").psnr_g.agg(["mean", "std"])
    ax[0].errorbar(g.index, g["mean"], yerr=g["std"], color=COL[m], marker=MRK[m], ms=5, capsize=2,
                   ls="-" if m == "adaptive" else "--", label=lab[m])
    g = rs[rs.method == m].groupby("bpp").rs_est.agg(["mean", "std"])
    ax[1].errorbar(g.index, g["mean"], yerr=g["std"], color=COL[m], marker=MRK[m], ms=5, capsize=2,
                   ls="-" if m == "adaptive" else "--", label=lab[m])
    g = pe[pe.method == m]
    ax[2].errorbar(g.bpp, g.pe_mean, yerr=g.pe_std, color=COL[m], marker=MRK[m], ms=5, capsize=2,
                   ls="-" if m == "adaptive" else "--", label=lab[m])
ax[0].set_title("Green-channel PSNR\n(PSNR curves overlap)"); ax[0].set_ylabel("PSNR (dB)")
ax[1].plot([0, 0.4], [0, 0.4], color="#8a8a85", lw=0.8, ls=":"); ax[1].text(0.2, 0.235, "perfect\nestimate", fontsize=7, color="#6b6b66", ha="right")
ax[1].set_title("RS steganalysis:\nestimated vs true payload"); ax[1].set_ylabel("RS-estimated rate")
ax[2].axhline(0.5, color="#8a8a85", lw=0.8, ls=":"); ax[2].text(0.4, 0.485, "undetectable", fontsize=7, color="#6b6b66", ha="right")
ax[2].set_title("SPAM + RF detector\n(preliminary, 494 patches)"); ax[2].set_ylabel("detection error $P_E$"); ax[2].set_ylim(0.2, 0.55)
for a in ax: a.set_xlabel("payload (bpp)")
ax[1].legend(frameon=False, loc="upper left", fontsize=7)
fig.tight_layout(); save(fig, "fig08_hidden_layer")
print("ok")
