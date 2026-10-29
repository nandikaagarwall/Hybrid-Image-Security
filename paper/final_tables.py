"""Final publication tables (A vs PROPOSED). Writes paper/final/tables/T*.md and T*.tex."""
import json
import numpy as np, pandas as pd
from pathlib import Path
from base_paper import MEAN_NCC, PSNR_NO_ATTACK
OUT = Path(__file__).resolve().parent / "out"; TD = OUT.parent / "final" / "tables"; TD.mkdir(parents=True, exist_ok=True)
ms = lambda s, d=2: f"{s.mean():.{d}f} ± {s.std(ddof=1):.{d}f}"
B = lambda s: f"**{s}**"

def write(stem, df, caption, note=""):
    md = f"**{caption}**\n\n" + df.to_markdown(index=False) + (f"\n\n{note}" if note else "")
    (TD / f"{stem}.md").write_text(md)
    tex = df.copy().astype(str).replace({r"\*\*(.*?)\*\*": r"\\textbf{\1}"}, regex=True)
    tex = tex.apply(lambda c: c.str.replace("%", r"\%").str.replace("±", r"$\pm$").str.replace("&", r"\&")
                    .str.replace("✓", r"\checkmark").str.replace("✗", r"$\times$").str.replace("≈", r"$\approx$"))
    cols = [c.replace("%", r"\%").replace("&", r"\&") for c in df.columns]
    body = " \\\\\n".join(" & ".join(r) for r in tex.values.tolist())
    (TD / f"{stem}.tex").write_text(
        "\\begin{table}[t]\n\\centering\n\\small\n\\caption{" + caption.split(". ", 1)[-1] + "}\n"
        "\\begin{tabular}{" + "l" + "c" * (len(cols) - 1) + "}\n\\toprule\n" + " & ".join(cols) + " \\\\\n\\midrule\n"
        + body + " \\\\\n\\bottomrule\n\\end{tabular}\n" + (f"\\\\[2pt]\\footnotesize {note}\n" if note else "") + "\\end{table}\n")
    return md

rA = pd.read_csv(OUT / "robustness.csv"); rA = rA[rA.config == "A"]
iA = pd.read_csv(OUT / "imperceptibility.csv"); iA = iA[iA.config == "A"].set_index("image")
iP = pd.read_csv(OUT / "final_imperceptibility_P.csv").set_index("image")
rP = pd.read_csv(OUT / "final_robustness_P.csv")
base = dict(zip(["house", "tree", "girl", "mandrill", "lena", "airplane", "lake", "peppers", "house2", "einstein", "monalisa", "boat"], PSNR_NO_ATTACK))
NAMES = {"house2": "House 2", "monalisa": "Mona Lisa"}
nm = lambda s: NAMES.get(s, s.capitalize())

# ---------------- T2 imperceptibility ----------------
rows = []
for im in iP.index:
    rows.append([nm(im), f"{base[im]:.2f}", f"{iA.psnr[im]:.2f}", f"{iA.ssim[im]:.4f}", f"{iP.psnr[im]:.2f}", f"{iP.ssim[im]:.4f}",
                 f"{iP.psnr_B[im]:.2f}", f"{iP.psnr_G[im]:.2f}"])
bp = pd.Series(list(base.values()))
rows.append(["**Mean ± SD**", B(ms(bp)), B(ms(iA.psnr)), B(ms(iA.ssim, 4)), B(ms(iP.psnr)), B(ms(iP.ssim, 4)), B(ms(iP.psnr_B)), B(ms(iP.psnr_G))])
T2 = pd.DataFrame(rows, columns=["Image", "Base paper PSNR (reported)", "A PSNR (dB)", "A SSIM", "Proposed PSNR (dB)", "Proposed SSIM",
                                 "Proposed blue PSNR (dB)", "Proposed green PSNR (dB)"])
write("T2_imperceptibility", T2, "Table 2. Imperceptibility of the marked images (12 images).",
      "PSNR/SSIM of the whole colour image against the cover. The proposed image carries both the watermark (blue) and a 0.10 bpp encrypted message (green); red is untouched. Base-paper values from its Table 2.")

# ---------------- T3 robustness ----------------
order = [a for a in rP.attack.unique() if a != "No attack"]
rows = []
for a in ["No attack"] + order:
    da, dp = rA[rA.attack == a], rP[rP.attack == a]
    ka, kp = int(da.decodes.sum()), int(dp.decodes.sum())
    fa, fp = (B if ka > kp else str), (B if kp > ka else str)
    rows.append([a, f"{dp.psnr.mean():.2f}" if a != "No attack" else "–",
                 fa(f"{ka}/12"), f"{da.ber.mean()*100:.1f}", f"{da.ncc.mean():.3f}",
                 fp(f"{kp}/12"), f"{dp.module_ber.mean()*100:.1f}", f"{dp.ncc.mean():.3f}",
                 f"{int(dp.owner_claim.sum())}/12", f"{int(dp.msg_ok.sum())}/12"])
