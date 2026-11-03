# Hybrid Image Security

Encryption + steganography + DWT-SVD watermarking on one colour image, evaluated against the base paper:

> P. V. Sanivarapu, K. N. V. P. S. Rajesh, K. M. Hosny and M. M. Fouda, "Digital Watermarking System for Copyright Protection and Authentication of Images Using Cryptographic Techniques," *Applied Sciences* 12(17):8724, 2022. https://doi.org/10.3390/app12178724

Nandika Agarwal, Pranalee Patel · NIIT University

## What the system does

One 512 × 512 colour image carries two independent layers in two channels, so neither can overwrite the other:

| Layer | Channel | How |
|---|---|---|
| Ownership watermark (proposed) | Blue | Owner text + fingerprint of the owner's RSA public key → 29 × 29 QR (error correction H) → bits scrambled with a logistic map → each bit set by QIM on the largest singular value of an 8 × 8 block of the 1-level Haar DWT LL band (1,024 blocks, step 183). **Blind extraction**: needs no cover image and no U/V matrices. |
| Ownership certificate | – | Owner, key fingerprint, logistic key and embedding settings, signed with RSA-PSS/SHA-256. A claim is accepted only if the signature verifies and the QR read from the image matches the certificate. |
| Hidden message | Green | AES-256-CBC message, AES key wrapped with RSA-2048-OAEP, embedded by LSB in the most textured 4 × 4 blocks. |

The **base scheme (A)** is the base paper reproduced: 256 × 256 QR, logistic-map scrambling, S′ = S + α·S_QR on the blue LL band (α = 0.05), non-blind extraction with the QR's U, V matrices.

## Headline results (12 images, equal PSNR)

| | Base scheme (A) | Proposed |
|---|---|---|
| PSNR / SSIM | 40.12 dB / 0.994 | 40.19 dB / 0.991 (watermark **and** hidden message) |
| False-ownership attack accepted | 12/12 | **0/12** |
| QR decodes after JPEG-70 / JPEG-50 | 8/12 / 8/12 | **12/12 / 12/12** |
| … after 3 × 3 blur / scaling / centre blanking | 1 / 2 / 0 of 12 | **11 / 11 / 12 of 12** |
| … after Gaussian noise v = 0.01 / salt & pepper | **12 / 12 of 12** | 0 / 9 of 12 |
| … after 2° rotation | 0/12 | 0/12 |
| Extraction | non-blind | blind |

All figures and tables for the paper are in [`paper/final/`](paper/final/) (Tables 2–8 as Markdown and LaTeX).

## Repository layout

```
src/                      core library
  payload.py              AES-256-CBC + RSA-2048-OAEP hybrid encryption, bit packing
  stego.py                texture-ranked LSB embedding (4 x 4 block variance on the top 6 bits)
  metrics.py              PSNR, SSIM, NCC, BER, entropy, chi-square, correlation, NPCR/UACI, P_E
  config.py, io_utils.py  shared paths and reference values
scripts/                  base-scheme building blocks (used by the paper pipeline)
  watermark_prep.py       QR generation + logistic-map scrambling
  embed_watermark.py      Config A embedding (global alpha)
  embed_watermark_adaptive.py / extract_watermark_adaptive.py   Config B (adaptive alpha, ablation only)
  extract_watermark.py, evaluate_watermark.py, attacks.py
  make_keys.py, check_setup.py, download_images.py
paper/                    everything behind the paper's results
  ownership.py            PROPOSED watermark: blind block-SVD QIM + RSA-signed certificate
  pipeline.py             shared wrapper around src/ and scripts/ (images, attacks, hidden layer)
  run_ownership_cfg.py    proposed-scheme parameters, keys and certificate
  run_baseline_watermark.py   Configs A / A* / B on 12 images + false-ownership sanity check
  run_hidden_layer.py     hidden-layer capacity, encryption metrics, SPAM steganalysis
  run_experiments.py      A / A* / B / C robustness, attack-strength sweeps, alpha trade-off
  run_steganalysis.py     RS analysis + chi-square attack on the green channel
  run_ownership.py        ownership-claim tests (12 images)
  run_final.py            PROPOSED system end to end: robustness, sweeps, trade-off
  final_tables.py, figs_final.py   build paper/final/
  base_paper.py           the base paper's reported values (its Tables 2-4)
  out/                    raw results (CSV) of every run above
  final/                  paper figures F01-F10 (PNG + PDF) and tables/ (Markdown + LaTeX)
data/images/              the 12 test images (512 x 512 x 3)
data/standard/            extra standard images, used only as steganalysis training patches
keys/rsa_public.pem       project public key (the private key is never committed)
tests/                    unit tests for the hidden layer
```

