import argparse
import sys
import cv2
import numpy as np

from src.stego import embed_payload, extract_payload
from src.metrics import mse, psnr, ssim, entropy_diff, hist_chi2_distance


def handle_embed(args):
    """Handles embedding a secret message into a cover image."""
    print(f"[*] Embedding message into '{args.cover}'...")
    try:
        embed_payload(args.cover, args.message, args.output)
        print(f"[+] Stego image successfully created: '{args.output}'")
    except Exception as e:
        print(f"[-] Embedding failed: {e}")
        sys.exit(1)


def handle_extract(args):
    """Handles extracting and decrypting the secret message from a stego image."""
    print(f"[*] Extracting payload from '{args.stego}'...")
    try:
        message = extract_payload(args.stego)
        print(f"[+] Extracted Secret Message:\n--- BEGIN MESSAGE ---\n{message}\n--- END MESSAGE ---")
    except Exception as e:
        print(f"[-] Extraction failed: {e}")
        sys.exit(1)


def handle_eval(args):
    """Runs imperceptibility and concealment evaluation metrics between cover and stego images."""
    print(f"[*] Evaluating metrics: Cover='{args.cover}' vs Stego='{args.stego}'...")
    try:
        cover = cv2.imread(args.cover, cv2.IMREAD_GRAYSCALE)
        stego = cv2.imread(args.stego, cv2.IMREAD_GRAYSCALE)

        if cover is None or stego is None:
            raise FileNotFoundError("Could not read cover or stego image path.")

        m_mse = mse(cover, stego)
        m_psnr = psnr(cover, stego)
        m_ssim = ssim(cover, stego)
        m_ent_diff = entropy_diff(cover, stego)
        m_chi2 = hist_chi2_distance(cover, stego)

        print("=" * 50)
        print("          HYBRID STEGANOGRAPHY METRICS         ")
        print("=" * 50)
        print(f"  MSE  (Mean Squared Error)       : {m_mse:.6f}")
        print(f"  PSNR (Peak Signal-to-Noise Ratio): {m_psnr:.2f} dB")
        print(f"  SSIM (Structural Similarity)    : {m_ssim:.4f}")
        print(f"  Entropy Difference              : {m_ent_diff:.6f}")
        print(f"  Histogram Chi-Sq Distance       : {m_chi2:.6f}")
        print("=" * 50)
    except Exception as e:
        print(f"[-] Evaluation failed: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Hybrid Image Security CLI: Texture-Adaptive Steganography & AES-RSA Encryption"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Embed Command
    parser_embed = subparsers.add_parser("embed", help="Encrypt and hide message inside cover image")
    parser_embed.add_argument("-c", "--cover", required=True, help="Path to cover image")
    parser_embed.add_argument("-m", "--message", required=True, help="Secret text message to conceal")
    parser_embed.add_argument("-o", "--output", default="stego.png", help="Path for generated stego image (default: stego.png)")
    parser_embed.set_defaults(func=handle_embed)

    # Extract Command
    parser_extract = subparsers.add_parser("extract", help="Extract and decrypt hidden message from stego image")
    parser_extract.add_argument("-s", "--stego", required=True, help="Path to stego image")
    parser_extract.set_defaults(func=handle_extract)

    # Evaluate Command
    parser_eval = subparsers.add_parser("eval", help="Calculate quality and concealment metrics")
    parser_eval.add_argument("-c", "--cover", required=True, help="Path to original cover image")
    parser_eval.add_argument("-s", "--stego", required=True, help="Path to stego image")
    parser_eval.set_defaults(func=handle_eval)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()