from typing import Optional
from pydantic import BaseModel, EmailStr


# ─── SCHEMA: DATA LOGIN PENGGUNA (REQUEST) ────────────────────────────
# Skema ini memastikan data yang dikirim dari Frontend (Cevin)
# wajib memiliki format email yang valid dan password.
class UserLogin(BaseModel):
    email: EmailStr
    password: str


# ─── SCHEMA: PROFIL PENGGUNA (RESPONSE) ───────────────────────────────
class UserResponse(BaseModel):
    id: str
    nama_lengkap: str
    email: EmailStr
    role: str

    trayek: Optional[str] = None
    bus: Optional[str] = None

    class Config:
        from_attributes = True


# ─── SCHEMA: REGISTRASI SUPIR BARU (REGISTER) ─────────────────────────
class UserRegister(BaseModel):
    id: str
    nama_lengkap: str
    email: EmailStr
    password: str
    role: str = "pengemudi"
    trayek: Optional[str] = None
    bus: Optional[str] = None

# ─── SCHEMA: EDIT DATA SUPIR (UPDATE) ─────────────────────────────────
class UserUpdate(BaseModel):
    nama_lengkap: Optional[str] = None
    email: Optional[EmailStr] = None
    trayek: Optional[str] = None
    bus: Optional[str] = None