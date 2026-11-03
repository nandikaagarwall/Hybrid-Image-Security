"""
Shared paths and reference values for the project.

The paper experiments read their parameters from paper/pipeline.py (base scheme,
attacks, hidden layer) and paper/run_ownership_cfg.py (proposed watermark). The
values below are kept in step with those files; change both together.
"""
from pathlib import Path

# ---------- paths ----------
ROOT = Path(__file__).resolve().parent.parent
DATA_STD = ROOT / "data" / "standard"      # the 12 standard colour images
DATA_BOSS = ROOT / "data" / "bossbase"     # BOSSbase 1.01 .pgm files
KEYS = ROOT / "keys"
RESULTS = ROOT / "results"

# ---------- reproducibility ----------
SEED = 2026                       # numpy / random seed for everything

# ---------- image setup (matches base paper) ----------
IMG_SIZE = 512                    # host images resized/cropped to 512 x 512 x 3
QR_SIZE = 256                     # watermark = 256 x 256 QR (= size of LL band)
WATERMARK_CHANNEL = 2             # index in RGB order: 0=R, 1=G, 2=B  (blue, as base paper)
PAYLOAD_CHANNEL = 1               # hidden layer goes in green -> never collides with watermark
WAVELET = "haar"                  # one-level DWT; confirm against base paper and log it
DWT_LEVEL = 1

# ---------- watermark text (base paper: name + country) ----------
OWNER_TEXT = "Nandika Agarwal, Pranalee Patel | India | NIIT University"

# ---------- chaotic logistic map  x_{n+1} = r * x_n * (1 - x_n) ----------
LOGISTIC_R = 3.9999               # must be in (3.57, 4] for chaotic behaviour
LOGISTIC_X0 = 0.12345             # initial condition = part of the key
LOGISTIC_DISCARD = 0              # the implementation (scripts/watermark_prep.py) discards none

# ---------- base paper embedding strength (Config A) ----------
ALPHA_FIXED = 0.05                # as in the base paper; gives PSNR ~40.1 dB on the 12 images

# ---------- adaptive strength (Config B) ----------
BLOCK = 8                         # block size on the LL band
ALPHA_MIN = 0.01                  # as used in scripts/embed_watermark_adaptive.py
ALPHA_MAX = 0.15

# ---------- proposed watermark (paper/run_ownership_cfg.py) ----------
QIM_STEP = 183                    # QIM step on the largest singular value; PSNR ~40.2 dB
QIM_BLOCK = 8                     # 8 x 8 blocks of the 256 x 256 LL band -> 1,024 blocks
QR_ECC = "H"                      # QR error-correction level (29 x 29 modules)

# ---------- hidden payload (green channel) ----------
PAYLOAD_BPP = [0.05, 0.1, 0.2, 0.3, 0.4]   # capacity sweep (Experiment 3)
PAYLOAD_MESSAGE = "Confidential: project record #001. Sharing prohibited."

# ---------- attacks ----------
# The attack suite used in the paper is ATTACKS in paper/pipeline.py (12 settings).

# ---------- steganalysis (Experiment 2) ----------
BOSS_SUBSET = 2000                # start with 2000, raise to 5000 if time allows
TRAIN_FRACTION = 0.5
