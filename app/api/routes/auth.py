from fastapi import APIRouter
from app.schemas.user import UserLogin
from app.services.auth_service import proses_login_supir

router = APIRouter()


@router.post("/login")
def login(data: UserLogin):
    hasil_login = proses_login_supir(data)
    return hasil_login
