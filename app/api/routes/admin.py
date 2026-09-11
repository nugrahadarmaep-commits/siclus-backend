# ==============================================================================
# ROUTE: ADMINISTRATOR
# ==============================================================================

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

from app.core.config import settings
from app.schemas.user import UserRegister, UserUpdate, AdminProfileUpdate
from app.schemas.jadwal import JadwalCreate, JadwalUpdate
from app.schemas.penugasan import PenugasanCreate, PenugasanUpdate
from app.services import admin_service

router = APIRouter()
security = HTTPBearer()


# ==============================================================================
# VERIFIKASI KEAMANAN ADMIN
# ==============================================================================
def verifikasi_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
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
                detail="Akses ditolak. Endpoint eksklusif untuk Administrator.",
            )
        return email_user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Sesi kedaluwarsa.")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token tidak valid.")


# ==============================================================================
# DASHBOARD & REKAP OPERASIONAL
# ==============================================================================
@router.get(
    "/dashboard",
    tags=["Admin - Dashboard & Rekap"],
    summary="Statistik Ringkasan Dashboard",
)
def get_dashboard(email_admin: str = Depends(verifikasi_admin)):
    return admin_service.get_dashboard_metrics()


@router.get(
    "/rekap",
    tags=["Admin - Dashboard & Rekap"],
    summary="Rekapitulasi Operasional Keseluruhan",
)
def get_rekap(email_admin: str = Depends(verifikasi_admin)):
    return admin_service.get_rekap_operasional()


@router.get(
    "/riwayat-harian",
    tags=["Admin - Dashboard & Rekap"],
    summary="Riwayat Operasional per Tanggal",
)
def get_riwayat_harian(email_admin: str = Depends(verifikasi_admin)):
    return admin_service.get_riwayat_harian_grouped()


@router.get(
    "/export-excel",
    tags=["Admin - Dashboard & Rekap"],
    summary="Unduh Laporan Format Excel (.xlsx)",
)
def export_excel(
    id_supir: Optional[str] = None, email_admin: str = Depends(verifikasi_admin)
):
    return admin_service.export_rekap_to_excel(id_supir=id_supir)


# ==============================================================================
# MANAJEMEN AKUN DRIVER (SUPIR)
# ==============================================================================
@router.get(
    "/users",
    tags=["Admin - Manajemen Pengemudi"],
    summary="Daftar Seluruh Akun Pengemudi",
)
def get_semua_driver(email_admin: str = Depends(verifikasi_admin)):
    return admin_service.get_all_drivers()


@router.post(
    "/users",
    tags=["Admin - Manajemen Pengemudi"],
    summary="Tambah Akun Pengemudi Baru",
)
def tambah_driver(data: UserRegister, email_admin: str = Depends(verifikasi_admin)):
    return admin_service.create_driver(data)


@router.put(
    "/users/{user_id}",
    tags=["Admin - Manajemen Pengemudi"],
    summary="Perbarui Data Akun Pengemudi",
)
def edit_driver(
    user_id: str, data: UserUpdate, email_admin: str = Depends(verifikasi_admin)
):
    return admin_service.update_driver(user_id, data)


@router.delete(
    "/users/{user_id}",
    tags=["Admin - Manajemen Pengemudi"],
    summary="Hapus Akun Pengemudi",
)
def hapus_driver(user_id: str, email_admin: str = Depends(verifikasi_admin)):
    return admin_service.delete_driver(user_id)


# ==============================================================================
# MANAJEMEN JADWAL OPERASIONAL
# ==============================================================================
@router.get(
    "/jadwal",
    tags=["Admin - Manajemen Jadwal"],
    summary="Daftar Seluruh Jadwal Operasional",
)
def get_semua_jadwal(email_admin: str = Depends(verifikasi_admin)):
    return admin_service.get_all_schedules()


@router.post(
    "/jadwal",
    tags=["Admin - Manajemen Jadwal"],
    summary="Tambah Jadwal Rute Baru",
)
def tambah_jadwal(data: JadwalCreate, email_admin: str = Depends(verifikasi_admin)):
    return admin_service.create_schedule(data)


@router.put(
    "/jadwal/{jadwal_id}",
    tags=["Admin - Manajemen Jadwal"],
    summary="Perbarui Jadwal Operasional",
)
def edit_jadwal(
    jadwal_id: str, data: JadwalUpdate, email_admin: str = Depends(verifikasi_admin)
):
    return admin_service.update_schedule(jadwal_id, data)


@router.delete(
    "/jadwal/{jadwal_id}",
    tags=["Admin - Manajemen Jadwal"],
    summary="Hapus Jadwal Operasional",
)
def hapus_jadwal(jadwal_id: str, email_admin: str = Depends(verifikasi_admin)):
    return admin_service.delete_schedule(jadwal_id)


# ==============================================================================
# PROFIL AKUN ADMIN
# ==============================================================================
@router.put(
    "/profil",
    tags=["Admin - Profil"],
    summary="Perbarui Nama Profil Administrator",
)
def update_profil_admin(
    data: AdminProfileUpdate, email_admin: str = Depends(verifikasi_admin)
):
    return admin_service.update_admin_profile(email_admin, data)


@router.put(
    "/profil/foto",
    tags=["Admin - Profil"],
    summary="Unggah Foto Profil Administrator",
)
async def update_foto_profil_admin(
    foto: UploadFile = File(...), email_admin: str = Depends(verifikasi_admin)
):
    return await admin_service.update_admin_avatar(email_admin, foto)


# ==============================================================================
# MANAJEMEN PENUGASAN KENDARAAN (HARIAN)
# ==============================================================================
@router.get(
    "/penugasan",
    tags=["Admin - Penugasan"],
    summary="Lihat Semua Penugasan Kendaraan Harian",
)
def get_semua_penugasan(email_admin: str = Depends(verifikasi_admin)):
    return admin_service.get_semua_penugasan()


@router.post(
    "/penugasan",
    tags=["Admin - Penugasan"],
    summary="Buat/Update Penugasan Kendaraan Harian untuk Supir",
)
def create_penugasan_harian(
    data: PenugasanCreate, email_admin: str = Depends(verifikasi_admin)
):
    return admin_service.create_penugasan_harian(data)


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
    return admin_service.update_penugasan_harian(id_penugasan, data)


@router.delete(
    "/penugasan/{id_penugasan}",
    tags=["Admin - Penugasan"],
    summary="Hapus Penugasan Kendaraan Harian",
)
def delete_penugasan_harian(
    id_penugasan: str, email_admin: str = Depends(verifikasi_admin)
):
    return admin_service.delete_penugasan_harian(id_penugasan)
