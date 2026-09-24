from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File
from app.api.dependencies import verifikasi_admin, verifikasi_master_admin
from app.services import admin_users_service
from app.schemas.user import (
    UserRegister,
    UserUpdate,
    AdminProfileUpdate,
    AdminDeleteDriverConfirm,
    AdminStaffCreate,
    AdminStaffUpdate,
)

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
    return admin_users_service.update_driver(user_id, data, email_admin)


@router.delete(
    "/users/{user_id}",
    tags=["Admin - Manajemen Pengemudi"],
    summary="Hapus Akun Pengemudi",
)
def hapus_driver(
    user_id: str,
    data: Optional[AdminDeleteDriverConfirm] = None,
    email_admin: str = Depends(verifikasi_admin),
):
    if data and data.password_admin:
        return admin_users_service.delete_driver(
            user_id, data.email_admin or email_admin, data.password_admin
        )
    return admin_users_service.delete_driver(user_id)


@router.post(
    "/users/{user_id}/hapus",
    tags=["Admin - Manajemen Pengemudi"],
    summary="Hapus Akun Pengemudi dengan Verifikasi Kredensial Admin",
)
def hapus_driver_dengan_verifikasi(
    user_id: str,
    data: AdminDeleteDriverConfirm,
    email_admin: str = Depends(verifikasi_admin),
):
    return admin_users_service.delete_driver(
        user_id, data.email_admin or email_admin, data.password_admin
    )



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


@router.get(
    "/staf",
    tags=["Admin - Kelola Staf Admin"],
    summary="Daftar Seluruh Staf Administrator",
)
def get_semua_staf_admin(email_admin: str = Depends(verifikasi_master_admin)):
    return admin_users_service.get_all_admin_staff()


@router.post(
    "/staf",
    tags=["Admin - Kelola Staf Admin"],
    summary="Tambah Akun Staf Administrator Baru",
)
def tambah_staf_admin(
    data: AdminStaffCreate, email_admin: str = Depends(verifikasi_master_admin)
):
    return admin_users_service.create_admin_staff(data)


@router.put(
    "/staf/{user_id}",
    tags=["Admin - Kelola Staf Admin"],
    summary="Perbarui Data Akun Staf Administrator",
)
def edit_staf_admin(
    user_id: str,
    data: AdminStaffUpdate,
    email_admin: str = Depends(verifikasi_master_admin),
):
    return admin_users_service.update_admin_staff(user_id, data, email_admin)


@router.delete(
    "/staf/{user_id}",
    tags=["Admin - Kelola Staf Admin"],
    summary="Hapus Akun Staf Administrator",
)
def hapus_staf_admin(
    user_id: str,
    data: Optional[AdminDeleteDriverConfirm] = None,
    email_admin: str = Depends(verifikasi_master_admin),
):
    if data and data.password_admin:
        return admin_users_service.delete_admin_staff(
            user_id, data.email_admin or email_admin, data.password_admin
        )
    return admin_users_service.delete_admin_staff(user_id, email_admin)


@router.post(
    "/staf/{user_id}/hapus",
    tags=["Admin - Kelola Staf Admin"],
    summary="Hapus Akun Staf Administrator dengan Verifikasi Kredensial Admin",
)
def hapus_staf_admin_dengan_verifikasi(
    user_id: str,
    data: AdminDeleteDriverConfirm,
    email_admin: str = Depends(verifikasi_master_admin),
):
    return admin_users_service.delete_admin_staff(
        user_id, data.email_admin or email_admin, data.password_admin
    )


