from fastapi import APIRouter, Depends
from app.api.dependencies import verifikasi_admin
from app.services import admin_penugasan_service
from app.schemas.penugasan import PenugasanCreate, PenugasanUpdate

router = APIRouter()


@router.get(
    "/penugasan",
    tags=["Admin - Penugasan"],
    summary="Lihat Semua Penugasan Kendaraan Harian",
)
def get_semua_penugasan(email_admin: str = Depends(verifikasi_admin)):
    return admin_penugasan_service.get_semua_penugasan()


@router.post(
    "/penugasan",
    tags=["Admin - Penugasan"],
    summary="Buat/Update Penugasan Kendaraan Harian untuk Supir",
)
def create_penugasan_harian(
    data: PenugasanCreate, email_admin: str = Depends(verifikasi_admin)
):
    return admin_penugasan_service.create_penugasan_harian(data)


@router.put(
    "/penugasan/{id_penugasan}",
    tags=["Admin - Penugasan"],
    summary="Update Penugasan Kendaraan Harian untuk Supir",
)
def update_penugasan_harian(
    id_penugasan: str,
    data: PenugasanUpdate,
    email_admin: str = Depends(verifikasi_admin),
):
    return admin_penugasan_service.update_penugasan_harian(id_penugasan, data)


@router.delete(
    "/penugasan/{id_penugasan}",
    tags=["Admin - Penugasan"],
    summary="Hapus Penugasan Kendaraan Harian",
)
def delete_penugasan_harian(
    id_penugasan: str, email_admin: str = Depends(verifikasi_admin)
):
    return admin_penugasan_service.delete_penugasan_harian(id_penugasan)


@router.post(
    "/penugasan/{id_penugasan}/batal",
    tags=["Admin - Penugasan"],
    summary="Batalkan Sisa Operasional Penugasan Supir",
)
def batalkan_operasional_penugasan(
    id_penugasan: str, email_admin: str = Depends(verifikasi_admin)
):
    return admin_penugasan_service.batalkan_operasional_penugasan(id_penugasan)