T3 = pd.DataFrame(rows, columns=["Attack", "Attacked PSNR (dB)", "A: QR decodes", "A: BER %", "A: NCC",
                                 "Proposed: QR decodes", "Proposed: BER %", "Proposed: NCC", "Proposed: ownership verified", "Hidden message recovered"])
write("T3_robustness", T3, "Table 3. Robustness of the watermark and the hidden message under attack (12 images; bold = more images decoded).",
      "BER for A is over QR pixels (256 × 256), for the proposed scheme over QR modules (29 × 29). NCC as defined in the base paper; an image that was never watermarked scores 0.43 with A's extractor. Ownership verified = certificate signature valid and extracted QR equals the certified text.")

# ---------------- T4 hidden layer ----------------
st = pd.read_csv(OUT.parent.parent / "exp1_3_stego.csv"); rs = pd.read_csv(OUT / "steganalysis_rs_chi2.csv")
pe = pd.read_csv(OUT.parent.parent / "exp2_steganalysis_prelim.csv")
rows = []
for bpp in [0.05, 0.1, 0.2, 0.3, 0.4]:
    s = st[(st.bpp == bpp) & (st.method == "adaptive")]
    rso, rsr = rs[(rs.bpp == bpp) & (rs.method == "adaptive")].rs_est, rs[(rs.bpp == bpp) & (rs.method == "random")].rs_est
    peo, per = pe[(pe.bpp == bpp) & (pe.method == "adaptive")].pe_mean, pe[(pe.bpp == bpp) & (pe.method == "random")].pe_mean
    rows.append([f"{bpp:.2f}", f"{int(bpp * 262144):,}", f"{s.psnr_g.mean():.2f}", f"{s.psnr_rgb.mean():.2f}", f"{int(s.msg_recovered.sum())}/{len(s)}",
                 B(f"{rso.mean():.3f}"), f"{rsr.mean():.3f}",
                 (B(f"{peo.iloc[0]:.3f}") if len(peo) else "–"), (f"{per.iloc[0]:.3f}" if len(per) else "–")])
T4 = pd.DataFrame(rows, columns=["Payload (bpp)", "Bits", "Green PSNR (dB)", "RGB PSNR (dB)", "Message recovered",
                                 "RS estimate: ours", "RS estimate: random LSB", "P_E: ours", "P_E: random LSB"])
write("T4_hidden_layer", T4, "Table 4. Hidden-layer capacity and detectability (texture-ranked LSB vs random LSB).",
      f"RS estimate = embedding rate inferred by RS steganalysis (closer to the true payload = easier to detect; on covers: {rs[rs.method=='cover'].rs_est.mean():.3f}). P_E = detection error of a SPAM-686 + random-forest detector (0.5 = undetectable; preliminary, 494 patches). Actual message: 340 bytes = 2,720 bits; padded with random bits to the stated payload.")

# ---------------- T5 security metrics ----------------
sec = pd.read_csv(OUT.parent.parent / "exp5_security.csv").set_index("item"); dif = pd.read_csv(OUT.parent.parent / "exp5_differential.csv", index_col=0).iloc[:, 0]
own = pd.read_csv(OUT / "ownership_tests.csv")
bf = own[own.test.str.startswith("Random logistic")].reason.iloc[0]
T5 = pd.DataFrame([
    ["AES-256-CBC ciphertext", "Entropy (bits/byte)", f"{sec.entropy['AES-256-CBC ciphertext (payload)']:.4f}", "8"],
    ["AES-256-CBC ciphertext", "χ² of byte histogram", f"{sec.chi2['AES-256-CBC ciphertext (payload)']:.1f}", "< 293.25 (α = 0.05)"],
    ["AES-256-CBC ciphertext", "Adjacent-byte correlation H / V / D", f"{sec.corr_h['AES-256-CBC ciphertext (payload)']:.3f} / {sec.corr_v['AES-256-CBC ciphertext (payload)']:.3f} / {sec.corr_d['AES-256-CBC ciphertext (payload)']:.3f}", "0"],
    ["AES-256-CBC ciphertext", "NPCR / UACI, 1-bit change in first byte", f"{dif['npcr_aes_first_byte']:.2f}% / {dif['uaci_aes_first_byte']:.2f}%", "99.61% / 33.46%"],
    ["AES-256-CBC ciphertext", "Bytes changed by a 1-bit change in the AES key", f"{dif['aes_wrongkey_bytes_differ_pct']:.2f}%", "≈ 99.6%"],
    ["Logistic-map scrambling (base scheme QR)", "Adjacent-pixel correlation H / V / D, plain → scrambled",
     f"{sec.corr_h['Plain QR (watermark)']:.3f} → {sec.corr_h['Scrambled QR (logistic map)']:.3f} / {sec.corr_v['Plain QR (watermark)']:.3f} → {sec.corr_v['Scrambled QR (logistic map)']:.3f} / {sec.corr_d['Plain QR (watermark)']:.3f} → {sec.corr_d['Scrambled QR (logistic map)']:.3f}", "→ 0"],
    ["Logistic-map key", "Watermark BER with x0 changed by 10⁻¹⁰", f"{dif['logistic_wrong_x0_ber']:.3f}", "0.5"],
    ["Proposed watermark key", "Random (r, x0) keys that yield any decodable QR", f"{bf} of 300", "0"],
], columns=["Component", "Metric", "Value", "Ideal"])
write("T5_security", T5, "Table 5. Security of the encryption and scrambling components.",
      "AES metrics on 64 KiB of ciphertext (the 64-byte message alone is too short for byte statistics). NPCR for a change in the LAST byte is 0.02%, as expected for CBC, which propagates changes forward only.")

