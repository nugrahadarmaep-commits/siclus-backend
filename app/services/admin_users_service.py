import time
from typing import Optional
from fastapi import HTTPException, status, UploadFile
from app.db.database import supabase
from app.core.security import get_password_hash
from app.schemas.user import UserRegister, UserUpdate, AdminProfileUpdate

def get_all_drivers():
    """Mengambil daftar seluruh akun pengemudi/driver."""
    try:
        response = (
            supabase.table("users")
            .select("id, nama, email, trayek, bus, foto_profil")
            .in_("role", ["pengemudi", "driver", "DRIVER", "Driver"])
            .execute()
        )
        return {
            "pesan": "Daftar pengemudi ditarik.",
            "total": len(response.data),
            "data": response.data,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


def create_driver(data: UserRegister):
    """Menambahkan akun supir/driver baru oleh admin."""
    id_clean = data.id.strip().upper()
    email_clean = data.email.strip().lower()
    nama_clean = (data.nama_lengkap or "").strip()
    pw_clean = data.password.strip()

    if not id_clean or not email_clean or not pw_clean:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Data tidak boleh kosong."
        )

    if not nama_clean:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Nama lengkap driver wajib diisi."
        )

    if len(pw_clean) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password driver wajib minimal 8 karakter.",
        )

    # 1. Validasi keunikan ID (Case-Insensitive)
    cek_id = supabase.table("users").select("id").ilike("id", id_clean).execute()
    if cek_id.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID sudah terdaftar.",
        )

    # 2. Validasi keunikan Email (Case-Insensitive)
    cek_email = supabase.table("users").select("id").ilike("email", email_clean).execute()
    if cek_email.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email sudah terdaftar.",
        )

    # 3. Validasi keunikan Nama Lengkap (Case-Insensitive)
    cek_nama = supabase.table("users").select("id, nama").ilike("nama", nama_clean).execute()
    if cek_nama.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nama sudah terdaftar.",
        )

    try:
        response = (
            supabase.table("users")
            .insert(
                {
                    "id": id_clean,
                    "nama": nama_clean,
                    "email": email_clean,
                    "password": get_password_hash(pw_clean),
                    "role": data.role,
                    "trayek": data.trayek,
                    "bus": data.bus,
                }
            )
            .execute()
        )
        user_terdaftar = response.data[0]
        user_terdaftar.pop("password", None)
        return {"pesan": "Akun dibuat.", "data": user_terdaftar}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


def update_driver(user_id: str, data: UserUpdate):
    """Memperbarui informasi akun supir/driver."""
    try:
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Tidak ada data diubah."
            )

        if "nama_lengkap" in update_data:
            update_data["nama"] = update_data.pop("nama_lengkap")

        # Cek keunikan email pada supir lain jika diubah
        if "email" in update_data and update_data["email"]:
            email_clean = str(update_data["email"]).strip().lower()
            update_data["email"] = email_clean
            cek_email = (
                supabase.table("users")
                .select("id")
                .ilike("email", email_clean)
                .neq("id", user_id)
                .execute()
            )
            if cek_email.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email sudah terdaftar.",
                )

        # Cek keunikan nama pada supir lain jika diubah
        if "nama" in update_data and update_data["nama"]:
            nama_clean = str(update_data["nama"]).strip()
            update_data["nama"] = nama_clean
            cek_nama = (
                supabase.table("users")
                .select("id, nama")
                .ilike("nama", nama_clean)
                .neq("id", user_id)
                .execute()
            )
            if cek_nama.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Nama sudah terdaftar.",
                )

        if "password" in update_data:
            pw = str(update_data["password"]).strip()
            if pw:
                if len(pw) < 8:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Password baru driver wajib minimal 8 karakter.",
                    )
                update_data["password"] = get_password_hash(pw)
            else:
                update_data.pop("password")

        response = (
            supabase.table("users").update(update_data).eq("id", user_id).execute()
        )
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Supir tidak ditemukan."
            )

        user_diperbarui = response.data[0]
        user_diperbarui.pop("password", None)
        return {"pesan": "Data diperbarui.", "data": user_diperbarui}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


def delete_driver(user_id: str):
    """Menghapus akun supir/driver dari sistem."""
    try:
        response = supabase.table("users").delete().eq("id", user_id).execute()
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Supir tidak ditemukan."
            )
        return {"pesan": f"Akun {user_id} dihapus."}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


def update_admin_profile(email_admin: str, data: AdminProfileUpdate):
    """Memperbarui informasi identitas profil admin (nama lengkap)."""
    try:
        nama_baru = data.nama_lengkap.strip()
        if not nama_baru:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nama lengkap tidak boleh kosong.",
            )

        res = (
            supabase.table("users")
            .update({"nama": nama_baru})
            .eq("email", email_admin)
            .execute()
        )
        if not res.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Akun admin tidak ditemukan.",
            )

        user_info = res.data[0]
        user_info.pop("password", None)
        return {
            "pesan": "Profil admin berhasil diperbarui.",
            "data": user_info,
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


async def update_admin_avatar(email_admin: str, foto: UploadFile):
    """Mengunggah dan memperbarui foto profil admin."""
    try:
        ekstensi = foto.filename.split(".")[-1].lower() if "." in foto.filename else ""
        if ekstensi not in ["jpg", "jpeg", "png", "webp"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Format tidak didukung. Gunakan JPG, JPEG, PNG, atau WEBP.",
            )

        isi_gambar = await foto.read()
        nama_prefix = email_admin.split("@")[0]
        nama_file_baru = f"admin_avatar_{nama_prefix}_{int(time.time())}.{ekstensi}"

        supabase.storage.from_("foto_profil").upload(
            file=isi_gambar,
            path=nama_file_baru,
            file_options={"content-type": foto.content_type},
        )

        url_publik = supabase.storage.from_("foto_profil").get_public_url(
            nama_file_baru
        )

        supabase.table("users").update({"foto_profil": url_publik}).eq(
            "email", email_admin
        ).execute()

        return {
            "pesan": "Foto profil admin berhasil diupdate",
            "foto_profil": url_publik,
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
