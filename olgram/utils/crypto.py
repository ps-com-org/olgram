import base64
import hashlib
from Crypto.Cipher import AES


class Cryptor:
    def __init__(self, password: str):
        if not password:
            raise ValueError("Password cannot be empty or None")
        # Используем SHA-256 для получения ровно 32 байта ключа
        # Это обеспечивает корректную длину ключа независимо от длины пароля
        key = hashlib.sha256(password.encode("utf-8")).digest()
        if len(key) != 32:
            raise ValueError(f"Key length must be 32 bytes, got {len(key)}")
        self._cipher = AES.new(key, AES.MODE_ECB)

    def encrypt(self, data: str) -> str:
        if data.startswith(" "):
            raise ValueError("Data should not start with space!")
        return base64.b64encode(self._cipher.encrypt(data.encode("utf-8").rjust(64))).decode("utf-8")

    def decrypt(self, data: str) -> str:
        return self._cipher.decrypt(base64.b64decode(data.encode("utf-8"))).decode("utf-8").lstrip()
