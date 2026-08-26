from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import time

from app.schemas.laporan import LaporanHarianCreate
from app.schemas.inspeksi import InspeksiCreate
from app.schemas.perjalanan import TripSessionCreate
from app.services.laporan_service import (
    create_laporan_harian,
    create_inspeksi_kendaraan,
    create_sesi_perjalanan,
)
from app.core.config import settings
from app.db.database import supabase

router = APIRouter()
security = HTTPBearer()


# ─── FUNGSI KEAMANAN: VERIFIKASI TOKEN JWT ────────────────────────────
def verifikasi_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Fungsi otorisasi yang dieksekusi sebelum endpoint utama diproses.
    Bertugas melakukan dekode JWT dan memvalidasi kredensial pengguna.
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        email_supir = payload.get("sub")

        if email_supir is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Kredensial tidak valid. Payload token kosong.",
            )

        return email_supir

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


# ─── ENDPOINT: INISIALISASI LAPORAN HARIAN ────────────────────────────
@router.post("/mulai")
def mulai_laporan(
    data: LaporanHarianCreate, email_supir: str = Depends(verifikasi_token)
):
    """
    Membuat entri data awal untuk laporan harian operasional pengemudi.
    """
    hasil = create_laporan_harian(data, email_supir)
    return hasil


# ─── ENDPOINT: PENGISIAN DATA INSPEKSI ────────────────────────────────
@router.post("/inspeksi")
def inspeksi_kendaraan(
    laporan_id: str, data: InspeksiCreate, email_supir: str = Depends(verifikasi_token)
):
    """
    Menyimpan hasil pemeriksaan kelaikan kondisi fisik kendaraan.
    """
    hasil = create_inspeksi_kendaraan(laporan_id, data)
    return hasil


# ─── ENDPOINT: PENGISIAN SESI PERJALANAN ──────────────────────────────
@router.post("/sesi")
def sesi_perjalanan(
    laporan_id: str,
    data: TripSessionCreate,
    email_supir: str = Depends(verifikasi_token),
):
    """
    Merekam data odometer dan waktu operasi untuk rute perjalanan pengemudi.
    """
    hasil = create_sesi_perjalanan(laporan_id, data)
    return hasil


# ─── ENDPOINT: UNGGAH FOTO KEHADIRAN (SELFIE) ─────────────────────────
@router.post("/upload-selfie")
async def upload_selfie(
    foto: UploadFile = File(...), email_supir: str = Depends(verifikasi_token)
):
    """
    Menerima file gambar (selfie) untuk validasi kehadiran,
    mengunggahnya ke infrastruktur penyimpanan (Storage),
    dan mengembalikan URL akses publik.
    """
    try:
        ekstensi = foto.filename.split(".")[-1].lower()
        if ekstensi not in ["jpg", "jpeg", "png"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Format file tidak didukung. Harap gunakan JPG, JPEG, atau PNG.",
            )

        nama_prefix = email_supir.split("@")[0]
        nama_file_baru = f"{nama_prefix}_{int(time.time())}.{ekstensi}"

        isi_gambar = await foto.read()

        response = supabase.storage.from_("selfie_driver").upload(
            file=isi_gambar,
            path=nama_file_baru,
            file_options={"content-type": foto.content_type},
        )

        url_publik = supabase.storage.from_("selfie_driver").get_public_url(
            nama_file_baru
        )

        return {
            "pesan": "Foto validasi kehadiran berhasil diunggah.",
            "url_foto": url_publik,
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan teknis saat mengunggah foto: {str(e)}",
        )
