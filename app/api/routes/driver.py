# ==============================================================================
# ROUTE: PENGEMUDI (DRIVER)
# ==============================================================================

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import time

from app.core.config import settings
from app.db.database import supabase
from datetime import date

router = APIRouter()
security = HTTPBearer()


# ==============================================================================
# VERIFIKASI KEAMANAN PENGEMUDI (TOKEN JWT)
# ==============================================================================
def verifikasi_pengemudi(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
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


# ==============================================================================
# PROFIL PENGEMUDI
# ==============================================================================
@router.get(
    "/profil",
    tags=["Pengemudi - Akun & Jadwal"],
    summary="Data Profil Pengemudi Aktif",
)
def get_profil_pengemudi(email_supir: str = Depends(verifikasi_pengemudi)):
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


# ==============================================================================
# UNGGAH FOTO PROFIL PENGEMUDI
# ==============================================================================
@router.put(
    "/profil/foto",
    tags=["Pengemudi - Akun & Jadwal"],
    summary="Unggah Foto Profil Pengemudi",
)
async def update_foto_profil(
    foto: UploadFile = File(...), email_supir: str = Depends(verifikasi_pengemudi)
):
    try:

        ekstensi = foto.filename.split(".")[-1].lower()
        if ekstensi not in ["jpg", "jpeg", "png", "webp"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Format tidak didukung. Gunakan JPG, JPEG, PNG, atau WEBP.",
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


# ==============================================================================
# HISTORI RIWAYAT PERJALANAN PENGEMUDI
# ==============================================================================
@router.get(
    "/riwayat",
    tags=["Pengemudi - Akun & Jadwal"],
    summary="Histori Riwayat Operasional Pengemudi",
)
def get_riwayat_pengemudi(email_supir: str = Depends(verifikasi_pengemudi)):
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


# ==============================================================================
# JADWAL PENUGASAN OPERASIONAL PENGEMUDI
# ==============================================================================
@router.get(
    "/jadwal",
    tags=["Pengemudi - Akun & Jadwal"],
    summary="Jadwal Penugasan Operasional Pengemudi",
)
def get_jadwal_hari_ini(email_supir: str = Depends(verifikasi_pengemudi)):

    """
    Menampilkan batas waktu toleransi keberangkatan dan kedatangan
    berdasarkan rute/trayek yang ditugaskan kepada pengemudi saat ini.
    """
    try:
        user_response = (
            supabase.table("users")
            .select("trayek, bus")
            .eq("email", email_supir)
            .execute()
        )

        if not user_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Data akun pengemudi tidak ditemukan.",
            )

        user_data = user_response.data[0]
        trayek_supir = user_data.get("trayek")

        if not trayek_supir:
            return {
                "pesan": "Anda belum ditugaskan ke rute/trayek mana pun hari ini.",
                "trayek": None,
                "bus": user_data.get("bus"),
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
            "trayek": trayek_supir,
            "bus": user_data.get("bus"),
            "data": jadwal_response.data,
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan teknis saat menarik jadwal operasional: {str(e)}",
        )


# ==============================================================================
# PENUGASAN KENDARAAN (SUGESTI DRIVER)
# ==============================================================================
@router.get(
    "/penugasan/hari-ini",
    tags=["Pengemudi - Akun & Jadwal"],
    summary="Data Penugasan Kendaraan Hari Ini (Sugesti)",
)
def get_penugasan_hari_ini(email_supir: str = Depends(verifikasi_pengemudi)):
    """
    Menarik data Nopol, Jenis Kendaraan, Kapasitas, dan Trayek 
    yang ditugaskan oleh admin khusus untuk hari ini.
    """
    try:
        # Cari ID supir dari email
        user_response = (
            supabase.table("users")
            .select("id")
            .eq("email", email_supir)
            .execute()
        )
        if not user_response.data:
            raise HTTPException(status_code=404, detail="Akun pengemudi tidak ditemukan.")
            
        id_supir = user_response.data[0]["id"]
        tanggal_hari_ini = str(date.today())
        
        penugasan_response = (
            supabase.table("penugasan")
            .select("*")
            .eq("id_supir", id_supir)
            .eq("tanggal", tanggal_hari_ini)
            .execute()
        )
        
        if not penugasan_response.data:
            return {
                "pesan": "Belum ada penugasan kendaraan untuk Anda hari ini.",
                "data": None
            }
            
        return {
            "pesan": "Data penugasan kendaraan hari ini berhasil ditarik.",
            "data": penugasan_response.data[0]
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal menarik data penugasan: {str(e)}",
        )

