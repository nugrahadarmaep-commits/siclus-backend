# ==============================================================================
# SERVICE: AUTENTIKASI PENGGUNA (LOGIN & TOKEN)
# ==============================================================================

from fastapi import HTTPException, status
from app.schemas.user import UserLogin
from app.core.security import create_access_token, verify_password
from app.db.database import supabase


def proses_login_supir(data_login: UserLogin):

    # 1. Ambil identitas login (bisa dikirim via field 'id' atau 'email')
    login_id = (data_login.id or data_login.email or "").strip()
    if not login_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kredensial tidak valid. ID Driver atau Email wajib diisi.",
        )

    # 2. Mencari data pengguna di database (prioritas: jika ada '@' cari email, selain itu cari ID)
    try:
        if "@" in login_id:
            response = (
                supabase.table("users").select("*").eq("email", login_id).execute()
            )
        else:
            response = supabase.table("users").select("*").eq("id", login_id).execute()

        db_user_list = response.data

        # Fallback pencarian silang jika percobaan pertama belum menemukan akun
        if not db_user_list:
            if "@" in login_id:
                alt_response = (
                    supabase.table("users").select("*").eq("id", login_id).execute()
                )
            else:
                alt_response = (
                    supabase.table("users").select("*").eq("email", login_id).execute()
                )
            db_user_list = alt_response.data

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan pada koneksi database: {str(e)}",
        )

    # 3. Validasi ketersediaan pengguna
    if not db_user_list:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kredensial tidak valid. ID Driver atau Email tidak ditemukan.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    db_user = db_user_list[0]

    # 4. Validasi Kata Sandi
    if not verify_password(data_login.password, db_user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kredensial tidak valid. Kata sandi salah.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 5. Token Akses (JWT)
    isi_tiket = {
        "sub": db_user["email"],
        "id": db_user["id"],
        "role": db_user["role"],
    }
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
            "foto_profil": db_user.get("foto_profil"),
        },
    }
