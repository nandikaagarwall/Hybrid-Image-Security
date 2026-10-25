import os
import struct
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Util.Padding import pad, unpad

DEFAULT_PUB_KEY = os.path.join("keys", "rsa_public.pem")
DEFAULT_PRIV_KEY = os.path.join("keys", "rsa_private.pem")


def encrypt_payload(message: str, rsa_public_key_path: str = DEFAULT_PUB_KEY) -> bytes:
    """
    Encrypts a string message using AES-256-CBC.
    Encrypts the 32-byte AES key using RSA public key.
    Payload layout:
      [256 bytes RSA Encrypted AES Key] + [16 bytes IV] + [AES-CBC Ciphertext]
    """
    # 1. Generate 256-bit (32 bytes) AES key & 16-byte IV
    aes_key = os.urandom(32)
    iv = os.urandom(16)

    # 2. Encrypt plaintext message with AES-CBC & PKCS7 padding
    cipher_aes = AES.new(aes_key, AES.MODE_CBC, iv=iv)
    padded_data = pad(message.encode("utf-8"), AES.block_size)
    ciphertext = cipher_aes.encrypt(padded_data)

    # 3. Encrypt AES key using RSA public key
    with open(rsa_public_key_path, "rb") as f:
        recipient_key = RSA.import_key(f.read())
    cipher_rsa = PKCS1_OAEP.new(recipient_key)
    enc_aes_key = cipher_rsa.encrypt(aes_key)

    # 4. Return concatenated payload
    return enc_aes_key + iv + ciphertext


def decrypt_payload(payload_bytes: bytes, rsa_private_key_path: str = DEFAULT_PRIV_KEY) -> str:
    """
    Decrypts the hybrid payload back to plaintext string using RSA private key.
    """
    # 1. Load private key & calculate modulus byte length (256 bytes for 2048-bit RSA)
    with open(rsa_private_key_path, "rb") as f:
        private_key = RSA.import_key(f.read())

    key_len = private_key.size_in_bytes()

    # 2. Parse payload segments
    enc_aes_key = payload_bytes[:key_len]
    iv = payload_bytes[key_len : key_len + 16]
    ciphertext = payload_bytes[key_len + 16 :]

    # 3. Decrypt AES key with RSA private key
    cipher_rsa = PKCS1_OAEP.new(private_key)
    aes_key = cipher_rsa.decrypt(enc_aes_key)

    # 4. Decrypt message with AES-CBC & remove PKCS7 padding
    cipher_aes = AES.new(aes_key, AES.MODE_CBC, iv=iv)
    decrypted_padded = cipher_aes.decrypt(ciphertext)
    decrypted_bytes = unpad(decrypted_padded, AES.block_size)

    return decrypted_bytes.decode("utf-8")


def bytes_to_bitstream(data: bytes) -> list[int]:
    """
    Prepends a 32-bit (4-byte) length header, then converts
    the entire byte block into a list of bits (0 or 1).
    """
    length_header = struct.pack(">I", len(data))
    full_data = length_header + data
    bits = []
    for byte in full_data:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    return bits


def bitstream_to_bytes(bits: list[int]) -> bytes:
    """
    Reads the 32-bit length header first to extract the exact payload length.
    """
    byte_list = []
    for i in range(0, len(bits) - (len(bits) % 8), 8):
        byte_val = 0
        for bit in bits[i : i + 8]:
            byte_val = (byte_val << 1) | bit
        byte_list.append(byte_val)

    raw_bytes = bytes(byte_list)
    if len(raw_bytes) < 4:
        return b""

    payload_length = struct.unpack(">I", raw_bytes[:4])[0]
    return raw_bytes[4 : 4 + payload_length]