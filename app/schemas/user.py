from typing import Optional
from pydantic import BaseModel, EmailStr


# ==========================================
# 1. CETAKAN DATA UNTUK LOGIN (REQUEST)
# ==========================================
# Skema ini memastikan data yang dikirim dari Frontend (Cevin)
# wajib memiliki format email yang valid dan password.
class UserLogin(BaseModel):
    email: EmailStr
    password: str


# ==========================================
# 2. CETAKAN PROFIL PENGGUNA (RESPONSE)
# ==========================================
# Skema ini mengatur data apa saja yang boleh dikembalikan ke Frontend.
# Sistem secara ketat menghilangkan password demi keamanan.
class UserResponse(BaseModel):
    id: str
    nama_lengkap: str
    email: EmailStr
    role: str

    trayek: Optional[str] = None
    bus: Optional[str] = None

    class Config:
        from_attributes = True


# ==========================================
# 3. CETAKAN UNTUK DAFTAR SUPIR BARU (REGISTER)
# ==========================================
# Skema ini bakal dipake sama Admin buat masukin data supir baru ke sistem
class UserRegister(BaseModel):
    id: str
    nama_lengkap: str
    email: EmailStr
    password: str
    role: str = "pengemudi"
    trayek: Optional[str] = None
    bus: Optional[str] = None
