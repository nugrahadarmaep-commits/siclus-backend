from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import time

from app.schemas.laporan import LaporanHarianCreate
from app.schemas.inspeksi import InspeksiCreate
from app.schemas.perjalanan import (
    SesiCP1Create,
    SesiCP2Update,
    SesiCP3Update,
    SesiCP4Update,
)
from app.services.laporan_service import (
    create_laporan_harian,
    create_inspeksi_kendaraan,
    proses_cp1,
    proses_cp2,
    proses_cp3,
    proses_cp4,
)
from app.core.config import settings
from app.db.database import supabase

router = APIRouter()
security = HTTPBearer()


# verifikasitoken
def verifikasi_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
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


# inspeksi laporan harian driver
@router.post("/mulai")
def mulai_laporan(
    data: LaporanHarianCreate, email_supir: str = Depends(verifikasi_token)
):
    return create_laporan_harian(data, email_supir)


# inspeksi
@router.post("/inspeksi")
def inspeksi_kendaraan(
    laporan_id: str, data: InspeksiCreate, email_supir: str = Depends(verifikasi_token)
):
    return create_inspeksi_kendaraan(laporan_id, data)


# sesicp1
@router.post("/sesi/cp1")
def sesi_checkpoint_1(
    laporan_id: str, data: SesiCP1Create, email_supir: str = Depends(verifikasi_token)
):
    return proses_cp1(laporan_id, data, email_supir)


# sesicp2
@router.put("/sesi/cp2/{sesi_id}")
def sesi_checkpoint_2(
    sesi_id: str, data: SesiCP2Update, email_supir: str = Depends(verifikasi_token)
):
    return proses_cp2(sesi_id, data, email_supir)


# sesicp3
@router.put("/sesi/cp3/{sesi_id}")
def sesi_checkpoint_3(
    sesi_id: str, data: SesiCP3Update, email_supir: str = Depends(verifikasi_token)
):
    return proses_cp3(sesi_id, data, email_supir)


# sesicp4
@router.put("/sesi/cp4/{sesi_id}")
def sesi_checkpoint_4(
    sesi_id: str, data: SesiCP4Update, email_supir: str = Depends(verifikasi_token)
):
    return proses_cp4(sesi_id, data, email_supir)


# uploadselfie
@router.post("/upload-selfie")
async def upload_selfie(
    foto: UploadFile = File(...), email_supir: str = Depends(verifikasi_token)
):
    try:
        ekstensi = foto.filename.split(".")[-1].lower()
        if ekstensi not in ["jpg", "jpeg", "png", "webp"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Format file tidak didukung. Harap gunakan JPG, JPEG, PNG, atau WEBP.",
            )

        nama_prefix = email_supir.split("@")[0]
        nama_file_baru = f"{nama_prefix}_{int(time.time())}.{ekstensi}"

        isi_gambar = await foto.read()

        supabase.storage.from_("selfie_driver").upload(
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
