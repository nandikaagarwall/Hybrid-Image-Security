"""Test setup: run from the repo root with `python -m pytest tests`.

The real RSA private key is never committed, so the tests generate a
throwaway key pair and point src.payload's default key paths at it."""
import sys
from pathlib import Path

import pytest
from Crypto.PublicKey import RSA

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src import payload  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def temporary_rsa_keys(tmp_path_factory):
    d = tmp_path_factory.mktemp("keys")
    key = RSA.generate(2048)
    (d / "rsa_private.pem").write_bytes(key.export_key())
    (d / "rsa_public.pem").write_bytes(key.publickey().export_key())
    old = payload.encrypt_payload.__defaults__, payload.decrypt_payload.__defaults__
    payload.encrypt_payload.__defaults__ = (str(d / "rsa_public.pem"),)
    payload.decrypt_payload.__defaults__ = (str(d / "rsa_private.pem"),)
    yield d
    payload.encrypt_payload.__defaults__, payload.decrypt_payload.__defaults__ = old
