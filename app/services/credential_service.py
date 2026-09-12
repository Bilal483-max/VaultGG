import base64
import hashlib
import os

from cryptography.fernet import Fernet


def _get_encryption_key():
    secret_key = os.getenv("SECRET_KEY")

    if not secret_key:
        raise RuntimeError(
            "SECRET_KEY is not configured."
        )

    digest = hashlib.sha256(
        secret_key.encode("utf-8")
    ).digest()

    return base64.urlsafe_b64encode(digest)


def encrypt_secret(value):
    if not value:
        return None

    cipher = Fernet(
        _get_encryption_key()
    )

    encrypted = cipher.encrypt(
        value.encode("utf-8")
    )

    return encrypted.decode("utf-8")


def decrypt_secret(value):
    if not value:
        return None

    cipher = Fernet(
        _get_encryption_key()
    )

    decrypted = cipher.decrypt(
        value.encode("utf-8")
    )

    return decrypted.decode("utf-8")