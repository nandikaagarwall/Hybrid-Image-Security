# Paper results package

Everything here is regenerated from the team's own code (`scripts/`, `src/`) by:

```
cd paper
python3 run_experiments.py      # robustness, sweeps, alpha trade-off  -> out/*.csv  (~10 min)
python3 run_steganalysis.py     # RS + chi-square on the green channel -> out/steganalysis_rs_chi2.csv
python3 figs_images.py; python3 figs_attacks.py; python3 figs_charts.py; python3 figs_compare_tables.py; python3 figs_correlation.py
```
Showcase image: Peppers (IEEE no longer accepts Lena). RSA keys for the runs are a fresh pair in `keys_experiment/` (do not commit the private key).

## Figures and draft captions (PNG for Word, PDF for LaTeX)

| File | Draft caption |
|---|---|
| fig01_visual_comparison | Cover and marked images (Peppers) with PSNR/SSIM. Bottom: absolute difference, ×10 for the blue (watermark) channel and ×255 for the green (hidden) channel, where every change is ±1. |
| fig02_histograms_embedded_channel | Histograms of the embedded channel only (cover in grey). Middle: zoom on values 100–123. Bottom: difference histogram (marked − cover). DWT-SVD spreads changes over ±30 with a slight positive bias; LSB embedding changes 5% of green pixels by exactly ±1. |
| fig03_scrambling_key_sensitivity | Plain QR, logistic-map scrambled QR, descrambled with the correct key and with x0 + 10⁻¹⁰. Adjacent-pixel correlations (H/V/D) under each. |
| fig04_embedding_map | Where the hidden bits go: texture-ranked 4×4 blocks (0.10 bpp) and the pixels actually changed. |
| fig05_attack_grid | Attacked images (top) and QR codes extracted with Config A and Config B, with BER and decodability (✓/✗). |
| fig06_ber_vs_attack_strength | Watermark BER vs attack strength (mean ± SD over 12 images). |
| fig07_alpha_tradeoff | Effect of global α: PSNR vs BER, and fraction of images whose QR still decodes. |
| fig08_hidden_layer | Hidden layer: green PSNR vs payload; RS steganalysis estimate vs true payload; SPAM detector error (preliminary). |
| fig10_adjacent_pixel_correlation | Adjacent-pixel correlation (horizontal, vertical, diagonal) of the embedded channels, cover vs Config C (Peppers). Scatter: 3,000 random pixel pairs at the same positions in every panel; r computed over all pixel pairs. |
| fig11_ownership_attack | False-ownership (ambiguity) attack. Top: Config A; an attacker's own U, V keys extract the attacker's QR from the owner's image. Bottom: Config D; extraction is blind, and the attacker's own signed certificate yields no QR, so the claim is rejected. |
| fig12_robustness_A_vs_D | Images (of 12) whose QR still decodes after each attack, Config A vs Config D at equal PSNR (~40 dB). |
| fig09_comparison_base_paper | NCC reported by the base paper vs our reproduction (A), adaptive (B) and combined (C); bottom: BER, which the base paper does not report. Red line: NCC obtained from an image that was never watermarked. |

Tables: `tables.md` (and `out/table_*.csv`).

## Config D: fixing the false-ownership flaw
`ownership.py`, `run_ownership_cfg.py`, `run_ownership.py`, `figs_ownership.py`.
- Embedding: each QR module bit sets the largest singular value of an 8x8 block of the blue LL band by QIM (step 205, chosen to match A's PSNR). Bit order scrambled with the logistic map (r, x0). QR = owner text + first 8 hex of SHA-256(owner RSA public key), error correction H.
- Extraction is blind (no cover, no U/V). Decoder: plain, 3x3 median, then grid re-synchronisation over shifts of up to 4 px.
- Certificate: {owner, key fingerprint, r, x0, step, block, QR size} signed with RSA-PSS/SHA-256. A claim is accepted only if the signature verifies, the key fingerprint matches, and the QR extracted with the certified parameters decodes to the certified text.
- Results: Tables 6 and 7 in tables.md. Ambiguity attack: A 12/12 succeed, D 0/12. Remaining limitations: an attacker who re-embeds their own Config D mark overwrites the owner's (needs a trusted timestamp on the certificate, e.g. RFC 3161); D is weaker than A under heavy Gaussian noise (v = 0.01: 3/12 vs 12/12); neither survives 2-degree rotation.

## Things to state honestly in the paper
- The "crop" attack blanks the central 1/4 × 1/4 of the image = 6.25% of the area, not 25%.
- NCC as defined in the base paper is not centred: an image that was never watermarked still scores 0.43, so BER and QR decodability are the more meaningful robustness numbers.
- Our reproduction of the base scheme does not reach the base paper's reported NCC for blur, scaling, rotation and cropping (their attack sizes are partly unstated; their S&P density is stated as 0.5).
- AES-CBC NPCR is 99.60% for a change in the first byte but 0.02% for a change in the last byte (CBC propagates forward only). The 7.9975 entropy is measured on 64 KiB of ciphertext, not the 64-byte message.
- The hidden layer does not survive any lossy attack (payload BER ≈ 0.5), as expected for spatial LSB.
- `run_combined.py`/`configC_combined.csv` and `experiments/generate_phase2_artifacts.py` do not run the real pipeline (random noise / hard-coded numbers) and must not be used.
