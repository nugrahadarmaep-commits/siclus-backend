# ==============================================================================
# ROUTE: AUTENTIKASI (LOGIN)
# ==============================================================================

from fastapi import APIRouter
from app.schemas.user import UserLogin
from app.services.auth_service import proses_login_supir

router = APIRouter(tags=["Autentikasi"])


@router.post("/login", summary="Masuk ke Sistem (Login)")
def login(data: UserLogin):
    return proses_login_supir(data)
