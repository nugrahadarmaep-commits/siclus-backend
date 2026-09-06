from io import BytesIO
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
import jwt
import pandas as pd
import time
from app.core.config import settings
from app.db.database import supabase
from datetime import date
from app.schemas.user import UserRegister, UserUpdate
from app.schemas.jadwal import JadwalCreate, JadwalUpdate
from app.core.security import get_password_hash

router = APIRouter()
security = HTTPBearer()


# verifikasiadmin
def verifikasi_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
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
                detail="Akses ditolak. Eksklusif untuk Administrator.",
            )
        return email_user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Sesi kedaluwarsa.")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token tidak valid.")


# dashboard
@router.get("/dashboard")
def dashboard_admin(email_admin: str = Depends(verifikasi_admin)):
    try:
        tanggal_hari_ini = str(date.today())

        users_res = (
            supabase.table("users").select("id").eq("role", "pengemudi").execute()
        )
        total_supir = len(users_res.data)

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
        raise HTTPException(status_code=500, detail=f"Gagal hitung metrik: {str(e)}")


# rekap
@router.get("/rekap")
def get_rekap_laporan(email_admin: str = Depends(verifikasi_admin)):
    try:
        response = (
            supabase.table("daily_reports")
            .select("*, inspections(*), trip_sessions(*)")
            .execute()
        )
        return {
            "pesan": "Rekapitulasi ditarik.",
            "total_data": len(response.data),
            "data": response.data,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# riwayatharian
@router.get("/riwayat-harian")
def get_riwayat_harian(email_admin: str = Depends(verifikasi_admin)):
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
        raise HTTPException(status_code=500, detail=str(e))


# exportexcel
@router.get("/export-excel")
def export_rekap_excel(
    id_supir: Optional[str] = None, email_admin: str = Depends(verifikasi_admin)
):
    try:
        query = supabase.table("daily_reports").select(
            "*, inspections(*), trip_sessions(*)"
        )

        if id_supir:
            query = query.eq("id_supir", id_supir)

        response = query.execute()
        data_laporan = response.data

        if not data_laporan:
            raise HTTPException(status_code=404, detail="Data laporan kosong.")

        tabel_excel = []
        for baris in data_laporan:
            sesi_list = baris.get("trip_sessions", [])
            sesi = sesi_list[0] if sesi_list else {}

            tabel_excel.append(
                {
                    "Tanggal Operasional": baris.get("tanggal"),
                    "ID Pengemudi": baris.get("id_supir"),
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal export: {str(e)}")


# getusers
@router.get("/users")
def get_semua_supir(email_admin: str = Depends(verifikasi_admin)):
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
        raise HTTPException(status_code=500, detail=str(e))


# postusers
@router.post("/users")
def tambah_supir_baru(data: UserRegister, email_admin: str = Depends(verifikasi_admin)):
    if not data.id.strip() or not data.email.strip() or not data.password.strip():
        raise HTTPException(status_code=400, detail="Data tidak boleh kosong.")

    if supabase.table("users").select("id").eq("id", data.id).execute().data:
        raise HTTPException(status_code=400, detail="ID sudah terdaftar.")
    if supabase.table("users").select("id").eq("email", data.email).execute().data:
        raise HTTPException(status_code=400, detail="Email sudah dipakai.")

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
        raise HTTPException(status_code=500, detail=str(e))


# putusers
@router.put("/users/{user_id}")
def edit_data_supir(
    user_id: str, data: UserUpdate, email_admin: str = Depends(verifikasi_admin)
):
    try:
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=400, detail="Tidak ada data diubah.")

        if "nama_lengkap" in update_data:
            update_data["nama"] = update_data.pop("nama_lengkap")

        response = (
            supabase.table("users").update(update_data).eq("id", user_id).execute()
        )
        if not response.data:
            raise HTTPException(status_code=404, detail="Supir tidak ditemukan.")
        return {"pesan": "Data diperbarui.", "data": response.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# deleteusers
@router.delete("/users/{user_id}")
def hapus_supir(user_id: str, email_admin: str = Depends(verifikasi_admin)):
    try:
        response = supabase.table("users").delete().eq("id", user_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Supir tidak ditemukan.")
        return {"pesan": f"Akun {user_id} dihapus."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# getjadwal
@router.get("/jadwal")
def get_semua_jadwal(email_admin: str = Depends(verifikasi_admin)):
    try:
        response = supabase.table("schedules").select("*").order("trayek").execute()
        return {
            "pesan": "Jadwal ditarik.",
            "total": len(response.data),
            "data": response.data,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# postjadwal
@router.post("/jadwal")
def tambah_jadwal_baru(
    data: JadwalCreate, email_admin: str = Depends(verifikasi_admin)
):
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
        raise HTTPException(status_code=500, detail=str(e))


# putjadwal
@router.put("/jadwal/{jadwal_id}")
def edit_jadwal(
    jadwal_id: int, data: JadwalUpdate, email_admin: str = Depends(verifikasi_admin)
):
    try:
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=400, detail="Tidak ada data diubah.")

        response = (
            supabase.table("schedules")
            .update(update_data)
            .eq("id", jadwal_id)
            .execute()
        )
        if not response.data:
            raise HTTPException(status_code=404, detail="Jadwal tidak ditemukan.")
        return {"pesan": "Jadwal diperbarui.", "data": response.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# uploadfotoadmin
@router.put("/profil/foto")
async def update_foto_profil_admin(
    foto: UploadFile = File(...), email_admin: str = Depends(verifikasi_admin)
):
    try:

        ekstensi = foto.filename.split(".")[-1].lower()
        if ekstensi not in ["jpg", "jpeg", "png"]:
            raise HTTPException(status_code=400, detail="Format tidak didukung!")

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

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
