from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


# Skema ini menerima email atau id pengemudi beserta password.
class UserLogin(BaseModel):
    email: Optional[str] = None
    id: Optional[str] = None
    password: str = Field(..., min_length=8, description="Password minimal 8 karakter")


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
    password: str = Field(..., min_length=8, description="Password minimal 8 karakter")
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

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.strip() != "":
            if len(v.strip()) < 8:
                raise ValueError("Password baru minimal 8 karakter")
        return v


# update profil pribadi admin (nama)
class AdminProfileUpdate(BaseModel):
    nama_lengkap: str