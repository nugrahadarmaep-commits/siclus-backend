from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
import bcrypt  # <-- Kita langsung pake bcrypt ori, buang passlib!
from app.core.config import settings


# ─── FUNGSI KEAMANAN: VERIFIKASI PASSWORD LOGIN ───────────────────────
def verify_password(plain_password: str, hashed_password: str) -> bool:
    # bcrypt butuh format bytes, jadi string-nya harus di-encode ke utf-8 dulu
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


# ─── FUNGSI KEAMANAN: ENKRIPSI PASSWORD (REGISTER) ────────────────────
def get_password_hash(password: str) -> str:
    # Bikin garam (salt) acak, lalu hash password-nya
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)

    # Balikin jadi string biasa biar aman disimpen ke Supabase
    return hashed.decode("utf-8")


# ─── FUNGSI KEAMANAN: PEMBUATAN TOKEN JWT ─────────────────────────────
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()

    # Menentukan waktu kedaluwarsa tiket
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})

    # Membuat token dengan kunci rahasia
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )

    return encoded_jwt
