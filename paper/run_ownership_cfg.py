"""Shared Config D parameters, keys and certificates (imported by run_ownership.py and figs_ownership.py)."""
import json, copy
import numpy as np, pandas as pd
from pipeline import *
import ownership as O
from Crypto.Signature import pss
from Crypto.Hash import SHA256

ECC, BLKD, STEP = "H", 8, 205          # STEP chosen so mean PSNR matches Config A (~40.1 dB)
X0_OWN, R_OWN = 0.12345, 3.9999
owner_key = RSA.import_key(PRIV.read_bytes())
OWNER = "NA+PP NIIT"
m_own = O.qr_modules(O.owner_qr_text(OWNER, owner_key.publickey()), ECC)
cert_own = O.make_certificate(owner_key, OWNER, X0_OWN, R_OWN, STEP, m_own.shape, BLKD)
_cf = OUT / "certificate_owner.json"            # RSA-PSS signatures are randomised: keep the first one
if _cf.exists() and json.loads(_cf.read_text())["body"] == cert_own["body"]:
    cert_own = json.loads(_cf.read_text())
else:
    _cf.write_text(json.dumps(cert_own, indent=2))

ATK_KEY = KEYDIR / "attacker_private.pem"            # simulated attacker, fixed for reproducibility
if not ATK_KEY.exists():
    ATK_KEY.write_bytes(RSA.generate(2048).export_key())
attacker_key = RSA.import_key(ATK_KEY.read_bytes())
X0_ATK, R_ATK = 0.67891, 3.9871
m_atk = O.qr_modules(O.owner_qr_text("XY+ZW ACME", attacker_key.publickey()), ECC)
body_a = dict(owner="XY+ZW ACME", pk_fingerprint=O.fingerprint(attacker_key.publickey()), x0=X0_ATK, r=R_ATK,
              step=STEP, block=BLKD, qr_shape=list(m_atk.shape), scheme="D-blockSVD-QIM-v1")
cert_atk = dict(body=body_a, signature=pss.new(attacker_key).sign(SHA256.new(json.dumps(body_a, sort_keys=True).encode())).hex())