## Setup

Python 3.11+.

```
pip install -r requirements.txt
sudo apt install libzbar0        # Ubuntu; macOS: brew install zbar; Windows: nothing extra
python scripts/check_setup.py
python -m pytest tests
```

The paper scripts create their own experiment RSA key pair in `paper/keys_experiment/` on first run (git-ignored).

## Reproducing the results

Run from the repository root, in this order (times are for one CPU core):

```
python paper/run_baseline_watermark.py   # ~5 min   -> paper/out/exp1_watermark*.csv, sanity_false_positive.csv
python paper/run_hidden_layer.py         # ~10 min  -> paper/out/exp1_3_stego.csv, exp5_*.csv, exp2_steganalysis_prelim.csv
python paper/run_experiments.py          # ~10 min  -> paper/out/robustness.csv, sweeps.csv, alpha_tradeoff.csv, ...
python paper/run_steganalysis.py         # ~1 min   -> paper/out/steganalysis_rs_chi2.csv
python paper/run_ownership.py            # ~10 min  -> paper/out/ownership_tests.csv, robustness_D.csv
python paper/run_final.py                # ~15 min  -> paper/out/final_*.csv
python paper/final_tables.py             # -> paper/final/tables/
python paper/figs_final.py               # -> paper/final/F01-F10
```

`run_baseline_watermark.py` and `run_hidden_layer.py` write to `paper/out/` and should be run from the repository root.

## Results to report with care

- **Centre blanking** zeroes the central 1/4 × 1/4 of the image, i.e. 6.25% of its area.
- **NCC** as defined in the base paper is not centred: an image that was never watermarked scores 0.43 with the base extractor. QR decodability and BER are the more meaningful robustness measures.
- **Reproduction gap:** our reproduction of the base scheme does not reach the base paper's reported NCC under blur, scaling and rotation. The base paper does not state its crop or rotation sizes and gives its salt & pepper density as 0.5.
- **AES metrics** (entropy 7.9975, χ² 227.9) are measured on 64 KiB of ciphertext; the 64-byte message alone is too short for byte statistics. NPCR for a change in the last byte is 0.02% (CBC propagates forward only).
- **Limitations:** the proposed watermark is weaker than the base scheme under heavy additive noise at 40 dB (it reaches 12/12 at 37.7 dB); neither scheme survives rotation; an attacker can overwrite a blind mark with their own (needs a trusted timestamp on the certificate); the LSB hidden message survives only lossless (PNG) sharing; the SPAM steganalysis result is preliminary (494 patches); logistic-map scrambling is a permutation and is breakable by chosen-plaintext attack, so secrecy rests on AES/RSA.
- **Lena:** IEEE no longer accepts papers containing the Lena image; the figures use Peppers.

## Decision log

| Decision | Reason |
|---|---|
| Watermark in blue, hidden message in green, red untouched | The two layers can never overwrite each other |
| 1-level Haar DWT, LL band | As in the base paper |
| 12 test images as in the base paper's Table 2 | Direct comparison; "monarch.png" is the fishing-boat image, reported as Boat |
| AES-256-CBC + RSA-2048-OAEP for the message | RSA alone cannot encrypt long messages; random key and IV per message |
| Texture-ranked LSB, ranking on the top 6 bits | Changes hide in busy areas; the receiver can recompute the same ranking |
| Base scheme kept at α = 0.05 | As published; gives PSNR ≈ 40 dB |
| Config B (adaptive α) dropped from the main results | It lowered PSNR and robustness to JPEG/noise; kept in `paper/out/robustness.csv` as an ablation |
| Proposed watermark: blind QIM + RSA-signed certificate | The base scheme accepts false ownership claims (12/12): its verifier uses keys the claimant supplies |
| QIM step 183 | Matches the base scheme's PSNR (≈ 40 dB) for an equal-quality comparison |
| QR text = short owner name + 8-hex key fingerprint, error correction H | Must fit 1,024 blocks (29 × 29 = 841 modules) and still decode after attacks |
| Showcase image: Peppers | IEEE policy on Lena |

The pre-cleanup state of the repository (including the Phase 0/1 setup guide) is preserved on the branch `archive/original-main`.
