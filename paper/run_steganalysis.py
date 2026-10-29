"""Classical LSB steganalysis of the green channel: RS analysis (Fridrich et al. 2001)
and the Westfeld-Pfitzmann chi-square pairs-of-values attack (2000).
Cover = Config A watermarked image (green untouched); stego = Config C at each bpp."""
import numpy as np, pandas as pd
from scipy.stats import chi2 as chi2dist
from pipeline import *

def _flip(x, mask, neg=False):
    y = x.copy()
    for j, m in enumerate(mask):
        if m == 0: continue
        if not neg: y[:, j] = y[:, j] ^ 1                       # F1: 0<->1, 2<->3
        else:       y[:, j] = ((y[:, j] + 1) ^ 1) - 1           # F-1: -1<->0, 1<->2
    return y

def _rs(groups, mask):
    f = lambda g: np.abs(np.diff(g, axis=1)).sum(1)
    f0 = f(groups)
    fp, fn = f(_flip(groups, mask)), f(_flip(groups, mask, True))
    n = len(groups)
    return (fp > f0).sum() / n, (fp < f0).sum() / n, (fn > f0).sum() / n, (fn < f0).sum() / n

def rs_estimate(ch, mask=(0, 1, 1, 0)):
    g = ch.astype(np.int32).reshape(-1, 4)
    Rm, Sm, Rn, Sn = _rs(g, mask)
    Rm1, Sm1, Rn1, Sn1 = _rs(g ^ 1, mask)
    d0, d1, dn0, dn1 = Rm - Sm, Rm1 - Sm1, Rn - Sn, Rn1 - Sn1
    a, b, c = 2 * (d1 + d0), (dn0 - dn1 - d1 - 3 * d0), d0 - dn0
    roots = np.roots([a, b, c]); roots = roots[np.isreal(roots)].real
    if roots.size == 0: return np.nan
    x = roots[np.argmin(np.abs(roots))]
    return float(np.clip(x / (x - 0.5), 0, 1))         # estimated fraction of pixels carrying a bit

def chi2_pov(ch):
    h = np.bincount(ch.ravel(), minlength=256).astype(float)
    even, odd = h[0::2], h[1::2]
    exp = (even + odd) / 2; k = exp > 4
    stat = (((even[k] - exp[k]) ** 2) / exp[k]).sum()
    return float(1 - chi2dist.cdf(stat, k.sum() - 1))  # p ~ 1 => looks like full LSB embedding

rows = []
for name in IMAGES:
    wm, *_ = embed(name, "A")
    G0 = wm[..., 1]
    rows.append(dict(image=name, bpp=0.0, method="cover", rs_est=rs_estimate(G0), chi2_p=chi2_pov(G0)))
    for bpp in [0.05, 0.1, 0.2, 0.3, 0.4]:
        bits = payload_bits(int(bpp * G0.size))
        for method in ["adaptive", "random"]:
            Gs, _ = lsb_embed(G0, bits, method)
            rows.append(dict(image=name, bpp=bpp, method=method,
                             rs_est=rs_estimate(Gs), chi2_p=chi2_pov(Gs)))
    print(name, flush=True)
df = pd.DataFrame(rows); df.to_csv(OUT / "steganalysis_rs_chi2.csv", index=False)
print(df.groupby(["method", "bpp"])[["rs_est", "chi2_p"]].agg(["mean", "std"]).round(3))
