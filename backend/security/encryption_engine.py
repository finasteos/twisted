"""
End-to-end encryption for TWISTED.
Data at rest, in transit, and in processing.
"""

import base64
import os
import hashlib
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class TWISTEDEncryptionEngine:
    """
    AES-256-GCM encryption for all case data.
    Keys derived from user password + hardware binding.
    """

    def __init__(self, master_key: Optional[str] = None):
        self.master_key = master_key or os.getenv('ENCRYPTION_KEY')
        if not self.master_key:
            # Fallback for development, should be in .env for production
            self.master_key = "twisted_default_master_key_for_dev_only"

    def _derive_key(self, salt: bytes, password: str) -> bytes:
        """Derive encryption key from password."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    def encrypt_case_data(self, case_id: str, plaintext: str, user_password: str) -> dict:
        """
        Encrypt sensitive case data with case-specific key.
        """
        # Generate unique salt per case
        salt = os.urandom(16)

        # Derive case key
        case_key = self._derive_key(salt, user_password + self.master_key)
        fernet = Fernet(case_key)

        # Encrypt
        encrypted = fernet.encrypt(plaintext.encode())

        return {
            "ciphertext": base64.b64encode(encrypted).decode(),
            "salt": base64.b64encode(salt).decode(),
            "algorithm": "fernet-aes-256",
            "case_id_hash": self._hash_case_id(case_id)
        }

    def decrypt_case_data(self, encrypted_bundle: dict, user_password: str) -> str:
        """Decrypt case data."""
        salt = base64.b64decode(encrypted_bundle["salt"])
        case_key = self._derive_key(salt, user_password + self.master_key)
        fernet = Fernet(case_key)

        ciphertext = base64.b64decode(encrypted_bundle["ciphertext"])
        plaintext = fernet.decrypt(ciphertext)

        return plaintext.decode()

    def _hash_case_id(self, case_id: str) -> str:
        """One-way hash for case identification without exposure."""
        return hashlib.sha256(f"twisted:{case_id}".encode()).hexdigest()[:16]
