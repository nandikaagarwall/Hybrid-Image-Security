"""Image loading / saving helpers. Everyone loads images through these."""
import cv2
import numpy as np
from . import config as C

EXTS = {".png", ".tif", ".tiff", ".bmp", ".jpg", ".jpeg", ".pgm", ".ppm"}


def load_rgb(path, size=C.IMG_SIZE):
    """Load any image as uint8 RGB, size x size. Never returns BGR."""
    img = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    if img.shape[:2] != (size, size):
        img = cv2.resize(img, (size, size), interpolation=cv2.INTER_AREA)
    return img


def load_gray(path):
    img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(path)
    return img


def save_rgb(img, path):
    """Always save as PNG (lossless). Saving as JPG silently destroys embedded bits."""
    path = str(path)
    assert path.lower().endswith(".png"), "save results as .png only"
    cv2.imwrite(path, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))


def standard_images():
    """Sorted list of the standard test images in data/standard/."""
    files = sorted(p for p in C.DATA_STD.iterdir() if p.suffix.lower() in EXTS)
    return files


def bossbase_images(n=C.BOSS_SUBSET):
    files = sorted(p for p in C.DATA_BOSS.iterdir() if p.suffix.lower() in EXTS)
    return files[:n]


def to_uint8(x):
    return np.clip(np.round(x), 0, 255).astype(np.uint8)
