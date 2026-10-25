import numpy as np
from PIL import Image
from src.payload import encrypt_payload, decrypt_payload, bytes_to_bitstream, bitstream_to_bytes

BLOCK_SIZE = 4


def calculate_block_variances(img_array: np.ndarray) -> list[tuple[float, int, int]]:
    """
    Divides image into 4x4 blocks and calculates local variance for each block.
    Returns a list of tuples: (variance, row_idx, col_idx) sorted descending by variance.
    Note: Standard deviation/variance is calculated on MSBs (clearing 2 LSBs) 
    so variance ranking remains identical between cover and stego images.
    """
    h, w = img_array.shape
    blocks = []

    # Mask out lowest 2 bits so LSB modifications don't alter block ranking order during extraction
    msb_array = img_array & 0xFC

    for r in range(0, h - BLOCK_SIZE + 1, BLOCK_SIZE):
        for c in range(0, w - BLOCK_SIZE + 1, BLOCK_SIZE):
            block = msb_array[r : r + BLOCK_SIZE, c : c + BLOCK_SIZE]
            var = float(np.var(block))
            blocks.append((var, r, c))

    # Sort blocks by variance in descending order (highest texture first)
    blocks.sort(key=lambda x: x[0], reverse=True)
    return blocks


def embed_payload(image_path: str, secret_message: str, output_stego_path: str):
    """
    Encrypts secret_message, converts to bitstream, and embeds into 
    high-variance blocks of the cover image.
    """
    # 1. Encrypt message & generate bitstream
    raw_payload = encrypt_payload(secret_message)
    bits = bytes_to_bitstream(raw_payload)
    total_bits = len(bits)

    # 2. Load cover image (grayscale)
    img = Image.open(image_path).convert("L")
    img_array = np.array(img, dtype=np.uint8)
    h, w = img_array.shape

    max_capacity_bits = h * w
    if total_bits > max_capacity_bits:
        raise ValueError(f"Payload size ({total_bits} bits) exceeds image capacity ({max_capacity_bits} bits).")

    # 3. Sort blocks by texture (variance)
    blocks = calculate_block_variances(img_array)

    # 4. Embed bits sequentially into LSB of pixels in high-variance blocks
    bit_idx = 0
    stego_array = img_array.copy()

    for _, r, c in blocks:
        if bit_idx >= total_bits:
            break
        for dr in range(BLOCK_SIZE):
            for dc in range(BLOCK_SIZE):
                if bit_idx < total_bits:
                    pixel = stego_array[r + dr, c + dc]
                    # Replace LSB with payload bit
                    stego_array[r + dr, c + dc] = (pixel & 0xFE) | bits[bit_idx]
                    bit_idx += 1
                else:
                    break

    # 5. Save stego image
    stego_img = Image.fromarray(stego_array)
    stego_img.save(output_stego_path)
    print(f"Successfully embedded {total_bits} bits into {output_stego_path}")


def extract_payload(stego_image_path: str) -> str:
    """
    Extracts bitstream from stego image based on identical variance block sorting,
    reconstructs bytes, and decrypts back to original message string.
    """
    # 1. Load stego image
    img = Image.open(stego_image_path).convert("L")
    stego_array = np.array(img, dtype=np.uint8)

    # 2. Re-calculate block ranking (identical order because ranking uses MSBs)
    blocks = calculate_block_variances(stego_array)

    # 3. Read bits sequentially from sorted blocks
    extracted_bits = []
    for _, r, c in blocks:
        for dr in range(BLOCK_SIZE):
            for dc in range(BLOCK_SIZE):
                pixel = stego_array[r + dr, c + dc]
                extracted_bits.append(pixel & 1)

    # 4. Convert bitstream back to raw bytes and decrypt
    recovered_bytes = bitstream_to_bytes(extracted_bits)
    return decrypt_payload(recovered_bytes)