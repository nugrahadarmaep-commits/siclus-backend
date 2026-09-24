import time
import re
from typing import Optional
from fastapi import HTTPException, status, UploadFile
from app.db.database import supabase
from app.core.security import get_password_hash, verify_password
from app.schemas.user import (
    UserRegister,
    UserUpdate,
    AdminProfileUpdate,
    AdminStaffCreate,
    AdminStaffUpdate,
)

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
    """Menambahkan akun driver baru oleh admin."""
    id_clean = data.id.strip().upper()
    email_clean = data.email.strip().lower()
    nama_clean = (data.nama_lengkap or "").strip()
    pw_clean = data.password.strip()

    if not id_clean or not email_clean or not pw_clean:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Data tidak boleh kosong."
        )
        
    if not email_clean.endswith("@siclus.id"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email driver wajib menggunakan domain resmi @siclus.id",
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


def update_driver(user_id: str, data: UserUpdate, email_admin: Optional[str] = None):
    """Memperbarui informasi akun supir/driver."""
    try:
        # Validasi kredensial administrator jika password_admin dikirim
        if data.password_admin and email_admin:
            admin_res = (
                supabase.table("users")
                .select("password, role")
                .ilike("email", email_admin.strip().lower())
                .execute()
            )
            if not admin_res.data or not verify_password(data.password_admin, admin_res.data[0].get("password", "")):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Password administrator salah. Tindakan modifikasi driver dibatalkan demi keamanan.",
                )

        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        update_data.pop("password_admin", None)
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


def delete_driver(
    user_id: str,
    email_admin: Optional[str] = None,
    password_admin: Optional[str] = None,
):
    """Menghapus akun supir/driver dari sistem dengan validasi keamanan kredensial admin."""
    # 1. Validasi kredensial administrator jika disediakan
    if email_admin and password_admin:
        admin_res = (
            supabase.table("users")
            .select("*")
            .ilike("email", email_admin.strip().lower())
            .execute()
        )
        if not admin_res.data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email administrator tidak ditemukan.",
            )
        admin_user = admin_res.data[0]
        if str(admin_user.get("role", "")).lower() != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Hanya akun Administrator yang berwenang menghapus pengemudi.",
            )
        if not verify_password(password_admin, admin_user.get("password", "")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password administrator salah. Tindakan penghapusan dibatalkan demi keamanan.",
            )

    # 2. Cek apakah target yang akan dihapus memang supir
    target_res = (
        supabase.table("users").select("id, role, nama").eq("id", user_id).execute()
    )
    if not target_res.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Akun driver tidak ditemukan."
        )
    target_user = target_res.data[0]
    if str(target_user.get("role", "")).lower() == "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tidak dapat menghapus sesama akun administrator.",
        )

    try:
        response = supabase.table("users").delete().eq("id", user_id).execute()
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Supir tidak ditemukan."
            )
        return {
            "pesan": f"Akun driver {target_user.get('nama', user_id)} berhasil dihapus permanen."
        }
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


def generate_next_staff_id() -> str:
    """Generate ID otomatis untuk staf operasional: DSHB-OPS-01, DSHB-OPS-02, dst."""
    try:
        res = supabase.table("users").select("id").ilike("id", "DSHB-OPS-%").execute()
        existing_ids = {str(r.get("id", "")).strip().upper() for r in (res.data or [])}
        counter = 1
        while f"DSHB-OPS-{counter:02d}" in existing_ids:
            counter += 1
        return f"DSHB-OPS-{counter:02d}"
    except Exception:
        return "DSHB-OPS-01"


