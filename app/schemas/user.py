from typing import Optional
from pydantic import BaseModel, EmailStr


# Skema ini menerima email atau id pengemudi beserta password.
class UserLogin(BaseModel):
    email: Optional[str] = None
    id: Optional[str] = None
    password: str


# profil driver
class UserResponse(BaseModel):
    id: str
    nama_lengkap: str
    email: EmailStr
    role: str
    trayek: Optional[str] = None
    bus: Optional[str] = None

    class Config:
        from_attributes = True

# register tambah driver baru
class UserRegister(BaseModel):
    id: str
    nama_lengkap: str
    email: EmailStr
    password: str
    role: str = "driver"
    trayek: Optional[str] = None
    bus: Optional[str] = None

# edit data supir baru
class UserUpdate(BaseModel):
    nama_lengkap: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[str] = None
    trayek: Optional[str] = None
    bus: Optional[str] = None
    