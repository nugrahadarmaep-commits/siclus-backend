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


# ==========================================
# FUNGSI KEAMANAN: VERIFIKASI TOKEN PENGEMUDI
# ==========================================
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


# ==========================================
# ENDPOINT: DATA PROFIL PENGEMUDI
# ==========================================
@router.get("/profil")
def get_profil_pengemudi(email_supir: str = Depends(verifikasi_pengemudi)):
    """
    Menarik data identitas dan penugasan pengemudi (Nama, Trayek, Armada)
    dari database berdasarkan email yang terekstrak dari Token JWT aktif.
    """
    try:
        # Menarik data spesifik dari tabel users berdasarkan email
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


# ==========================================
# ENDPOINT: UBAH FOTO PROFIL PENGEMUDI
# ==========================================
@router.put("/profil/foto")
async def update_foto_profil(
    foto: UploadFile = File(...), email_supir: str = Depends(verifikasi_pengemudi)
):
    """
    Mengunggah foto profil baru ke penyimpanan awan dan memperbarui
    tautan (URL) foto tersebut di tabel profil pengguna.
    """
    try:
        # 1. Validasi keamanan ekstensi file
        ekstensi = foto.filename.split(".")[-1].lower()
        if ekstensi not in ["jpg", "jpeg", "png"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Format tidak didukung. Gunakan JPG, JPEG, atau PNG.",
            )

        # 2. Bikin nama file unik biar kaga ketumpuk
        nama_prefix = email_supir.split("@")[0]
        nama_file_baru = f"avatar_{nama_prefix}_{int(time.time())}.{ekstensi}"

        # 3. Baca dan lempar gambar ke bucket 'foto_profil'
        isi_gambar = await foto.read()
        response_storage = supabase.storage.from_("foto_profil").upload(
            file=isi_gambar,
            path=nama_file_baru,
            file_options={"content-type": foto.content_type},
        )

        # 4. Ambil URL publiknya
        url_publik = supabase.storage.from_("foto_profil").get_public_url(
            nama_file_baru
        )

        # 5. SIMPAN URL TERSEBUT KE TABEL USERS (Ini yang bedain sama selfie biasa!)
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


# ==========================================
# ENDPOINT: RIWAYAT PERJALANAN PENGEMUDI
# ==========================================
@router.get("/riwayat")
def get_riwayat_pengemudi(email_supir: str = Depends(verifikasi_pengemudi)):
    """
    Menarik histori laporan operasional khusus untuk pengemudi yang sedang aktif.
    Dilengkapi sistem filter ketat untuk mencegah kebocoran data antar pengemudi.
    """
    try:
        # Menarik data laporan utama beserta detail sesinya (Pagi/Siang).
        # WAJIB pake .eq() buat nge-filter milik supir ini aja!
        # Pake .order() biar laporan paling baru muncul di paling atas list FE.
        response = (
            supabase.table("daily_reports")
            .select("*, trip_sessions(*)")
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


# ==========================================
# ENDPOINT: JADWAL OPERASIONAL PENGEMUDI
# ==========================================
@router.get("/jadwal")
def get_jadwal_hari_ini(email_supir: str = Depends(verifikasi_pengemudi)):
    """
    Menarik jadwal operasional dan batas waktu toleransi (cut-off time)
    berdasarkan rute/trayek yang ditugaskan kepada pengemudi saat ini.
    """
    try:
        # 1. Cari tau dulu pengemudi ini ditugaskan di Trayek apa
        user_response = (
            supabase.table("users").select("trayek").eq("email", email_supir).execute()
        )

        if not user_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Data akun pengemudi tidak ditemukan.",
            )

        trayek_supir = user_response.data[0].get("trayek")

        # Jika admin belum ngasih trayek ke supir ini
        if not trayek_supir:
            return {
                "pesan": "Anda belum ditugaskan ke rute/trayek mana pun hari ini.",
                "data": [],
            }

        # 2. Tarik jadwal dari tabel schedules berdasarkan trayek supir
        # Pake 'ilike' biar pencariannya kebal huruf besar/kecil (Trayek A = trayek a)
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
