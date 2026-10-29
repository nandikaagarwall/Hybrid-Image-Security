"""Final evaluation of the PROPOSED system (Config D watermark in blue + AES/RSA hidden layer in green)
against Config A (base paper). Writes paper/out/final_*.csv."""
import time
import numpy as np, pandas as pd
from run_ownership_cfg import *
from src import metrics as M

BPP = 0.10
QR_IMG = O.modules_to_image(m_own)
TXT = O.owner_qr_text(OWNER, owner_key.publickey())

def make_P(cover):
    t = time.perf_counter()
    D = O.embed_D(cover, m_own, X0_OWN, R_OWN, STEP, BLKD)
    bits = payload_bits(int(BPP * 512 * 512))
    G, _ = lsb_embed(D[..., 1], bits, "adaptive")
    P = D.copy(); P[..., 1] = G
    return P, bits, time.perf_counter() - t

def read_P(img, bits):
    t = time.perf_counter()
    txt, mm = O.extract_and_decode(img, m_own.shape, X0_OWN, R_OWN, STEP, BLKD)
    claim = O.verify_claim(img, cert_own, owner_key.publickey())[0] if txt == TXT else False
    ext = lsb_extract(img[..., 1], len(bits))
    msg = recover_message(ext) == MESSAGE
    return dict(decodes=txt is not None, owner_claim=claim, module_ber=float(np.mean(mm != m_own)),
                ncc=calculate_ncc(QR_IMG, O.modules_to_image(mm)), payload_ber=M.ber(bits, ext),
                msg_ok=msg, t_extract=time.perf_counter() - t)

# ---------- 1. imperceptibility + robustness ----------
imp, rob = [], []
for name in IMAGES:
    cover = load(name); P, bits, te = make_P(cover)
    imp.append(dict(image=LABEL.get(name, name), psnr=calculate_psnr(cover, P), ssim=calculate_ssim(cover, P),
                    psnr_B=calculate_psnr(cover[..., 0], P[..., 0]), psnr_G=calculate_psnr(cover[..., 1], P[..., 1]),
                    psnr_R=calculate_psnr(cover[..., 2], P[..., 2]), t_embed=te))
    for an in ATTACKS:
        atk = attack(an, P)
        rob.append(dict(image=LABEL.get(name, name), attack=an, psnr=calculate_psnr(cover, atk),
                        ssim=calculate_ssim(cover, atk), **read_P(atk, bits)))
    print("rob", name, flush=True)
pd.DataFrame(imp).to_csv(OUT / "final_imperceptibility_P.csv", index=False)
pd.DataFrame(rob).to_csv(OUT / "final_robustness_P.csv", index=False)

# ---------- 2. attack-strength sweeps (watermark only) ----------
SWEEPS = {
    "jpeg": ([100, 90, 80, 70, 60, 50, 40, 30], lambda im, q: apply_jpeg(im, q)),
    "gaussian": ([0.0005, 0.001, 0.002, 0.005, 0.01, 0.02], lambda im, v: apply_noise(im, "gaussian", v)),
    "saltpepper": ([0.005, 0.01, 0.02, 0.05, 0.1], lambda im, d: apply_noise(im, "sp", d)),
}
sw = []
for name in IMAGES:
    D = O.embed_D(load(name), m_own, X0_OWN, R_OWN, STEP, BLKD)
    for s, (levels, f) in SWEEPS.items():
        for lv in levels:
            np.random.seed(2026)
            txt, mm = O.extract_and_decode(f(D, lv), m_own.shape, X0_OWN, R_OWN, STEP, BLKD)
            sw.append(dict(config="P", image=name, sweep=s, level=lv, decodes=txt is not None,
                           module_ber=float(np.mean(mm != m_own))))
    print("sweep", name, flush=True)
pd.DataFrame(sw).to_csv(OUT / "final_sweeps_P.csv", index=False)

# ---------- 3. imperceptibility-robustness trade-off (QIM step) ----------
tr = []
for name in IMAGES:
    cover = load(name)
    for st in [120, 150, 180, 205, 240, 280, 330]:
        D = O.embed_D(cover, m_own, X0_OWN, R_OWN, st, BLKD)
        for an in ["JPEG Q=70", "Gaussian v=0.01", "Salt&Pepper d=0.01"]:
            txt, mm = O.extract_and_decode(attack(an, D), m_own.shape, X0_OWN, R_OWN, st, BLKD)
            tr.append(dict(image=name, step=st, psnr=calculate_psnr(cover, D), attack=an, decodes=txt is not None,
                           module_ber=float(np.mean(mm != m_own))))
    print("trade", name, flush=True)
pd.DataFrame(tr).to_csv(OUT / "final_step_tradeoff_P.csv", index=False)
print("done")
