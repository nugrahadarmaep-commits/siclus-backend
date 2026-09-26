from fastapi import HTTPException, status
from app.schemas.user import UserLogin
from app.core.security import create_access_token, verify_password
from app.db.database import supabase


# service: autentikasi pengguna (login & token)
def proses_login_supir(data_login: UserLogin):
    login_id = (data_login.id or data_login.email or "").strip()
    if not login_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kredensial tidak valid. ID Driver atau Email wajib diisi.",
        )

    if not data_login.password or len(data_login.password.strip()) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password wajib minimal 8 karakter.",
        )

    try:
        # cari user berdasarkan email atau id dalam satu kueri
        response = (
            supabase.table("users")
            .select("*")
            .or_(f"email.eq.{login_id},id.eq.{login_id}")
            .execute()
        )
        db_user_list = response.data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan pada koneksi database: {str(e)}",
        )

    if not db_user_list:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kredensial tidak valid. ID Driver atau Email tidak ditemukan.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    db_user = db_user_list[0]
 
    if str(db_user.get("role", "")).lower() == "nonaktif":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akun driver ini telah dinonaktifkan. Silakan hubungi Administrator Dishub.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(data_login.password, db_user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kredensial tidak valid. Kata sandi salah.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # pembuatan token jwt
    isi_tiket = {
        "sub": db_user["email"],
        "id": db_user["id"],
        "role": db_user["role"],
    }
    token_jwt = create_access_token(data=isi_tiket)

    return {
        "access_token": token_jwt,
        "token_type": "bearer",
        "user": {
            "id": db_user["id"],
            "nama_lengkap": db_user["nama"],
            "email": db_user["email"],
            "role": db_user["role"],
            "trayek": db_user["trayek"],
            "bus": db_user["bus"],
            "foto_profil": db_user.get("foto_profil"),
        },
    }
