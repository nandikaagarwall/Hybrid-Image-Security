import os
import unittest
import numpy as np
from PIL import Image

from src.payload import encrypt_payload, decrypt_payload, bytes_to_bitstream, bitstream_to_bytes
from src.stego import embed_payload, extract_payload
from src.metrics import mse, psnr, ssim, ber


class TestHybridSteganographyPipeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Creates temporary test directories and synthetic cover images."""
        cls.test_dir = "tests_tmp"
        os.makedirs(cls.test_dir, exist_ok=True)

        cls.cover_path = os.path.join(cls.test_dir, "test_cover.png")
        cls.stego_path = os.path.join(cls.test_dir, "test_stego.png")

        # Generate a 256x256 test image with high texture/variance
        rng = np.random.default_rng(42)
        random_image = rng.integers(0, 256, (256, 256), dtype=np.uint8)
        Image.fromarray(random_image).save(cls.cover_path)

    @classmethod
    def tearDownClass(cls):
        """Clean up generated test files after execution."""
        for file in [cls.cover_path, cls.stego_path]:
            if os.path.exists(file):
                os.remove(file)
        if os.path.exists(cls.test_dir):
            os.rmdir(cls.test_dir)

    def test_01_payload_encryption_decryption(self):
        """Test RSA-AES encryption and bitstream reconstruction."""
        original_message = "Confidential Payload Test Message 2026!"
        encrypted = encrypt_payload(original_message)
        bits = bytes_to_bitstream(encrypted)
        recovered_bytes = bitstream_to_bytes(bits)
        decrypted_message = decrypt_payload(recovered_bytes)

        self.assertEqual(original_message, decrypted_message)

    def test_02_stego_embedding_and_extraction(self):
        """Test full texture-adaptive embedding and extraction pipeline."""
        secret_msg = "Top Secret Steganography Test Payload"
        embed_payload(self.cover_path, secret_msg, self.stego_path)

        extracted_msg = extract_payload(self.stego_path)
        self.assertEqual(secret_msg, extracted_msg)

    def test_03_imperceptibility_benchmarks(self):
        """Verify image quality thresholds (PSNR > 40 dB, SSIM > 0.95)."""
        secret_msg = "Benchmarking Image Quality Metrics"
        embed_payload(self.cover_path, secret_msg, self.stego_path)

        cover = np.array(Image.open(self.cover_path).convert("L"))
        stego = np.array(Image.open(self.stego_path).convert("L"))

        val_psnr = psnr(cover, stego)
        val_ssim = ssim(cover, stego)
        val_mse = mse(cover, stego)

        print(f"\n[Benchmark Results] PSNR: {val_psnr:.2f} dB | SSIM: {val_ssim:.4f} | MSE: {val_mse:.4f}")

        # Assert visual imperceptibility thresholds
        self.assertGreater(val_psnr, 40.0, "PSNR failed quality threshold (>40 dB)")
        self.assertGreater(val_ssim, 0.95, "SSIM failed quality threshold (>0.95)")

    def test_04_zero_bit_error_rate(self):
        """Verify Bit Error Rate (BER) is exactly 0.0 for uncorrupted extraction."""
        raw_payload = encrypt_payload("Zero Bit Error Test")
        original_bits = bytes_to_bitstream(raw_payload)

        # Simulate round-trip conversion
        recovered_bytes = bitstream_to_bytes(original_bits)
        recovered_bits = bytes_to_bitstream(recovered_bytes)

        bit_err = ber(original_bits, recovered_bits)
        self.assertEqual(bit_err, 0.0, "BER should be 0.0 under normal extraction")


if __name__ == "__main__":
    unittest.main()