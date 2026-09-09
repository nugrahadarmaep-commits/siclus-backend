# ==============================================================================
# SERVICE: ADMINISTRATOR OPERATIONS
# ==============================================================================

from io import BytesIO
from typing import Optional
from datetime import date
import time
import pandas as pd
from fastapi import HTTPException, status, UploadFile
from fastapi.responses import StreamingResponse

from app.db.database import supabase
from app.core.security import get_password_hash
from app.schemas.user import UserRegister, UserUpdate, AdminProfileUpdate
from app.schemas.jadwal import JadwalCreate, JadwalUpdate
from app.schemas.penugasan import PenugasanCreate, PenugasanUpdate


# ==============================================================================
# DASHBOARD & STATISTIK OPERASIONAL
# ==============================================================================

def get_dashboard_metrics():
    """Menghitung metrik kehadiran dan keterlambatan driver hari ini."""
    try:
        tanggal_hari_ini = str(date.today())

        # Hitung total armada driver terdaftar
        users_res = (
            supabase.table("users")
            .select("id")
            .in_("role", ["pengemudi", "driver", "DRIVER", "Driver"])
            .execute()
        )
        total_supir = len(users_res.data)

        # Hitung laporan yang masuk hari ini
        reports_res = (
            supabase.table("daily_reports")
            .select("id, id_supir, trip_sessions(status_waktu)")
            .eq("tanggal", tanggal_hari_ini)
            .execute()
        )
        data_laporan_hari_ini = reports_res.data

        total_jalan = len(data_laporan_hari_ini)
        total_absen = max(0, total_supir - total_jalan)

        total_telat = 0
        for laporan in data_laporan_hari_ini:
            sesi_list = laporan.get("trip_sessions", [])
            for sesi in sesi_list:
                if sesi.get("status_waktu") == "TERLAMBAT":
                    total_telat += 1
                    break

        return {
            "pesan": "Metrik dashboard ditarik.",
            "data": {
                "tanggal": tanggal_hari_ini,
                "total_supir_terdaftar": total_supir,
                "total_supir_jalan": total_jalan,
                "total_supir_absen": total_absen,
                "total_supir_telat": total_telat,
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal hitung metrik dashboard: {str(e)}",
        )


# ==============================================================================
# REKAPITULASI & LAPORAN OPERASIONAL
# ==============================================================================
def get_rekap_operasional():
    """Mengambil seluruh data rekap harian lengkap beserta inspeksi dan sesi."""
    try:
        response = (
            supabase.table("daily_reports")
            .select("*, inspections(*), trip_sessions(*), users(nama, trayek, bus)")
            .execute()
        )
        return {
            "pesan": "Rekapitulasi ditarik.",
            "total_data": len(response.data),
            "data": response.data,
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


def get_riwayat_harian_grouped():
    """Mengambil riwayat laporan operasional yang dikelompokkan berdasarkan tanggal."""
    try:
        response = (
            supabase.table("daily_reports")
            .select("*, users(nama), trip_sessions(status_waktu, tipe_sesi)")
            .order("tanggal", desc=True)
            .execute()
        )

        grup_tanggal = {}
        for laporan in response.data:
            tgl = laporan.get("tanggal")
            if tgl not in grup_tanggal:
                grup_tanggal[tgl] = []
            grup_tanggal[tgl].append(laporan)

        hasil_format = [
            {"tanggal": tgl, "laporan": isi} for tgl, isi in grup_tanggal.items()
        ]

        return {"pesan": "Riwayat harian ditarik.", "data": hasil_format}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


def export_rekap_to_excel(id_supir: Optional[str] = None):
    """Menghasilkan file Excel rekapan operasional harian untuk diunduh."""
    try:
        query = supabase.table("daily_reports").select(
            "*, inspections(*), trip_sessions(*), users(nama)"
        )

        if id_supir:
            query = query.eq("id_supir", id_supir)

        response = query.execute()
        data_laporan = response.data

        if not data_laporan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data laporan kosong.")

        tabel_excel = []
        for baris in data_laporan:
            sesi_list = baris.get("trip_sessions", [])
            sesi = sesi_list[0] if sesi_list else {}
            user_info = baris.get("users") or {}
            nama_driver = user_info.get("nama") or baris.get("id_supir") or "-"

            tabel_excel.append(
                {
                    "Tanggal Operasional": baris.get("tanggal"),
                    "Nama Driver": nama_driver,
                    "ID Driver": baris.get("id_supir"),
                    "Trayek": baris.get("trayek"),
                    "Armada Bus": baris.get("bus"),
                    "Tipe Sesi": sesi.get("tipe_sesi", "-"),
                    "Jam Keluar Dishub": sesi.get("jam_berangkat_kantor", "-"),
                    "Jam Tiba di Sekolah": sesi.get("jam_berangkat_start", "-"),
                    "Status Kedisiplinan": sesi.get("status_waktu", "-"),
                }
            )

        df = pd.DataFrame(tabel_excel)
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Rekap_Siclus")

        buffer.seek(0)
        nama_file = f"Rekap_{id_supir}.xlsx" if id_supir else "Rekap_Semua_Supir.xlsx"

        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={nama_file}"},
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal export Excel: {str(e)}",
        )


# ==============================================================================
# MANAJEMEN AKUN DRIVER (SUPIR)
# ==============================================================================
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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


def create_driver(data: UserRegister):
    """Menambahkan akun supir/driver baru oleh admin."""
    if not data.id.strip() or not data.email.strip() or not data.password.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Data tidak boleh kosong.")

    # Validasi keunikan ID dan Email
    if supabase.table("users").select("id").eq("id", data.id).execute().data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ID sudah terdaftar.")
    if supabase.table("users").select("id").eq("email", data.email).execute().data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email sudah dipakai.")

    try:
        response = (
            supabase.table("users")
            .insert(
                {
                    "id": data.id,
                    "nama": data.nama_lengkap,
                    "email": data.email,
                    "password": get_password_hash(data.password),
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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


def update_driver(user_id: str, data: UserUpdate):
    """Memperbarui informasi akun supir/driver."""
    try:
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tidak ada data diubah.")

        if "nama_lengkap" in update_data:
            update_data["nama"] = update_data.pop("nama_lengkap")

        if "password" in update_data:
            pw = str(update_data["password"]).strip()
            if pw:
                update_data["password"] = get_password_hash(pw)
            else:
                update_data.pop("password")

        response = (
            supabase.table("users").update(update_data).eq("id", user_id).execute()
        )
        if not response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supir tidak ditemukan.")

        user_diperbarui = response.data[0]
        user_diperbarui.pop("password", None)
        return {"pesan": "Data diperbarui.", "data": user_diperbarui}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


def delete_driver(user_id: str):
    """Menghapus akun supir/driver dari sistem."""
    try:
        response = supabase.table("users").delete().eq("id", user_id).execute()
        if not response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supir tidak ditemukan.")
        return {"pesan": f"Akun {user_id} dihapus."}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ==============================================================================
# MANAJEMEN JADWAL OPERASIONAL
# ==============================================================================
def get_all_schedules():
    """Mengambil daftar seluruh jadwal operasional."""
    try:
        response = supabase.table("schedules").select("*").order("trayek").execute()
        return {
            "pesan": "Jadwal ditarik.",
            "total": len(response.data),
            "data": response.data,
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


def create_schedule(data: JadwalCreate):
    """Menambahkan jadwal rute baru."""
    try:
        response = (
            supabase.table("schedules")
            .insert(
                {
                    "trayek": data.trayek,
                    "tipe_sesi": data.tipe_sesi.upper(),
                    "batas_keluar_dishub": data.batas_keluar_dishub,
                    "batas_tiba_start": data.batas_tiba_start,
                }
            )
            .execute()
        )
        return {"pesan": "Jadwal ditambahkan.", "data": response.data[0]}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


def update_schedule(jadwal_id: str, data: JadwalUpdate):
    """Memperbarui jadwal rute operasional."""
    try:
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tidak ada data diubah.")

        if "tipe_sesi" in update_data and update_data["tipe_sesi"]:
            update_data["tipe_sesi"] = update_data["tipe_sesi"].upper()

        response = (
            supabase.table("schedules")
            .update(update_data)
            .eq("id", jadwal_id)
            .execute()
        )
        if not response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Jadwal tidak ditemukan.")
        return {"pesan": "Jadwal diperbarui.", "data": response.data[0]}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


def delete_schedule(jadwal_id: str):
    """Menghapus jadwal operasional."""
    try:
        response = (
            supabase.table("schedules")
            .delete()
            .eq("id", jadwal_id)
            .execute()
        )
        if not response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Jadwal tidak ditemukan.")
        return {"pesan": f"Jadwal {jadwal_id} berhasil dihapus."}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ==============================================================================
# PROFIL PRIBADI ADMIN
# ==============================================================================
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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


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

        url_publik = supabase.storage.from_("foto_profil").get_public_url(nama_file_baru)

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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ==============================================================================
# MANAJEMEN PENUGASAN KENDARAAN (HARIAN)
# ==============================================================================
def get_semua_penugasan():
    """Mengambil daftar seluruh penugasan harian."""
    try:
        response = (
            supabase.table("penugasan")
            .select("*, users(nama, email)")
            .order("tanggal", desc=True)
            .execute()
        )
        return {
            "pesan": "Daftar penugasan ditarik.",
            "total": len(response.data),
            "data": response.data,
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


def create_penugasan_harian(data: PenugasanCreate):
    """Admin membuat penugasan kendaraan untuk supir pada hari tertentu."""
    try:
        # Cek apakah supir ada
        user = supabase.table("users").select("id").eq("id", data.id_supir).execute()
        if not user.data:
            raise HTTPException(status_code=404, detail="Supir tidak ditemukan.")

        # Cek apakah sudah ada penugasan di tanggal yang sama untuk supir ini
        cek = (
            supabase.table("penugasan")
            .select("id")
            .eq("id_supir", data.id_supir)
            .eq("tanggal", str(data.tanggal))
            .execute()
        )
        
        if cek.data:
            # Update jika sudah ada
            res = (
                supabase.table("penugasan")
                .update(
                    {
                        "nopol_kendaraan": data.nopol_kendaraan,
                        "jenis_kendaraan": data.jenis_kendaraan,
                        "kapasitas_penumpang": data.kapasitas_penumpang,
                        "trayek": data.trayek,
                    }
                )
                .eq("id", cek.data[0]["id"])
                .execute()
            )
            pesan = "Penugasan diperbarui."
        else:
            # Insert baru
            res = (
                supabase.table("penugasan")
                .insert(
                    {
                        "id_supir": data.id_supir,
                        "tanggal": str(data.tanggal),
                        "nopol_kendaraan": data.nopol_kendaraan,
                        "jenis_kendaraan": data.jenis_kendaraan,
                        "kapasitas_penumpang": data.kapasitas_penumpang,
                        "trayek": data.trayek,
                    }
                )
                .execute()
            )
            pesan = "Penugasan dibuat."
            
        return {"pesan": pesan, "data": res.data[0]}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
