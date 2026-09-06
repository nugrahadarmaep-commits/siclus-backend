from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from app.core.config import settings
from app.db.database import supabase
from fastapi import UploadFile, File
import time

router = APIRouter()
security = HTTPBearer()


# verifikasi token(jwt) driver 
def verifikasi_pengemudi(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """
    Fungsi otorisasi untuk memvalidasi token JWT pada Zona Pengemudi.
    Mengekstrak email pengguna dari payload token.
    """
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


# data profil driver
@router.get("/profil")
def get_profil_pengemudi(email_supir: str = Depends(verifikasi_pengemudi)):
    """
    Menarik data identitas dan penugasan pengemudi (Nama, Trayek, Armada)
    dari database berdasarkan email yang terekstrak dari Token JWT aktif.
    """
    try:
        response = (
            supabase.table("users")
            .select("id, nama, email, role, trayek, bus, foto_profil")
            .eq("email", email_supir)
            .execute()
        )

        data_user = response.data

        if not data_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Data profil pengemudi tidak ditemukan di dalam sistem.",
            )

        return {"pesan": "Data profil berhasil ditarik.", "data": data_user[0]}

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan teknis saat menarik data profil: {str(e)}",
        )


# ubah foto profil driver
@router.put("/profil/foto")
async def update_foto_profil(
    foto: UploadFile = File(...), email_supir: str = Depends(verifikasi_pengemudi)
):
    """
    Mengunggah foto profil baru ke penyimpanan awan dan memperbarui
    tautan (URL) foto tersebut di tabel profil pengguna.
    """
    try:

        ekstensi = foto.filename.split(".")[-1].lower()
        if ekstensi not in ["jpg", "jpeg", "png"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Format tidak didukung. Gunakan JPG, JPEG, atau PNG.",
            )

        nama_prefix = email_supir.split("@")[0]
        nama_file_baru = f"avatar_{nama_prefix}_{int(time.time())}.{ekstensi}"

        isi_gambar = await foto.read()
        response_storage = supabase.storage.from_("foto_profil").upload(
            file=isi_gambar,
            path=nama_file_baru,
            file_options={"content-type": foto.content_type},
        )

        url_publik = supabase.storage.from_("foto_profil").get_public_url(
            nama_file_baru
        )

        supabase.table("users").update({"foto_profil": url_publik}).eq(
            "email", email_supir
        ).execute()

        return {"pesan": "Foto profil berhasil diperbarui!", "foto_profil": url_publik}

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan teknis saat memperbarui foto: {str(e)}",
        )


# riwayat perjalanan driver
@router.get("/riwayat")
def get_riwayat_pengemudi(email_supir: str = Depends(verifikasi_pengemudi)):
    """
    Menarik histori laporan operasional khusus untuk pengemudi yang sedang aktif.
    Dilengkapi sistem filter ketat untuk mencegah kebocoran data antar pengemudi.
    """
    try:
        response = (
            supabase.table("daily_reports")
            .select("*, trip_sessions(*), inspections(*)")
            .eq("id_supir", email_supir)
            .order("tanggal", desc=True)
            .execute()
        )

        data_riwayat = response.data

        return {
            "pesan": "Riwayat perjalanan berhasil ditarik.",
            "total_riwayat": len(data_riwayat),
            "data": data_riwayat,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan teknis saat menarik riwayat: {str(e)}",
        )


# jadwal operasional driver
@router.get("/jadwal")
def get_jadwal_hari_ini(email_supir: str = Depends(verifikasi_pengemudi)):
    """
    Menarik jadwal operasional dan batas waktu toleransi (cut-off time)
    berdasarkan rute/trayek yang ditugaskan kepada pengemudi saat ini.
    """
    try:
        user_response = (
            supabase.table("users").select("trayek").eq("email", email_supir).execute()
        )

        if not user_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Data akun pengemudi tidak ditemukan.",
            )

        trayek_supir = user_response.data[0].get("trayek")

        if not trayek_supir:
            return {
                "pesan": "Anda belum ditugaskan ke rute/trayek mana pun hari ini.",
                "data": [],
            }

        jadwal_response = (
            supabase.table("schedules")
            .select("*")
            .ilike("trayek", trayek_supir)
            .execute()
        )

        return {
            "pesan": f"Jadwal operasional untuk rute {trayek_supir} berhasil ditarik.",
            "data": jadwal_response.data,
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan teknis saat menarik jadwal operasional: {str(e)}",
        )
