import json, numpy as np, pandas as pd, cv2, matplotlib.pyplot as plt
from pipeline import *
import ownership as O
from style import COL, NAME, save
from run_ownership_cfg import *          # shared parameters (no re-run)

SHOW = "peppers"; cover = load(SHOW)
# --- Config A ambiguity attack (as in run_watermark.py sanity check) ---
A, keyA, fnA, kwA = embed(SHOW, "A")
qr_atk = generate_qr_code("Author: Attacker, Country: Nowhere")
scr_atk, _ = chaotic_logistic_map_scramble(qr_atk, x0=X0, mu=MU)
U2, S2, V2 = np.linalg.svd(scr_atk.astype(float), full_matrices=False)
np.savez(TMP / "atk.npz", U=U2, S=S2, V=V2)
exA_atk = descramble(extract_config_a(A, cover, str(TMP / "atk.npz"), alpha=0.05))
exA_own = descramble(extract_config_a(A, cover, keyA, alpha=0.05))
# --- Config D ---
D = O.embed_D(cover, m_own, X0_OWN, R_OWN, STEP, BLKD)
_, mD_own = O.extract_and_decode(D, m_own.shape, X0_OWN, R_OWN, STEP, BLKD)
mD_atk = O.extract_D(D, m_atk.shape, X0_ATK, R_ATK, STEP, BLKD)
okA = test_qr_decodability(exA_atk)
fig, ax = plt.subplots(2, 3, figsize=(7.2, 4.9))
panels = [
  (exA_own, f"Owner's key\nQR decodes: {'yes' if test_qr_decodability(exA_own) else 'no'}"),
  (exA_atk, f"Attacker's own U, V keys\nQR decodes: {'YES — false claim succeeds' if okA else 'no'}"),
  (cv2.cvtColor(A, cv2.COLOR_BGR2RGB), f"Base scheme (A) image\nPSNR {calculate_psnr(cover, A):.2f} dB"),
  (O.modules_to_image(mD_own), "Owner's certificate\nQR decodes, signature valid → accepted"),
  (O.modules_to_image(mD_atk), "Attacker's own signed certificate\nno QR → rejected"),
  (cv2.cvtColor(D, cv2.COLOR_BGR2RGB), f"Proposed image\nPSNR {calculate_psnr(cover, D):.2f} dB")]
for a, (im, t) in zip(ax.ravel(), panels):
    a.imshow(im, cmap="gray" if im.ndim == 2 else None, vmin=0, vmax=255, interpolation="nearest")
    a.set_title(t, fontsize=7.5, color="#b3261e" if "YES" in t else "#1f1f1d")
    a.set_xticks([]); a.set_yticks([]); a.grid(False)
ax[0, 0].set_ylabel("Base scheme (A)\nnon-blind, U/V keys", fontsize=8)
ax[1, 0].set_ylabel("Proposed\nblind + RSA certificate", fontsize=8)
fig.tight_layout(); save(fig, "fig11_ownership_attack")

# --- robustness: A vs D at equal PSNR ---
ra = pd.read_csv(OUT / "robustness.csv"); rd = pd.read_csv(OUT / "robustness_D.csv")
atks = [a for a in ATTACKS if a != "No attack"]
gA = ra[ra.config == "A"].groupby("attack").decodes.sum(); gD = rd.groupby("attack").decodes.sum()
fig, ax = plt.subplots(figsize=(7.2, 2.8))
x = np.arange(len(atks)); w = 0.38
ax.bar(x - w / 2, [gA[a] for a in atks], w * 0.92, color=COL["A"], label=f"A: base (non-blind), PSNR {ra[(ra.config=='A')&(ra.attack=='No attack')].psnr.mean():.1f} dB")
ax.bar(x + w / 2, [gD[a] for a in atks], w * 0.92, color="#7a5cd6", label=f"D: blind + RSA certificate, PSNR {rd[rd.attack=='No attack'].psnr.mean():.1f} dB")
for i, a in enumerate(atks):
    for dx, v in ((-w / 2, gA[a]), (w / 2, gD[a])):
        ax.text(i + dx, v + 0.2, str(int(v)), ha="center", fontsize=6.5, color="#4a4a46")
ax.set_xticks(x); ax.set_xticklabels([a.replace(" ", "\n", 1) for a in atks], fontsize=6.5)
ax.set_ylabel("images whose QR decodes (of 12)"); ax.set_ylim(0, 13.5)
ax.legend(frameon=False, ncol=2, loc="lower left", bbox_to_anchor=(0, 1.0), fontsize=7)
fig.tight_layout(); save(fig, "fig12_robustness_A_vs_D")
print("ok")

# --- tables ---
sec = pd.read_csv(OUT / "ownership_tests.csv")
t6 = sec[sec.accepted.notna()].groupby("test", sort=False).agg(
    accepted=("accepted", lambda x: f"{int((x == True).sum())}/{len(x)}"),
    reason=("reason", lambda x: ", ".join(sorted({str(v) for v in x if str(v) != "nan"})))).reset_index()
fp = pd.read_csv(ROOT / "sanity_false_positive.csv")
t6.loc[len(t6)] = ["Config A, same ambiguity attack (attacker's own U, V)", f"{int(fp.attacker_decodes.sum())}/12", "attacker's QR decodes"]
extra = sec[sec.accepted.isna()].groupby("test").reason.agg(lambda x: list(x))
note = "; ".join(f"{k}: {v[0] if len(v) == 1 else 'mean %.2f' % np.mean([float(i) for i in v])}" for k, v in extra.items())
t7 = pd.DataFrame({"Attack": atks, "A decodes": [f"{int(gA[a])}/12" for a in atks],
                   "D decodes": [f"{int(gD[a])}/12" for a in atks],
                   "D module BER %": [round(rd[rd.attack == a].module_ber.mean() * 100, 1) for a in atks]})
md = ["\n## Table 6: Ownership-claim tests (Config D)\n", t6.to_markdown(index=False), f"\n{note}\n",
      "\n## Table 7: Robustness, Config A vs Config D at equal PSNR\n", t7.to_markdown(index=False),
      f"\nMean PSNR: A {ra[(ra.config=='A')&(ra.attack=='No attack')].psnr.mean():.2f} dB, D {rd[rd.attack=='No attack'].psnr.mean():.2f} dB; SSIM D {rd[rd.attack=='No attack'].ssim.mean():.4f}.\n"]
tm = (OUT.parent / "tables.md").read_text()
tm = tm.split("\n## Table 6:")[0]
(OUT.parent / "tables.md").write_text(tm + "\n".join(md))
t6.to_csv(OUT / "table_table6.csv", index=False); t7.to_csv(OUT / "table_table7.csv", index=False)
print("tables ok")
