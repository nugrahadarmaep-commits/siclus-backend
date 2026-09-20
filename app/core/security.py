from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
import bcrypt
from app.core.config import settings


# verifikasi kecocokan password login
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Memverifikasi password mentah dengan hash bcrypt."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


# enkripsi password baru (hashing)
def get_password_hash(password: str) -> str:
    """Menghasilkan hash string dari password mentah menggunakan salt bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


# pembuatan access token jwt
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Membuat token akses JWT dengan payload dan waktu kedaluwarsa."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
