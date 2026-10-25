import os
from Crypto.PublicKey import RSA

KEY_DIR = "keys"
PUB_KEY_PATH = os.path.join(KEY_DIR, "rsa_public.pem")
PRIV_KEY_PATH = os.path.join(KEY_DIR, "rsa_private.pem")


def generate_rsa_keys(key_size: int = 2048):
    """Generates a new 2048-bit RSA key pair and saves them to the keys directory."""
    os.makedirs(KEY_DIR, exist_ok=True)

    print(f"[*] Generating {key_size}-bit RSA key pair...")
    key = RSA.generate(key_size)

    # Export Private Key
    private_key = key.export_key()
    with open(PRIV_KEY_PATH, "wb") as f:
        f.write(private_key)

    # Export Public Key
    public_key = key.publickey().export_key()
    with open(PUB_KEY_PATH, "wb") as f:
        f.write(public_key)

    print(f"[+] Private Key saved to: {PRIV_KEY_PATH}")
    print(f"[+] Public Key saved to: {PUB_KEY_PATH}")


if __name__ == "__main__":
    generate_rsa_keys()