# ---------------- T6 ownership ----------------
fp = pd.read_csv(OUT.parent.parent / "sanity_false_positive.csv")
g = own[own.accepted.notna()].groupby("test").accepted.apply(lambda x: f"{int((x == True).sum())}/{len(x)}")
T6 = pd.DataFrame([
    ["Real owner claims the marked image", "12/12", g["Legitimate owner on marked image"], "accept"],
    ["Attacker presents their own keys (false-ownership attack)", f"{int(fp.attacker_decodes.sum())}/12", B(g["Attacker's own certificate on our image (ambiguity attack)"]), "reject"],
    ["Owner's certificate with the owner name edited", "no certificate", g["Our certificate, owner field edited"], "reject"],
    ["Owner's parameters re-signed with the attacker's key", "no certificate", g["Our parameters re-signed with attacker's key"], "reject"],
    ["Owner's claim on an image never watermarked", f"{int(fp.unmarked_decodes.sum())}/12", g["Owner certificate on unmarked cover"], "reject"],
    ["Same, after JPEG-90", "–", g["Owner certificate on unmarked cover, JPEG-90"], "reject"],
    ["Attacker re-watermarks the image with their own mark", "–", f"attacker {g['Overwrite attack: attacker claim on re-marked image']}, owner {g['Overwrite attack: owner claim on re-marked image']}", "needs trusted timestamp"],
], columns=["Claim", "Base scheme (A): accepted", "Proposed: accepted", "Correct outcome"])
write("T6_ownership", T6, "Table 6. Ownership-verification tests (12 images each).",
      "The overwrite attack is not prevented by any blind scheme alone; the standard remedy is a trusted timestamp on the signed certificate (first registration wins).")

# ---------------- T7 comparison ----------------
cmp_atk = ["JPEG Q=90", "Gaussian v=0.01", "Salt&Pepper d=0.01", "Avg blur 3x3", "Scaling 0.5x->1x", "Rotation 2 deg", "Translation 2 px"]
short = {"JPEG Q=90": "JPEG 90", "Gaussian v=0.01": "Gauss 0.01", "Salt&Pepper d=0.01": "S&P", "Avg blur 3x3": "Blur 3×3",
         "Scaling 0.5x->1x": "Scale 0.5", "Rotation 2 deg": "Rot. 2°", "Translation 2 px": "Shift 2 px"}
row = lambda name, psnr, ncc, blind, own_: [name, psnr] + [f"{ncc[a]:.3f}" if a in ncc else "–" for a in cmp_atk] + [blind, own_]
T7 = pd.DataFrame([
    row("Sanivarapu et al. 2022 (as reported)", f"{np.mean(PSNR_NO_ATTACK):.2f}", MEAN_NCC, "no", "not evaluated"),
    row("Same scheme, our reproduction (A)", f"{iA.psnr.mean():.2f}", rA.groupby("attack").ncc.mean().to_dict(), "no", "fails (12/12)"),
    row("**Proposed**", f"{iP.psnr.mean():.2f}", rP.groupby("attack").ncc.mean().to_dict(), "yes", "passes (0/12)"),
    ["[Paper 2 — to add]"] + [""] * (len(cmp_atk) + 3),
    ["[Paper 3 — to add]"] + [""] * (len(cmp_atk) + 3),
], columns=["Method", "PSNR (dB)"] + [f"NCC: {short[a]}" for a in cmp_atk] + ["Blind extraction", "False-ownership attack"])
write("T7_comparison", T7, "Table 7. Comparison with the base paper (mean NCC over 12 images).",
      "Base-paper attack sizes for cropping and rotation are not stated, and its salt & pepper density is stated as 0.5; our settings are in Table 1. Centre blanking is omitted here for that reason (see Table 3).")

# ---------------- T8 timing ----------------
T8 = pd.DataFrame([["Base scheme (A)", f"{iA.t_embed.mean():.3f}", f"{rA.t_extract.mean():.3f}", "cover image + U, V matrices (2 × 256 × 256 floats)"],
                   ["Proposed", f"{iP.t_embed.mean():.3f}", f"{rP.t_extract.mean():.3f}", "signed certificate (< 1 KB) + RSA private key for the message"]],
                  columns=["Scheme", "Embed (s)", "Extract (s)", "What the verifier needs"])
write("T8_cost", T8, "Table 8. Computational cost and key material.",
      "Mean over 12 images, Python on a single CPU core. Proposed extract time includes the hidden message and certificate check; it rises when the decoder has to search for a shift.")
print("tables ok")
