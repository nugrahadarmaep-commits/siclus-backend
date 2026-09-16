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
    "/operasional-hari-ini",
    tags=["Admin - Dashboard & Rekap"],
    summary="Operasional Driver Hari Ini",
)
def get_operasional_hari_ini(email_admin: str = Depends(verifikasi_admin)):
    return admin_dashboard_service.get_operasional_hari_ini()
