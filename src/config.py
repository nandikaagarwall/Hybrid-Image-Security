"""
Single source of truth for every fixed parameter in the experiments.
Change a value here, never inside individual scripts, so both tracks
always run with identical settings. Record any change in the README log.
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
LOGISTIC_R = 3.99                 # must be in (3.57, 4] for chaotic behaviour
LOGISTIC_X0 = 0.3141592653589793  # initial condition = part of the key
LOGISTIC_DISCARD = 1000           # drop transient iterations

# ---------- base paper embedding strength (Config A) ----------
ALPHA_FIXED = 0.05                # TUNE in Step A3 until PSNR lands in 40-44 dB, then freeze

# ---------- adaptive strength (Config B) ----------
BLOCK = 8                         # block size on the LL band
ALPHA_MIN = 0.02
ALPHA_MAX = 0.10

# ---------- hidden payload (Config C) ----------
PAYLOAD_BPP = [0.05, 0.1, 0.2, 0.3, 0.4]   # capacity sweep (Experiment 3)
PAYLOAD_MESSAGE = "Confidential: project record #001. Sharing prohibited."

# ---------- attacks (parameters shared by both tracks) ----------
ATTACKS = {
    "none": {},
    "salt_pepper": {"density": [0.01, 0.05]},
    "gaussian": {"var": [0.001, 0.01]},
    "jpeg": {"quality": [90, 70, 50]},
    "crop": {"fraction": [0.25]},
    "rotation": {"degrees": [1, 5]},
    "scaling": {"factor": [0.5, 2.0]},
    "translation": {"pixels": [10]},
}

# ---------- steganalysis (Experiment 2) ----------
BOSS_SUBSET = 2000                # start with 2000, raise to 5000 if time allows
TRAIN_FRACTION = 0.5
