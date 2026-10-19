"""
The CONTRACT between the two tracks. Agree on these signatures in Phase 0
and do not change them without telling your teammate.

Person A implements watermark.py (embed_watermark / extract_watermark).
Person B implements payload.py   (embed_payload  / extract_payload).

All images: numpy uint8, RGB, shape (512, 512, 3).
"""
import numpy as np


def embed_watermark(img: np.ndarray, qr: np.ndarray, key: dict,
                    adaptive: bool = False) -> tuple[np.ndarray, dict]:
    """Embed the QR watermark into the BLUE channel only.
    adaptive=False -> Config A (base paper), True -> Config B.
    Returns (watermarked_img, side_info) where side_info holds whatever the
    semi-blind extractor needs (e.g. stored singular vectors)."""
    raise NotImplementedError("Person A: implement in src/watermark.py")


def extract_watermark(img: np.ndarray, key: dict, side_info: dict) -> np.ndarray:
    """Return the extracted 256 x 256 QR (uint8, 0/255)."""
    raise NotImplementedError("Person A: implement in src/watermark.py")


def embed_payload(img: np.ndarray, bits: np.ndarray, key: dict,
                  method: str = "adaptive") -> np.ndarray:
    """Hide a 0/1 bit array in the GREEN channel only.
    method in {'adaptive', 'lsb_replacement'} (the second is the naive baseline)."""
    raise NotImplementedError("Person B: implement in src/payload.py")


def extract_payload(img: np.ndarray, n_bits: int, key: dict,
                    method: str = "adaptive") -> np.ndarray:
    raise NotImplementedError("Person B: implement in src/payload.py")
