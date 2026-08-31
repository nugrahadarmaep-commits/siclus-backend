from fastapi import HTTPException, status
from app.schemas.user import UserLogin
from app.core.security import create_access_token, verify_password
from app.db.database import supabase


def proses_login_supir(data_login: UserLogin):
    # 1. Mencari data pengguna di database berdasarkan email
    try:
        response = (
            supabase.table("users").select("*").eq("email", data_login.email).execute()
        )
        db_user_list = response.data
    except Exception as e:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan pada koneksi database: {str(e)}",
        )

    # 2. Validasi ketersediaan email
    if not db_user_list:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kredensial tidak valid. Email tidak ditemukan.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    db_user = db_user_list[0]

    # 3. Validasi Kata Sandi
    if not verify_password(data_login.password, db_user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kredensial tidak valid. Kata sandi salah.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 4. Token Akses (JWT)
    isi_tiket = {"sub": db_user["email"], "role": db_user["role"]}
    token_jwt = create_access_token(data=isi_tiket)

    # 5. Pengembalian Data Respons
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
        },
    }
