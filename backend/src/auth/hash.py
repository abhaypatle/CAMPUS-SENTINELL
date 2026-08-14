from typing import Optional

try:
    from passlib.context import CryptContext

    # Use pbkdf2_sha256 to avoid environment-specific bcrypt backend issues during tests.
    _pwd_ctx = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


    def hash_password(password: str) -> str:
        return _pwd_ctx.hash(password)


    def verify_password(plain_password: str, password_hash: str) -> bool:
        return _pwd_ctx.verify(plain_password, password_hash)

except Exception:
    # Fallback implementation using hashlib.pbkdf2_hmac
    import hashlib
    import os
    import hmac


    ITERATIONS = 200_000


    def hash_password(password: str) -> str:
        salt = os.urandom(16)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
        return f"pbkdf2_sha256${ITERATIONS}${salt.hex()}${dk.hex()}"


    def verify_password(plain_password: str, password_hash: str) -> bool:
        try:
            prefix, iter_s, salt_hex, dk_hex = password_hash.split("$")
            iterations = int(iter_s)
            salt = bytes.fromhex(salt_hex)
            expected = bytes.fromhex(dk_hex)
            test = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, iterations)
            return hmac.compare_digest(test, expected)
        except Exception:
            return False
