import time
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File

from app.api.dependencies import verifikasi_token
from app.db.database import supabase
from app.schemas.laporan import LaporanHarianCreate
from app.schemas.inspeksi import InspeksiCreate
from app.schemas.perjalanan import (
    SesiCP1Create,
    SesiCP2Update,
    SesiCP3Update,
)
from app.services.driver_service import get_driver_active_report
from app.services.laporan_service import (
    create_laporan_harian,
    create_inspeksi_kendaraan,
    proses_cp1,
    proses_cp2,
    proses_cp3,
)

router = APIRouter()


# laporan harian aktif hari ini
@router.get(
    "/hari-ini",
    tags=["Pengemudi - Operasional Harian"],
    summary="Ambil Laporan Operasional Pengemudi Hari Ini",
)
def get_laporan_hari_ini(
    trayek: Optional[str] = None,
    bus: Optional[str] = None,
    laporan_id: Optional[str] = None,
    email_supir: str = Depends(verifikasi_token),
):
    try:
        report = get_driver_active_report(
            email_supir=email_supir,
            trayek=trayek,
            bus=bus,
            laporan_id=laporan_id,
        )
        return {"status": "sukses", "data": report}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal mengambil laporan hari ini: {str(e)}",
        )


# inisialisasi laporan harian
@router.post(
    "/mulai",
    tags=["Pengemudi - Operasional Harian"],
    summary="Mulai Sesi Laporan Harian Pengemudi",
)
def mulai_laporan(
    data: LaporanHarianCreate, email_supir: str = Depends(verifikasi_token)
):
    return create_laporan_harian(data, email_supir)


# inspeksi kelayakan armada bus
@router.post(
    "/inspeksi",
    tags=["Pengemudi - Operasional Harian"],
    summary="Kirim Hasil Inspeksi Armada Bus",
)
def inspeksi_kendaraan(
    laporan_id: str, data: InspeksiCreate, email_supir: str = Depends(verifikasi_token)
):
    return create_inspeksi_kendaraan(laporan_id, data)


# checkpoint 1: keluar garasi dishub
@router.post(
    "/sesi/cp1",
    tags=["Pengemudi - Operasional Harian"],
    summary="Simpan Checkpoint 1 (Keluar Garasi Dishub)",
)
def sesi_checkpoint_1(
    laporan_id: str, data: SesiCP1Create, email_supir: str = Depends(verifikasi_token)
):
    return proses_cp1(laporan_id, data, email_supir)


# checkpoint 2: tiba di titik akhir rute / sekolah
@router.put(
    "/sesi/cp2/{sesi_id}",
    tags=["Pengemudi - Operasional Harian"],
    summary="Simpan Checkpoint 2 (Tiba di Titik Finish Rute / Sekolah)",
)
def sesi_checkpoint_2(
    sesi_id: str, data: SesiCP2Update, email_supir: str = Depends(verifikasi_token)
):
    return proses_cp2(sesi_id, data, email_supir)


# checkpoint 3: kembali ke garasi dishub
@router.put(
    "/sesi/cp3/{sesi_id}",
    tags=["Pengemudi - Operasional Harian"],
    summary="Simpan Checkpoint 3 (Kembali Masuk Garasi Dishub)",
)
def sesi_checkpoint_3(
    sesi_id: str, data: SesiCP3Update, email_supir: str = Depends(verifikasi_token)
):
    return proses_cp3(sesi_id, data, email_supir)


# validasi swafoto (selfie) kehadiran pengemudi
@router.post(
    "/upload-selfie",
    tags=["Pengemudi - Operasional Harian"],
    summary="Unggah Swafoto (Selfie) Kehadiran Pengemudi",
)
async def upload_selfie(
    foto: UploadFile = File(...), email_supir: str = Depends(verifikasi_token)
):
    try:
        ekstensi = foto.filename.split(".")[-1].lower() if "." in foto.filename else ""
        if ekstensi not in ["jpg", "jpeg", "png", "webp"]:
            if foto.content_type in ["image/jpeg", "image/jpg"]:
                ekstensi = "jpg"
            elif foto.content_type == "image/png":
                ekstensi = "png"
            elif foto.content_type == "image/webp":
                ekstensi = "webp"
            else:
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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan teknis saat mengunggah foto: {str(e)}",
        )
