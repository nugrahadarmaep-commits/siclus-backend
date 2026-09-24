from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from app.core.config import settings
from app.db.database import supabase

security = HTTPBearer()

def verifikasi_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """Verifikasi token JWT khusus administrator dan validasi keaktifan akun di database."""
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        email_user = payload.get("sub")
        role_user = payload.get("role")

        if role_user != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Akses ditolak. Endpoint eksklusif untuk Administrator.",
            )

        if not email_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Kredensial tidak valid. Sesi pengguna kosong.",
            )

        # Cek real-time ke database Supabase (mencegah 'zombie token' bila akun sudah dihapus)
        clean_email = email_user.strip().lower()
        user_res = (
            supabase.table("users")
            .select("id, role")
            .ilike("email", clean_email)
            .execute()
        )
        if not user_res.data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Akun administrator Anda telah dihapus atau dinonaktifkan oleh Administrator Utama.",
            )

        db_role = str(user_res.data[0].get("role", "")).lower()
        if db_role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Hak akses administrator Anda telah dicabut.",
            )

        return email_user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Sesi kedaluwarsa.")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token tidak valid.")


def verifikasi_master_admin(
    email_admin: str = Depends(verifikasi_admin),
) -> str:
    """Verifikasi hak akses khusus Administrator Utama"""
    if (email_admin or "").strip().lower() != "admin@siclus.id":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akses ditolak. Fitur kelola staf hanya untuk Administrator Utama.",
        )
    return email_admin


def verifikasi_pengemudi(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """Verifikasi token JWT untuk pengemudi dan mengembalikan email pengemudi."""
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        email_user = payload.get("sub")
        if not email_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Kredensial tidak valid. Payload token kosong.",
            )

        # Cek real-time ke database Supabase (mencegah akses supir yang sudah dihapus)
        clean_email = email_user.strip().lower()
        user_res = (
            supabase.table("users")
            .select("id, role")
            .ilike("email", clean_email)
            .execute()
        )
        if not user_res.data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Akun pengemudi Anda telah dihapus atau tidak terdaftar.",
            )

        return email_user
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesi telah kedaluwarsa. Silakan login kembali.",
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token autentikasi tidak valid atau telah dimanipulasi.",
        )


# Alias untuk fleksibilitas pemanggilan di rute laporan
verifikasi_token = verifikasi_pengemudi

