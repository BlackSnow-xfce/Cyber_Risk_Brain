import base64
import hashlib

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from aidp_orchestration.ed25519 import AIDPSignatureV1, _signed_bytes


def sign_for_test(payload: bytes, *, key_id: str, private_key: bytes, schema_version: str) -> bytes:
    key = Ed25519PrivateKey.from_private_bytes(private_key)
    signature = key.sign(_signed_bytes(payload, schema_version))
    return AIDPSignatureV1(
        schema_version,
        "Ed25519",
        key_id,
        hashlib.sha256(payload).hexdigest(),
        base64.urlsafe_b64encode(signature).decode("ascii"),
    ).encoded()
