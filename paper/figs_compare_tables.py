import numpy as np, pandas as pd, matplotlib.pyplot as plt
from pipeline import OUT, ROOT, FIG
from style import COL, NAME, save
from base_paper import MEAN_NCC, NCC, PSNR_NO_ATTACK
rb = pd.read_csv(OUT / "robustness.csv"); imp = pd.read_csv(OUT / "imperceptibility.csv")
bl = pd.read_csv(OUT / "unmarked_baseline.csv")
atk = list(MEAN_NCC)

# ---------- Fig 9: comparison with base paper ----------
fig, ax = plt.subplots(2, 1, figsize=(7.2, 4.8), sharex=True)
x = np.arange(len(atk)); w = 0.2
series = [("Base paper (reported)", "#4a4a46", [MEAN_NCC[a] for a in atk], None)]
for cfg in ["A", "B", "C"]:
    d = rb[rb.config == cfg].groupby("attack")
    series.append((NAME[cfg] if cfg != "A" else "A: our reproduction", COL[cfg],
                   [d.ncc.mean()[a] for a in atk], [d.ber.mean()[a] * 100 for a in atk]))
for i, (lab, c, ncc, ber) in enumerate(series):
    ax[0].bar(x + (i - 1.5) * w, ncc, w * 0.9, color=c, label=lab, hatch="//" if i == 0 else None, edgecolor="white", lw=0)
    if ber is not None:
        ax[1].bar(x + (i - 1.5) * w, ber, w * 0.9, color=c, label=lab)
ax[0].axhline(bl.ncc.mean(), color="#b3261e", ls="--", lw=1)
ax[0].text(-0.62, bl.ncc.mean() - 0.045, f"NCC of a never-watermarked image = {bl.ncc.mean():.2f}",
           ha="left", bbox=dict(fc="white", ec="none", pad=1), fontsize=7, color="#b3261e")
ax[0].set_ylim(0.3, 1.02); ax[0].set_xlim(-0.7, len(atk) - 0.3); ax[0].set_ylabel("NCC (mean, 12 images)")
ax[0].legend(ncol=4, frameon=False, fontsize=7, loc="lower left", bbox_to_anchor=(0, 1.0))
ax[1].axhline(50, color="#8a8a85", ls=":", lw=0.8); ax[1].set_ylabel("BER of decoded QR (%)")
ax[1].text(-0.4, 44, "base paper reports no BER", fontsize=7, color="#6b6b66")
ax[1].set_xticks(x); ax[1].set_xticklabels([a.replace(" ", "\n", 1) for a in atk], fontsize=7)
fig.tight_layout(); save(fig, "fig09_comparison_base_paper")

# ---------- Tables ----------
md = []
def table(df, title, note=""):
    md.append(f"## {title}\n"); md.append(df.to_markdown(index=False)); md.append(f"\n{note}\n")
    df.to_csv(OUT / ("table_" + title.split(":")[0].lower().replace(" ", "") + ".csv"), index=False)

# T1 per-image imperceptibility
p = imp.pivot_table(index="image", columns="config", values=["psnr", "ssim"])
t1 = pd.DataFrame({"Image": p.index})
for cfg in ["A", "A*", "B", "C"]:
    t1[f"{cfg} PSNR (dB)"] = p["psnr"][cfg].round(2).values; t1[f"{cfg} SSIM"] = p["ssim"][cfg].round(4).values
base = dict(zip(["house", "tree", "girl", "mandrill", "lena", "airplane", "lake", "peppers", "house2", "einstein", "monalisa", "boat"], PSNR_NO_ATTACK))
t1.insert(1, "Base paper PSNR (reported)", t1.Image.map(base))
mean = t1.drop(columns="Image").mean().round(4); t1.loc[len(t1)] = ["Mean"] + list(mean.values)
table(t1, "Table 1: Imperceptibility per image",
      "Base paper reports PSNR only (Table 2 of Sanivarapu et al.); its 'Monarch' and 'Jetplane' are taken as our 'boat' and 'airplane'. C carries 0.10 bpp of encrypted payload.")

# T2 robustness
rows = []
for a in rb.attack.unique():
    r = {"Attack": a}
    if a in MEAN_NCC: r["Base paper NCC (reported)"] = round(MEAN_NCC[a], 4)
    for cfg in ["A", "A*", "B", "C"]:
        d = rb[(rb.config == cfg) & (rb.attack == a)]
        r[f"{cfg} NCC"] = round(d.ncc.mean(), 3); r[f"{cfg} BER %"] = round(d.ber.mean() * 100, 1)
        r[f"{cfg} QR ok"] = f"{int(d.decodes.sum())}/12"
    d = rb[(rb.config == "C") & (rb.attack == a)]
    r["C payload BER"] = round(d.payload_ber.mean(), 3); r["C message ok"] = f"{int(d.msg_ok.sum())}/12"
    rows.append(r)
table(pd.DataFrame(rows), "Table 2: Robustness under attacks",
      f"Mean over 12 images. NCC of the extracted watermark from a never-watermarked image (JPEG-90 of the cover): {bl.ncc.mean():.3f} (BER {bl.ber.mean()*100:.1f}%, decodes {int(bl.decodes.sum())}/12).")

# T3 hidden layer
st = pd.read_csv(ROOT / "exp1_3_stego.csv"); rs = pd.read_csv(OUT / "steganalysis_rs_chi2.csv")
pe = pd.read_csv(ROOT / "exp2_steganalysis_prelim.csv")
g = st.groupby(["bpp", "method"]).agg(PSNR_RGB=("psnr_rgb", "mean"), PSNR_G=("psnr_g", "mean"),
        hist_chi2=("chi2_dist", "mean"), recovered=("msg_recovered", "sum")).reset_index()
g = g.merge(rs.groupby(["bpp", "method"]).rs_est.mean().rename("RS estimate").reset_index(), how="left")
g = g.merge(pe[["bpp", "method", "pe_mean"]].rename(columns={"pe_mean": "P_E (SPAM)"}), how="left")
table(g.round(3), "Table 3: Hidden layer capacity and detectability",
      "11 images (exp1_3_stego.csv) for PSNR/chi2/recovery; RS on 12 images; P_E preliminary (494 patches). RS estimate on covers alone: %.3f." % rs[rs.method == 'cover'].rs_est.mean())

# T4 security
sec = pd.read_csv(ROOT / "exp5_security.csv"); dif = pd.read_csv(ROOT / "exp5_differential.csv", index_col=0).iloc[:, 0]
t4 = sec.round(4); table(t4, "Table 4: Security metrics",
      "Differential/key tests: " + "; ".join(f"{k} = {v:.4f}" for k, v in dif.items()))

# T5 timing
tm = imp.groupby("config").t_embed.mean(); tx = rb.groupby("config").t_extract.mean()
table(pd.DataFrame({"Config": tm.index, "Embed (s)": tm.round(3).values, "Extract (s)": tx.round(3).values}),
      "Table 5: Execution time", "Python, single thread, cloud container; includes key/file I/O.")
(OUT.parent / "tables.md").write_text("\n".join(md))
print("ok")
