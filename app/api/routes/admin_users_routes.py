from fastapi import APIRouter, Depends, UploadFile, File
from app.api.dependencies import verifikasi_admin
from app.services import admin_users_service
from app.schemas.user import UserRegister, UserUpdate, AdminProfileUpdate

router = APIRouter()

@router.get(
    "/users",
    tags=["Admin - Manajemen Pengemudi"],
    summary="Daftar Seluruh Akun Pengemudi",
)
def get_semua_driver(email_admin: str = Depends(verifikasi_admin)):
    return admin_users_service.get_all_drivers()


@router.post(
    "/users",
    tags=["Admin - Manajemen Pengemudi"],
    summary="Tambah Akun Pengemudi Baru",
)
def tambah_driver(data: UserRegister, email_admin: str = Depends(verifikasi_admin)):
    return admin_users_service.create_driver(data)


@router.put(
    "/users/{user_id}",
    tags=["Admin - Manajemen Pengemudi"],
    summary="Perbarui Data Akun Pengemudi",
)
def edit_driver(
    user_id: str, data: UserUpdate, email_admin: str = Depends(verifikasi_admin)
):
    return admin_users_service.update_driver(user_id, data)


@router.delete(
    "/users/{user_id}",
    tags=["Admin - Manajemen Pengemudi"],
    summary="Hapus Akun Pengemudi",
)
def hapus_driver(user_id: str, email_admin: str = Depends(verifikasi_admin)):
    return admin_users_service.delete_driver(user_id)


@router.put(
    "/profil",
    tags=["Admin - Profil"],
    summary="Perbarui Nama Profil Administrator",
)
def update_profil_admin(
    data: AdminProfileUpdate, email_admin: str = Depends(verifikasi_admin)
):
    return admin_users_service.update_admin_profile(email_admin, data)


@router.put(
    "/profil/foto",
    tags=["Admin - Profil"],
    summary="Unggah Foto Profil Administrator",
)
async def update_foto_profil_admin(
    foto: UploadFile = File(...), email_admin: str = Depends(verifikasi_admin)
):
    return await admin_users_service.update_admin_avatar(email_admin, foto)
