"""Run ONCE (Person A), commit keys/ to the repo, and never regenerate.
Both tracks must use exactly the same keys or results won't match."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from Crypto.PublicKey import RSA
from src import config as C

C.KEYS.mkdir(exist_ok=True)
priv, pub = C.KEYS / "rsa_private.pem", C.KEYS / "rsa_public.pem"
if priv.exists():
    sys.exit("keys/ already exists - not overwriting. Delete manually only if you really mean it.")
key = RSA.generate(2048)
priv.write_bytes(key.export_key())
pub.write_bytes(key.publickey().export_key())
print("Wrote", priv, "and", pub)