def get_all_admin_staff():
    """Mengambil daftar seluruh akun administrator untuk dikelola Master Admin."""
    try:
        res = (
            supabase.table("users")
            .select("id, nama, email, role, foto_profil")
            .eq("role", "admin")
            .execute()
        )
        staff_list = []
        for u in (res.data or []):
            raw_id = str(u.get("id", "")).strip().upper()
            raw_email = str(u.get("email", "")).strip().lower()
            is_master = raw_id in ["DSHB-ADM-01", "ADM001", "ADM-MASTER"] or raw_email == "admin@siclus.id"
            staff_list.append({
                "id": "DSHB-ADM-01" if is_master else u.get("id"),
                "raw_id": u.get("id"),
                "nama": u.get("nama"),
                "email": u.get("email"),
                "role": u.get("role"),
                "foto_profil": u.get("foto_profil"),
                "is_master": is_master,
                "tipe_admin": "Administrator Utama" if is_master else "Administrator Operasional",
            })
        staff_list.sort(key=lambda x: (not x["is_master"], str(x["id"])))
        return {
            "pesan": "Daftar staf administrator berhasil diambil.",
            "total": len(staff_list),
            "data": staff_list,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


def create_admin_staff(data: AdminStaffCreate):
    """Menambahkan akun staf administrator operasional baru oleh Administrator Utama."""
    nama_clean = (data.nama_lengkap or "").strip()
    email_clean = data.email.strip().lower()
    pw_clean = data.password.strip()

    if not nama_clean:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nama lengkap staf administrator wajib diisi.",
        )

    if not email_clean.endswith("@siclus.id"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email staf administrator wajib menggunakan domain resmi @siclus.id",
        )

    if len(pw_clean) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password wajib minimal 8 karakter.",
        )
    if not re.search(r"[A-Z]", pw_clean):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password wajib mengandung minimal 1 huruf kapital.",
        )
    if not re.search(r"[a-z]", pw_clean):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password wajib mengandung minimal 1 huruf kecil.",
        )
    if not re.search(r"[0-9]", pw_clean):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password wajib mengandung minimal 1 angka.",
        )
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", pw_clean):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password wajib mengandung minimal 1 simbol/karakter khusus (contoh: #, @, $, !).",
        )

    cek_email = supabase.table("users").select("id").ilike("email", email_clean).execute()
    if cek_email.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email '{email_clean}' sudah digunakan akun lain.",
        )

    staff_id = generate_next_staff_id()
    hashed_pw = get_password_hash(pw_clean)

    payload = {
        "id": staff_id,
        "nama": nama_clean,
        "email": email_clean,
        "password": hashed_pw,
        "role": "admin",
    }

    try:
        res = supabase.table("users").insert(payload).execute()
        if not res.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Gagal menyimpan staf administrator ke database.",
            )
        new_staff = res.data[0]
        new_staff.pop("password", None)
        return {
            "pesan": f"Staf administrator operasional {nama_clean} ({staff_id}) berhasil ditambahkan.",
            "data": new_staff,
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


def delete_admin_staff(
    user_id: str,
    email_admin: Optional[str] = None,
    password_admin: Optional[str] = None,
):
    """Menghapus akun staf administrator operasional (Khusus Master Admin)."""
    clean_id = (user_id or "").strip()

    if clean_id.upper() in ["DSHB-ADM-01", "ADM001", "ADM-MASTER"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tindakan ditolak. Akun Administrator Utama terproteksi dan tidak dapat dihapus.",
        )

    # Verifikasi kredensial master admin jika disediakan
    if email_admin and password_admin:
        admin_res = (
            supabase.table("users")
            .select("password, role")
            .ilike("email", email_admin.strip().lower())
            .execute()
        )
        if not admin_res.data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email administrator tidak ditemukan.",
            )
        admin_user = admin_res.data[0]
        if not verify_password(password_admin, admin_user.get("password", "")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password administrator salah. Tindakan penghapusan dibatalkan demi keamanan.",
            )

    target_res = (
        supabase.table("users")
        .select("id, nama, email, role")
        .eq("id", clean_id)
        .execute()
    )
    if not target_res.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Akun administrator dengan ID '{clean_id}' tidak ditemukan.",
        )

    target_user = target_res.data[0]
    if str(target_user.get("email", "")).lower() == "admin@siclus.id":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tindakan ditolak. Akun Administrator Utama terproteksi dan tidak dapat dihapus.",
        )

    try:
        supabase.table("users").delete().eq("id", clean_id).execute()
        return {
            "pesan": f"Akun staf administrator {target_user.get('nama')} ({clean_id}) berhasil dihapus.",
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


def update_admin_staff(
    user_id: str,
    data: AdminStaffUpdate,
    email_admin: Optional[str] = None,
):
    """Memperbarui informasi nama dan/atau reset kata sandi staf admin operasional (Khusus Master Admin)."""
    clean_id = (user_id or "").strip()

    if clean_id.upper() in ["DSHB-ADM-01", "ADM001", "ADM-MASTER"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tindakan ditolak. Akun Administrator Utama dikelola melalui menu Profil Pribadi.",
        )

    # Validasi password administrator jika dikirim
    if data.password_admin and email_admin:
        admin_res = (
            supabase.table("users")
            .select("password, role")
            .ilike("email", email_admin.strip().lower())
            .execute()
        )
        if not admin_res.data or not verify_password(data.password_admin, admin_res.data[0].get("password", "")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password administrator salah. Perubahan data staf dibatalkan demi keamanan.",
            )

    target_res = (
        supabase.table("users")
        .select("id, nama, email, role")
        .eq("id", clean_id)
        .execute()
    )
    if not target_res.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Akun administrator dengan ID '{clean_id}' tidak ditemukan.",
        )

    target_user = target_res.data[0]
    if str(target_user.get("email", "")).lower() == "admin@siclus.id":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tindakan ditolak. Akun Administrator Utama dikelola melalui menu Profil Pribadi.",
        )

    update_payload = {}

    if data.nama_lengkap is not None:
        nama_clean = data.nama_lengkap.strip()
        if not nama_clean:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nama lengkap staf administrator tidak boleh kosong.",
            )
        update_payload["nama"] = nama_clean

    if data.password is not None and data.password.strip():
        pw_clean = data.password.strip()
        if len(pw_clean) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password baru wajib minimal 8 karakter.",
            )
        if not re.search(r"[A-Z]", pw_clean):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password baru wajib mengandung minimal 1 huruf kapital.",
            )
        if not re.search(r"[a-z]", pw_clean):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password baru wajib mengandung minimal 1 huruf kecil.",
            )
        if not re.search(r"[0-9]", pw_clean):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password baru wajib mengandung minimal 1 angka.",
            )
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", pw_clean):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password baru wajib mengandung minimal 1 simbol/karakter khusus.",
            )
        update_payload["password"] = get_password_hash(pw_clean)

    if not update_payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tidak ada data perubahan yang dikirimkan.",
        )

    try:
        res = (
            supabase.table("users")
            .update(update_payload)
            .eq("id", clean_id)
            .execute()
        )
        if not res.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Gagal memperbarui data staf administrator di database.",
            )
        updated_staff = res.data[0]
        updated_staff.pop("password", None)
        return {
            "pesan": f"Data staf administrator {updated_staff.get('nama', clean_id)} berhasil diperbarui.",
            "data": updated_staff,
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )

