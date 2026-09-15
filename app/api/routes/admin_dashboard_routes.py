from fastapi import APIRouter, Depends
from app.api.dependencies import verifikasi_admin
from app.services import admin_dashboard_service

router = APIRouter()

@router.get(
    "/dashboard",
    tags=["Admin - Dashboard & Rekap"],
    summary="Statistik Ringkasan Dashboard",
)
def get_dashboard(email_admin: str = Depends(verifikasi_admin)):
    return admin_dashboard_service.get_dashboard_metrics()


@router.get(
    "/rekap",
    tags=["Admin - Dashboard & Rekap"],
    summary="Rekapitulasi Operasional Keseluruhan",
)
def get_rekap(email_admin: str = Depends(verifikasi_admin)):
    return admin_dashboard_service.get_rekap_operasional()


@router.get(
    "/riwayat-harian",
    tags=["Admin - Dashboard & Rekap"],
    summary="Riwayat Operasional per Tanggal",
)
def get_riwayat_harian(email_admin: str = Depends(verifikasi_admin)):
    return admin_dashboard_service.get_riwayat_harian_grouped()
