import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

ENCRYPTION_SECRET = os.getenv(
    "ENCRYPTION_SECRET", "aperture_default_encryption_key_for_dev_only_change_in_prod"
)
SALT = b"\xbf\x8a\xdb\x9a\x1a\xdf\xd0\xa1\x81\x87\xc0\xbf\xee\xa3\x9a\x12"


def get_key_from_secret(secret: str, salt: bytes) -> bytes:
    """Derives a secure encryption key from a secret string using PBKDF2."""
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=480000)
    key = base64.urlsafe_b64encode(kdf.derive(secret.encode()))
    return key


encryption_key = get_key_from_secret(ENCRYPTION_SECRET, SALT)
fernet_client = Fernet(encryption_key)


def encrypt_data(data: str) -> str:
    """Encrypts a string using Fernet symmetric encryption."""
    if not data:
        return ""
    try:
        encrypted_bytes = fernet_client.encrypt(data.encode())
        return encrypted_bytes.decode()
    except Exception as e:
        logging.exception(f"Encryption failed: {e}")
        raise


def decrypt_data(encrypted_data: str) -> str:
    """Decrypts a string using Fernet symmetric encryption."""
    if not encrypted_data:
        return ""
    try:
        decrypted_bytes = fernet_client.decrypt(encrypted_data.encode())
        return decrypted_bytes.decode()
    except Exception as e:
        logging.exception(
            f"Decryption failed: {e}. The data may be tampered or the key is incorrect."
        )
        return ""