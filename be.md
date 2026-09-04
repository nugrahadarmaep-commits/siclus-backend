# SICLUS Backend - Source Code Documentation

Dokumentasi lengkap seluruh file source code proyek **SICLUS Backend** terbaru (Update 2 September 2026) murni tanpa modifikasi kode.

---

## 📁 Struktur Direktori Proyek

```text
siclus-backend/
├── .env.example
├── .gitignore
├── .python-version
├── pyproject.toml
├── be.md
└── app/
    ├── __init__.py
    ├── main.py
    ├── api/
    │   ├── __init__.py
    │   └── routes/
    │       ├── __init__.py
    │       ├── admin.py
    │       ├── auth.py
    │       ├── driver.py
    │       └── laporan.py
    ├── core/
    │   ├── __init__.py
    │   ├── config.py
    │   └── security.py
    ├── db/
    │   ├── __init__.py
    │   └── database.py
    ├── schemas/
    │   ├── __init__.py
    │   ├── inspeksi.py
    │   ├── jadwal.py
    │   ├── laporan.py
    │   ├── perjalanan.py
    │   └── user.py
    └── services/
        ├── __init__.py
        ├── auth_service.py
        └── laporan_service.py
```

---

## 📑 Daftar Isi

### ⚙️ Konfigurasi & Lingkungan
- [`pyproject.toml`](#1-pyprojecttoml)
- [`.env.example`](#2-envexample)
- [`.gitignore`](#3-gitignore)
- [`.python-version`](#4-python-version)

### 🚀 Entry Point Aplikasi
- [`app/__init__.py`](#5-app__init__py)
- [`app/main.py`](#6-appmainpy)

### 🛡️ Core & Keamanan
- [`app/core/__init__.py`](#7-appcore__init__py)
- [`app/core/config.py`](#8-appcoreconfigpy)
- [`app/core/security.py`](#9-appcoresecuritypy)

### 🗄️ Database
- [`app/db/__init__.py`](#10-appdb__init__py)
- [`app/db/database.py`](#11-appdbdatabasepy)

### 📋 Schemas (Pydantic)
- [`app/schemas/__init__.py`](#12-appschemas__init__py)
- [`app/schemas/user.py`](#13-appschemasuserpy)
- [`app/schemas/inspeksi.py`](#14-appschemasinspeksipy)
- [`app/schemas/jadwal.py`](#15-appschemasjadwalpy)
- [`app/schemas/perjalanan.py`](#16-appschemasperjalananpy)
- [`app/schemas/laporan.py`](#17-appschemaslaporanpy)

### ⚙️ Services (Business Logic)
- [`app/services/__init__.py`](#18-appservices__init__py)
- [`app/services/auth_service.py`](#19-appservicesauth_servicepy)
- [`app/services/laporan_service.py`](#20-appserviceslaporan_servicepy)

### 🌐 API Routes (Endpoints)
- [`app/api/__init__.py`](#21-appapi__init__py)
- [`app/api/routes/__init__.py`](#22-appapiroutes__init__py)
- [`app/api/routes/auth.py`](#23-appapiroutesauthpy)
- [`app/api/routes/admin.py`](#24-appapiroutesadminpy)
- [`app/api/routes/driver.py`](#25-appapiroutesdriverpy)
- [`app/api/routes/laporan.py`](#26-appapirouteslaporanpy)

---

## 1. `pyproject.toml`

```toml
[project]
name = "siclus-backend"
version = "0.1.0"
description = "Backend Siclus"
readme = "README.md"
authors = [
    { name = "Darma Nugraha", email = "nugrahadarma.ep@gmail.com" }
]
requires-python = ">=3.14"
dependencies = [
    "bcrypt>=5.0.0",
    "email-validator>=2.3.0",
    "fastapi>=0.141.1",
    "openpyxl>=3.1.5",
    "pandas>=3.0.5",
    "passlib>=1.7.4",
    "pydantic>=2.13.4",
    "pyjwt>=2.13.0",
    "python-dotenv>=1.2.3",
    "python-multipart>=0.0.32",
    "supabase>=2.31.0",
    "uvicorn>=0.52.4",
]

[tool.uv]
package = false
```

[Kembali ke Daftar Isi](#-daftar-isi)

---

## 2. `.env.example`

```env
# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-supabase-anon-or-service-key

# JWT Security Configuration
SECRET_KEY=your-jwt-secret-key-here
```

[Kembali ke Daftar Isi](#-daftar-isi)

---

## 3. `.gitignore`

```gitignore
# ==========================================
# 1. Environment Variables & Secrets (SANGAT KRUSIAL)
# ==========================================
# Jangan pernah upload kredensial / API key / database key ke GitHub!
.env
.env.*
!.env.example
*.pem
*.key
*.cert

# ==========================================
# 2. Virtual Environments
# ==========================================
# Folder dependensi lokal yang diinstall
.venv/
venv/
ENV/
env/
env.bak/
venv.bak/
.python-version-backup

# ==========================================
# 3. Python Bytecode & Cache
# ==========================================
__pycache__/
*.py[cod]
*$py.class
*.so
.Python

# ==========================================
# 4. Testing, Linting & Coverage
# ==========================================
.pytest_cache/
.coverage
.coverage.*
htmlcov/
.mypy_cache/
.ruff_cache/

# ==========================================
# 5. Build, Distribution & Packaging
# ==========================================
build/
dist/
*.egg-info/
*.egg
.eggs/

# ==========================================
# 6. IDE, Code Editor & Tools
# ==========================================
.vscode/
.idea/
*.swp
*.swo
*~

# ==========================================
# 7. OS Generated & Temporary Files
# ==========================================
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db
desktop.ini
*.log
logs/
*.tmp
*.bak
```

[Kembali ke Daftar Isi](#-daftar-isi)

---

## 4. `.python-version`

```text
3.14
```

[Kembali ke Daftar Isi](#-daftar-isi)

---

## 5. `app/__init__.py`

```python

```

[Kembali ke Daftar Isi](#-daftar-isi)

---

## 6. `app/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.auth import router as auth_router
from app.api.routes.laporan import router as laporan_router
from app.api.routes.admin import router as admin_router
from app.api.routes.driver import router as driver_router

# Inisialisasi Mesin Utama
app = FastAPI(
    title="SICLUS API",
    description="API Endpoint untuk Sistem Inspeksi & Catatan Laporan Sopir",
    version="1.0.0",
)
# konfigur cors fe
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mendaftarkan semua colokan API yang sudah dibuat
app.include_router(auth_router, prefix="/api/auth", tags=["Autentikasi"])
app.include_router(laporan_router, prefix="/api/laporan", tags=["Laporan Harian"])
app.include_router(admin_router, prefix="/api/admin", tags=["Dashboard Admin"])
app.include_router(driver_router, prefix="/api/driver", tags=["Zona Pengemudi"])


# test
@app.get("/")
def root():
    return {"status": "mesin siclus berjalan!"}
```

[Kembali ke Daftar Isi](#-daftar-isi)

---

## 7. `app/core/__init__.py`

```python

```

[Kembali ke Daftar Isi](#-daftar-isi)

---

## 8. `app/core/config.py`

```python
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

    SECRET_KEY: str = os.getenv(
        "SECRET_KEY", "kunci-rahasia-siclus-dishub-mojokerto-2026"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24


settings = Settings()
```

[Kembali ke Daftar Isi](#-daftar-isi)

---

## 9. `app/core/security.py`

```python
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
import bcrypt  # <-- Kita langsung pake bcrypt ori, buang passlib!
from app.core.config import settings


# ─── FUNGSI KEAMANAN: VERIFIKASI PASSWORD LOGIN ───────────────────────
def verify_password(plain_password: str, hashed_password: str) -> bool:
    # bcrypt butuh format bytes, jadi string-nya harus di-encode ke utf-8 dulu
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


# ─── FUNGSI KEAMANAN: ENKRIPSI PASSWORD (REGISTER) ────────────────────
def get_password_hash(password: str) -> str:
    # Bikin garam (salt) acak, lalu hash password-nya
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)

    # Balikin jadi string biasa biar aman disimpen ke Supabase
    return hashed.decode("utf-8")


# ─── FUNGSI KEAMANAN: PEMBUATAN TOKEN JWT ─────────────────────────────
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()

    # Menentukan waktu kedaluwarsa tiket
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})

    # Membuat token dengan kunci rahasia
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )

    return encoded_jwt
```

[Kembali ke Daftar Isi](#-daftar-isi)

---

## 10. `app/db/__init__.py`

```python

```

[Kembali ke Daftar Isi](#-daftar-isi)

---

## 11. `app/db/database.py`

```python
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# 2. Ambil alamat dan kunci rahasia dari dalem brankas
API_URL = os.getenv("SUPABASE_URL")
API_KEY = os.getenv("SUPABASE_KEY")

# 3. Validasi biar laptop lu ngasih tau kalo kuncinya lupa ditaruh
if not API_URL or not API_KEY:
    raise Exception("WEY KUNCINYA BELOM DIMASUKIN KE .ENV TUH!")

# 4. Bikin jembatan koneksinya!
supabase: Client = create_client(API_URL, API_KEY)
```

[Kembali ke Daftar Isi](#-daftar-isi)

---

## 12. `app/schemas/__init__.py`

```python

```

[Kembali ke Daftar Isi](#-daftar-isi)

---

## 13. `app/schemas/user.py`

```python
from typing import Optional
from pydantic import BaseModel, EmailStr


# ─── SCHEMA: DATA LOGIN PENGGUNA (REQUEST) ────────────────────
# Skema ini memastikan data yang dikirim dari Frontend (Cevin)
# wajib memiliki format email yang valid dan password.
class UserLogin(BaseModel):
    email: EmailStr
    password: str


# ─── SCHEMA: PROFIL PENGGUNA (RESPONSE) ───────────────────────
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


# ─── SCHEMA: REGISTRASI SUPIR BARU (REGISTER) ─────────────────
# Skema ini bakal dipake sama Admin buat masukin data supir baru ke sistem
class UserRegister(BaseModel):
    id: str
    nama_lengkap: str
    email: EmailStr
    password: str
    role: str = "pengemudi"
    trayek: Optional[str] = None
    bus: Optional[str] = None

# ─── SCHEMA: EDIT DATA SUPIR (UPDATE) ─────────────────────────
# Semua field bersifat opsional (Optional) karena Admin mungkin
# hanya ingin mengubah satu data saja (misal: ganti rute trayek).
class UserUpdate(BaseModel):
    nama_lengkap: Optional[str] = None
    email: Optional[EmailStr] = None
    trayek: Optional[str] = None
    bus: Optional[str] = None
```

[Kembali ke Daftar Isi](#-daftar-isi)

---

## 14. `app/schemas/inspeksi.py`

```python
from typing import Optional
from pydantic import BaseModel


# inspeksi setiap parts kendaraan
class InspeksiCreate(BaseModel):
    rem: str
    ac: str
    lampu: str
    klakson: str
    wiper: str
    lampu_rem: str
    bell: str
    pintu: str
    kebersihan: str

    # opsional catatan kerusakan
    catatan: Optional[str] = None
```

[Kembali ke Daftar Isi](#-daftar-isi)

---

## 15. `app/schemas/jadwal.py`

```python
from typing import Optional
from pydantic import BaseModel


# ─── SCHEMA: PEMBUATAN JADWAL BARU (CREATE) ───────────────────
class JadwalCreate(BaseModel):
    trayek: str
    tipe_sesi: str
    batas_keluar_dishub: str
    batas_tiba_start: str


# ─── SCHEMA: PEMBARUAN JADWAL (UPDATE) ────────────────────────
class JadwalUpdate(BaseModel):
    batas_keluar_dishub: Optional[str] = None
    batas_tiba_start: Optional[str] = None
```

[Kembali ke Daftar Isi](#-daftar-isi)

---

## 16. `app/schemas/perjalanan.py`

```python
from pydantic import BaseModel


# cp 1
class SesiCP1Create(BaseModel):
    tipe_sesi: str
    nopol_kendaraan: str
    km_berangkat_kantor: int
    foto_awal: str


# cp 2
class SesiCP2Update(BaseModel):
    km_berangkat_start: int


# cp 3
class SesiCP3Update(BaseModel):
    km_tiba_finish: int
    jumlah_penumpang: int


# cp 4
class SesiCP4Update(BaseModel):
    km_tiba_kantor: int
    foto_akhir: str
```

[Kembali ke Daftar Isi](#-daftar-isi)

---

## 17. `app/schemas/laporan.py`

```python
from datetime import date
from pydantic import BaseModel


# ─── SCHEMA: INISIALISASI LAPORAN HARIAN (CREATE) ─────────────
# Skema ini adalah cangkang utama untuk hari tersebut.
# ID Supir tidak perlu dikirim dari Frontend karena akan diambil otomatis
# dari tiket JWT (Token) demi keamanan.
class LaporanHarianCreate(BaseModel):
    tanggal: date
    trayek: str
    bus: str
```

[Kembali ke Daftar Isi](#-daftar-isi)

---

## 18. `app/services/__init__.py`

```python

```

[Kembali ke Daftar Isi](#-daftar-isi)

---

## 19. `app/services/auth_service.py`

```python
from fastapi import HTTPException, status
from app.schemas.user import UserLogin
from app.core.security import create_access_token, verify_password
from app.db.database import supabase


def proses_login_supir(data_login: UserLogin):
    # 1. Mencari data pengguna di database berdasarkan email
    try:
        response = (
            supabase.table("users").select("*").eq("email", data_login.email).execute()
        )
        db_user_list = response.data
    except Exception as e:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan pada koneksi database: {str(e)}",
        )

    # 2. Validasi ketersediaan email
    if not db_user_list:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kredensial tidak valid. Email tidak ditemukan.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    db_user = db_user_list[0]

    # 3. Validasi Kata Sandi
    if not verify_password(data_login.password, db_user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kredensial tidak valid. Kata sandi salah.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 4. Token Akses (JWT)
    isi_tiket = {"sub": db_user["email"], "role": db_user["role"]}
    token_jwt = create_access_token(data=isi_tiket)

    # 5. Pengembalian Data Respons
    return {
        "access_token": token_jwt,
        "token_type": "bearer",
        "user": {
            "id": db_user["id"],
            "nama_lengkap": db_user["nama"],
            "email": db_user["email"],
            "role": db_user["role"],
            "trayek": db_user["trayek"],
            "bus": db_user["bus"],
        },
    }
```

[Kembali ke Daftar Isi](#-daftar-isi)

---

## 20. `app/services/laporan_service.py`

```python
from fastapi import HTTPException, status
from datetime import datetime, timezone, timedelta
from app.db.database import supabase
from app.schemas.laporan import LaporanHarianCreate
from app.schemas.inspeksi import InspeksiCreate
from app.schemas.perjalanan import (
    SesiCP1Create,
    SesiCP2Update,
    SesiCP3Update,
    SesiCP4Update,
)

# Waktu WIB (UTC+7) untuk acuan backend
WIB = timezone(timedelta(hours=7))


# inislaporan
def create_laporan_harian(data: LaporanHarianCreate, id_supir: str):
    try:
        response = (
            supabase.table("daily_reports")
            .insert(
                {
                    "tanggal": str(data.tanggal),
                    "id_supir": id_supir,
                    "trayek": data.trayek,
                    "bus": data.bus,
                }
            )
            .execute()
        )
        return response.data[0]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal inisialisasi laporan: {str(e)}",
        )


# inspeksi
def create_inspeksi_kendaraan(laporan_id: str, data: InspeksiCreate):
    cek = supabase.table("daily_reports").select("id").eq("id", laporan_id).execute()
    if not cek.data:
        raise HTTPException(status_code=404, detail="Laporan harian belum dibuat!")

    try:
        response = (
            supabase.table("inspections")
            .insert(
                {
                    "laporan_id": laporan_id,
                    "rem": data.rem,
                    "ac": data.ac,
                    "lampu": data.lampu,
                    "klakson": data.klakson,
                    "wiper": data.wiper,
                    "lampu_rem": data.lampu_rem,
                    "bell": data.bell,
                    "pintu": data.pintu,
                    "kebersihan": data.kebersihan,
                    "catatan": data.catatan,
                }
            )
            .execute()
        )
        return response.data[0]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal simpan inspeksi: {str(e)}",
        )


# sesicp1
def proses_cp1(laporan_id: str, data: SesiCP1Create, email_supir: str):
    cek = supabase.table("daily_reports").select("id").eq("id", laporan_id).execute()
    if not cek.data:
        raise HTTPException(status_code=404, detail="Laporan harian tidak valid.")

    waktu_sekarang = datetime.now(WIB)
    jam_teks = waktu_sekarang.strftime("%H:%M")

    # Radar Cek Keterlambatan Keluar Garasi (CP1)
    status_waktu = "TEPAT WAKTU"
    laporan = (
        supabase.table("daily_reports").select("trayek").eq("id", laporan_id).execute()
    )
    trayek = laporan.data[0]["trayek"]

    jadwal = (
        supabase.table("schedules")
        .select("batas_keluar_dishub")
        .ilike("trayek", trayek)
        .eq("tipe_sesi", data.tipe_sesi.upper())
        .execute()
    )

    if jadwal.data and jadwal.data[0].get("batas_keluar_dishub"):
        batas_maksimal = jadwal.data[0]["batas_keluar_dishub"]
        if jam_teks > batas_maksimal:
            status_waktu = "TERLAMBAT"

    try:
        response = (
            supabase.table("trip_sessions")
            .insert(
                {
                    "laporan_id": laporan_id,
                    "tipe_sesi": data.tipe_sesi.upper(),
                    "nopol_kendaraan": data.nopol_kendaraan,
                    "km_berangkat_kantor": data.km_berangkat_kantor,
                    "foto_awal": data.foto_awal,
                    "jam_berangkat_kantor": waktu_sekarang.isoformat(),
                    "status_waktu": status_waktu,
                }
            )
            .execute()
        )
        return {"pesan": "Check Point 1 Selesai", "data": response.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal CP1: {str(e)}")


# sesicp2
def proses_cp2(sesi_id: str, data: SesiCP2Update, email_supir: str):
    # validasi cp1
    sesi = (
        supabase.table("trip_sessions")
        .select("laporan_id, tipe_sesi, jam_berangkat_kantor, status_waktu")
        .eq("id", sesi_id)
        .execute()
    )

    if not sesi.data or not sesi.data[0].get("jam_berangkat_kantor"):
        raise HTTPException(
            status_code=403, detail="Gagal: Selesaikan Check Point 1 terlebih dahulu!"
        )

    tipe_sesi = sesi.data[0]["tipe_sesi"]
    laporan_id = sesi.data[0]["laporan_id"]
    status_waktu_bawaan = sesi.data[0].get(
        "status_waktu", "TEPAT WAKTU"
    )  # ambil dari cp1

    waktu_sekarang = datetime.now(WIB)
    jam_teks = waktu_sekarang.strftime("%H:%M")

    # otomatisasi cek keterlambatan halte cp2
    laporan = (
        supabase.table("daily_reports").select("trayek").eq("id", laporan_id).execute()
    )
    trayek = laporan.data[0]["trayek"]
    jadwal = (
        supabase.table("schedules")
        .select("batas_tiba_start")
        .ilike("trayek", trayek)
        .eq("tipe_sesi", tipe_sesi)
        .execute()
    )

    if jadwal.data and jadwal.data[0].get("batas_tiba_start"):
        batas_maksimal = jadwal.data[0]["batas_tiba_start"]
        if jam_teks > batas_maksimal:
            status_waktu_bawaan = "TERLAMBAT"

    try:
        response = (
            supabase.table("trip_sessions")
            .update(
                {
                    "km_berangkat_start": data.km_berangkat_start,
                    "jam_berangkat_start": waktu_sekarang.isoformat(),
                    "status_waktu": status_waktu_bawaan,
                }
            )
            .eq("id", sesi_id)
            .execute()
        )
        return {"pesan": "Check Point 2 Selesai", "data": response.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal CP2: {str(e)}")


# sesicp3
def proses_cp3(sesi_id: str, data: SesiCP3Update, email_supir: str):
    # validasi cp2
    sesi = (
        supabase.table("trip_sessions")
        .select("jam_berangkat_start")
        .eq("id", sesi_id)
        .execute()
    )
    if not sesi.data or not sesi.data[0].get("jam_berangkat_start"):
        raise HTTPException(
            status_code=403,
            detail="Gagal: Selesaikan Check Point 2 (Tiba di Halte) terlebih dahulu!",
        )

    waktu_sekarang = datetime.now(WIB).isoformat()
    try:
        response = (
            supabase.table("trip_sessions")
            .update(
                {
                    "km_tiba_finish": data.km_tiba_finish,
                    "jumlah_penumpang": data.jumlah_penumpang,
                    "jam_tiba_finish": waktu_sekarang,
                }
            )
            .eq("id", sesi_id)
            .execute()
        )
        return {"pesan": "Check Point 3 Selesai", "data": response.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal CP3: {str(e)}")


# sesicp4
def proses_cp4(sesi_id: str, data: SesiCP4Update, email_supir: str):
    # Validasi CP3
    sesi = (
        supabase.table("trip_sessions")
        .select("jam_tiba_finish")
        .eq("id", sesi_id)
        .execute()
    )
    if not sesi.data or not sesi.data[0].get("jam_tiba_finish"):
        raise HTTPException(
            status_code=403,
            detail="Gagal: Selesaikan Check Point 3 (Selesai Rute) terlebih dahulu!",
        )

    waktu_sekarang = datetime.now(WIB).isoformat()
    try:
        response = (
            supabase.table("trip_sessions")
            .update(
                {
                    "km_tiba_kantor": data.km_tiba_kantor,
                    "foto_akhir": data.foto_akhir,
                    "jam_tiba_kantor": waktu_sekarang,
                }
            )
            .eq("id", sesi_id)
            .execute()
        )
        return {"pesan": "Shift Laporan Selesai & Ditutup!", "data": response.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal CP4: {str(e)}")
```

[Kembali ke Daftar Isi](#-daftar-isi)

---

## 21. `app/api/__init__.py`

```python

```

[Kembali ke Daftar Isi](#-daftar-isi)

---

## 22. `app/api/routes/__init__.py`

```python

```

[Kembali ke Daftar Isi](#-daftar-isi)

---

## 23. `app/api/routes/auth.py`

```python
from fastapi import APIRouter
from app.schemas.user import UserLogin
from app.services.auth_service import proses_login_supir

router = APIRouter()

@router.post("/login")
def login(data: UserLogin):
    hasil_login = proses_login_supir(data)
    return hasil_login
```

[Kembali ke Daftar Isi](#-daftar-isi)

---

## 24. `app/api/routes/admin.py`

```python
from io import BytesIO
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import pandas as pd
from app.core.config import settings
from app.db.database import supabase
from datetime import date
from app.schemas.user import UserRegister, UserUpdate
from app.schemas.jadwal import JadwalCreate, JadwalUpdate
from app.core.security import get_password_hash

router = APIRouter()
security = HTTPBearer()


# verifikasiadmin
def verifikasi_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
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
                detail="Akses ditolak. Eksklusif untuk Administrator.",
            )
        return email_user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Sesi kedaluwarsa.")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token tidak valid.")


# dashboard
@router.get("/dashboard")
def dashboard_admin(email_admin: str = Depends(verifikasi_admin)):
    try:
        tanggal_hari_ini = str(date.today())

        users_res = (
            supabase.table("users").select("id").eq("role", "pengemudi").execute()
        )
        total_supir = len(users_res.data)

        reports_res = (
            supabase.table("daily_reports")
            .select("id, id_supir, trip_sessions(status_waktu)")
            .eq("tanggal", tanggal_hari_ini)
            .execute()
        )
        data_laporan_hari_ini = reports_res.data

        total_jalan = len(data_laporan_hari_ini)
        total_absen = max(0, total_supir - total_jalan)

        total_telat = 0
        for laporan in data_laporan_hari_ini:
            sesi_list = laporan.get("trip_sessions", [])
            for sesi in sesi_list:
                if sesi.get("status_waktu") == "TERLAMBAT":
                    total_telat += 1
                    break

        return {
            "pesan": "Metrik dashboard ditarik.",
            "data": {
                "tanggal": tanggal_hari_ini,
                "total_supir_terdaftar": total_supir,
                "total_supir_jalan": total_jalan,
                "total_supir_absen": total_absen,
                "total_supir_telat": total_telat,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal hitung metrik: {str(e)}")


# rekap
@router.get("/rekap")
def get_rekap_laporan(email_admin: str = Depends(verifikasi_admin)):
    try:
        response = (
            supabase.table("daily_reports")
            .select("*, inspections(*), trip_sessions(*)")
            .execute()
        )
        return {
            "pesan": "Rekapitulasi ditarik.",
            "total_data": len(response.data),
            "data": response.data,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# riwayatharian
@router.get("/riwayat-harian")
def get_riwayat_harian(email_admin: str = Depends(verifikasi_admin)):
    try:
        # Ambil laporan + nama supir + status waktu, urutkan dari terbaru
        response = (
            supabase.table("daily_reports")
            .select("*, users(nama), trip_sessions(status_waktu, tipe_sesi)")
            .order("tanggal", desc=True)
            .execute()
        )

        # Algoritma grouping per tanggal buat frontend
        grup_tanggal = {}
        for laporan in response.data:
            tgl = laporan.get("tanggal")
            if tgl not in grup_tanggal:
                grup_tanggal[tgl] = []
            grup_tanggal[tgl].append(laporan)

        hasil_format = [
            {"tanggal": tgl, "laporan": isi} for tgl, isi in grup_tanggal.items()
        ]

        return {"pesan": "Riwayat harian ditarik.", "data": hasil_format}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# exportexcel
@router.get("/export-excel")
def export_rekap_excel(
    id_supir: Optional[str] = None, email_admin: str = Depends(verifikasi_admin)
):
    try:
        query = supabase.table("daily_reports").select(
            "*, inspections(*), trip_sessions(*)"
        )

        # Filter jika mau export personal
        if id_supir:
            query = query.eq("id_supir", id_supir)

        response = query.execute()
        data_laporan = response.data

        if not data_laporan:
            raise HTTPException(status_code=404, detail="Data laporan kosong.")

        tabel_excel = []
        for baris in data_laporan:
            sesi_list = baris.get("trip_sessions", [])
            sesi = sesi_list[0] if sesi_list else {}

            tabel_excel.append(
                {
                    "Tanggal Operasional": baris.get("tanggal"),
                    "ID Pengemudi": baris.get("id_supir"),
                    "Trayek": baris.get("trayek"),
                    "Armada Bus": baris.get("bus"),
                    "Tipe Sesi": sesi.get("tipe_sesi", "-"),
                    "Jam Keluar Dishub": sesi.get("jam_berangkat_kantor", "-"),
                    "Jam Tiba di Sekolah": sesi.get("jam_berangkat_start", "-"),
                    "Status Kedisiplinan": sesi.get("status_waktu", "-"),
                }
            )

        df = pd.DataFrame(tabel_excel)
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Rekap_Siclus")

        buffer.seek(0)
        nama_file = f"Rekap_{id_supir}.xlsx" if id_supir else "Rekap_Semua_Supir.xlsx"

        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={nama_file}"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal export: {str(e)}")


# getusers
@router.get("/users")
def get_semua_supir(email_admin: str = Depends(verifikasi_admin)):
    try:
        response = (
            supabase.table("users")
            .select("id, nama, email, trayek, bus, foto_profil")
            .eq("role", "pengemudi")
            .execute()
        )
        return {
            "pesan": "Daftar pengemudi ditarik.",
            "total": len(response.data),
            "data": response.data,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# postusers
@router.post("/users")
def tambah_supir_baru(data: UserRegister, email_admin: str = Depends(verifikasi_admin)):
    if not data.id.strip() or not data.email.strip() or not data.password.strip():
        raise HTTPException(status_code=400, detail="Data tidak boleh kosong.")

    if supabase.table("users").select("id").eq("id", data.id).execute().data:
        raise HTTPException(status_code=400, detail="ID sudah terdaftar.")
    if supabase.table("users").select("id").eq("email", data.email).execute().data:
        raise HTTPException(status_code=400, detail="Email sudah dipakai.")

    try:
        response = (
            supabase.table("users")
            .insert(
                {
                    "id": data.id,
                    "nama": data.nama_lengkap,
                    "email": data.email,
                    "password": get_password_hash(data.password),
                    "role": data.role,
                    "trayek": data.trayek,
                    "bus": data.bus,
                }
            )
            .execute()
        )
        user_terdaftar = response.data[0]
        user_terdaftar.pop("password", None)
        return {"pesan": "Akun dibuat.", "data": user_terdaftar}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# putusers
@router.put("/users/{user_id}")
def edit_data_supir(
    user_id: str, data: UserUpdate, email_admin: str = Depends(verifikasi_admin)
):
    try:
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=400, detail="Tidak ada data diubah.")

        if "nama_lengkap" in update_data:
            update_data["nama"] = update_data.pop("nama_lengkap")

        response = (
            supabase.table("users").update(update_data).eq("id", user_id).execute()
        )
        if not response.data:
            raise HTTPException(status_code=404, detail="Supir tidak ditemukan.")
        return {"pesan": "Data diperbarui.", "data": response.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# deleteusers
@router.delete("/users/{user_id}")
def hapus_supir(user_id: str, email_admin: str = Depends(verifikasi_admin)):
    try:
        response = supabase.table("users").delete().eq("id", user_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Supir tidak ditemukan.")
        return {"pesan": f"Akun {user_id} dihapus."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# getjadwal
@router.get("/jadwal")
def get_semua_jadwal(email_admin: str = Depends(verifikasi_admin)):
    try:
        response = supabase.table("schedules").select("*").order("trayek").execute()
        return {
            "pesan": "Jadwal ditarik.",
            "total": len(response.data),
            "data": response.data,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# postjadwal
@router.post("/jadwal")
def tambah_jadwal_baru(
    data: JadwalCreate, email_admin: str = Depends(verifikasi_admin)
):
    try:
        response = (
            supabase.table("schedules")
            .insert(
                {
                    "trayek": data.trayek,
                    "tipe_sesi": data.tipe_sesi.upper(),
                    "batas_keluar_dishub": data.batas_keluar_dishub,
                    "batas_tiba_start": data.batas_tiba_start,
                }
            )
            .execute()
        )
        return {"pesan": "Jadwal ditambahkan.", "data": response.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# putjadwal
@router.put("/jadwal/{jadwal_id}")
def edit_jadwal(
    jadwal_id: int, data: JadwalUpdate, email_admin: str = Depends(verifikasi_admin)
):
    try:
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=400, detail="Tidak ada data diubah.")

        response = (
            supabase.table("schedules")
            .update(update_data)
            .eq("id", jadwal_id)
            .execute()
        )
        if not response.data:
            raise HTTPException(status_code=404, detail="Jadwal tidak ditemukan.")
        return {"pesan": "Jadwal diperbarui.", "data": response.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

[Kembali ke Daftar Isi](#-daftar-isi)

---

## 25. `app/api/routes/driver.py`

```python
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from app.core.config import settings
from app.db.database import supabase
from fastapi import UploadFile, File
import time

router = APIRouter()
security = HTTPBearer()


# ─── FUNGSI KEAMANAN: VERIFIKASI TOKEN PENGEMUDI ──────────────────────
def verifikasi_pengemudi(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """
    Fungsi otorisasi untuk memvalidasi token JWT pada Zona Pengemudi.
    Mengekstrak email pengguna dari payload token.
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        email_user = payload.get("sub")

        if not email_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Kredensial tidak valid. Payload token kosong.",
            )

        return email_user

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesi telah kedaluwarsa. Silakan login kembali.",
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token autentikasi tidak valid atau telah dimanipulasi.",
        )


# ─── ENDPOINT: DATA PROFIL PENGEMUDI ──────────────────────────────────
@router.get("/profil")
def get_profil_pengemudi(email_supir: str = Depends(verifikasi_pengemudi)):
    """
    Menarik data identitas dan penugasan pengemudi (Nama, Trayek, Armada)
    dari database berdasarkan email yang terekstrak dari Token JWT aktif.
    """
    try:
        # Menarik data spesifik dari tabel users berdasarkan email
        response = (
            supabase.table("users")
            .select("id, nama, email, role, trayek, bus, foto_profil")
            .eq("email", email_supir)
            .execute()
        )

        data_user = response.data

        if not data_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Data profil pengemudi tidak ditemukan di dalam sistem.",
            )

        return {"pesan": "Data profil berhasil ditarik.", "data": data_user[0]}

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan teknis saat menarik data profil: {str(e)}",
        )


# ─── ENDPOINT: UBAH FOTO PROFIL PENGEMUDI ─────────────────────────────
@router.put("/profil/foto")
async def update_foto_profil(
    foto: UploadFile = File(...), email_supir: str = Depends(verifikasi_pengemudi)
):
    """
    Mengunggah foto profil baru ke penyimpanan awan dan memperbarui
    tautan (URL) foto tersebut di tabel profil pengguna.
    """
    try:
        # 1. Validasi keamanan ekstensi file
        ekstensi = foto.filename.split(".")[-1].lower()
        if ekstensi not in ["jpg", "jpeg", "png"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Format tidak didukung. Gunakan JPG, JPEG, atau PNG.",
            )

        # 2. Bikin nama file unik biar kaga ketumpuk
        nama_prefix = email_supir.split("@")[0]
        nama_file_baru = f"avatar_{nama_prefix}_{int(time.time())}.{ekstensi}"

        # 3. Baca dan lempar gambar ke bucket 'foto_profil'
        isi_gambar = await foto.read()
        response_storage = supabase.storage.from_("foto_profil").upload(
            file=isi_gambar,
            path=nama_file_baru,
            file_options={"content-type": foto.content_type},
        )

        # 4. Ambil URL publiknya
        url_publik = supabase.storage.from_("foto_profil").get_public_url(
            nama_file_baru
        )

        # 5. SIMPAN URL TERSEBUT KE TABEL USERS (Ini yang bedain sama selfie biasa!)
        supabase.table("users").update({"foto_profil": url_publik}).eq(
            "email", email_supir
        ).execute()

        return {"pesan": "Foto profil berhasil diperbarui!", "foto_profil": url_publik}

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan teknis saat memperbarui foto: {str(e)}",
        )


# ─── ENDPOINT: RIWAYAT PERJALANAN PENGEMUDI ───────────────────────────
@router.get("/riwayat")
def get_riwayat_pengemudi(email_supir: str = Depends(verifikasi_pengemudi)):
    """
    Menarik histori laporan operasional khusus untuk pengemudi yang sedang aktif.
    Dilengkapi sistem filter ketat untuk mencegah kebocoran data antar pengemudi.
    """
    try:
        # Menarik data laporan utama beserta detail sesinya (Pagi/Siang).
        # WAJIB pake .eq() buat nge-filter milik supir ini aja!
        # Pake .order() biar laporan paling baru muncul di paling atas list FE.
        response = (
            supabase.table("daily_reports")
            .select("*, trip_sessions(*)")
            .eq("id_supir", email_supir)
            .order("tanggal", desc=True)
            .execute()
        )

        data_riwayat = response.data

        return {
            "pesan": "Riwayat perjalanan berhasil ditarik.",
            "total_riwayat": len(data_riwayat),
            "data": data_riwayat,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan teknis saat menarik riwayat: {str(e)}",
        )


# ─── ENDPOINT: JADWAL OPERASIONAL PENGEMUDI ───────────────────────────
@router.get("/jadwal")
def get_jadwal_hari_ini(email_supir: str = Depends(verifikasi_pengemudi)):
    """
    Menarik jadwal operasional dan batas waktu toleransi (cut-off time)
    berdasarkan rute/trayek yang ditugaskan kepada pengemudi saat ini.
    """
    try:
        # 1. Cari tau dulu pengemudi ini ditugaskan di Trayek apa
        user_response = (
            supabase.table("users").select("trayek").eq("email", email_supir).execute()
        )

        if not user_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Data akun pengemudi tidak ditemukan.",
            )

        trayek_supir = user_response.data[0].get("trayek")

        # Jika admin belum ngasih trayek ke supir ini
        if not trayek_supir:
            return {
                "pesan": "Anda belum ditugaskan ke rute/trayek mana pun hari ini.",
                "data": [],
            }

        # 2. Tarik jadwal dari tabel schedules berdasarkan trayek supir
        # Pake 'ilike' biar pencariannya kebal huruf besar/kecil (Trayek A = trayek a)
        jadwal_response = (
            supabase.table("schedules")
            .select("*")
            .ilike("trayek", trayek_supir)
            .execute()
        )

        return {
            "pesan": f"Jadwal operasional untuk rute {trayek_supir} berhasil ditarik.",
            "data": jadwal_response.data,
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan teknis saat menarik jadwal operasional: {str(e)}",
        )
```

[Kembali ke Daftar Isi](#-daftar-isi)

---

## 26. `app/api/routes/laporan.py`

```python
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import time

from app.schemas.laporan import LaporanHarianCreate
from app.schemas.inspeksi import InspeksiCreate
from app.schemas.perjalanan import (
    SesiCP1Create,
    SesiCP2Update,
    SesiCP3Update,
    SesiCP4Update,
)
from app.services.laporan_service import (
    create_laporan_harian,
    create_inspeksi_kendaraan,
    proses_cp1,
    proses_cp2,
    proses_cp3,
    proses_cp4,
)
from app.core.config import settings
from app.db.database import supabase

router = APIRouter()
security = HTTPBearer()


# verifikasitoken
def verifikasi_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        email_supir = payload.get("sub")

        if email_supir is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Kredensial tidak valid. Payload token kosong.",
            )
        return email_supir

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesi telah kedaluwarsa. Silakan login kembali.",
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token autentikasi tidak valid atau telah dimanipulasi.",
        )


# inislaporan
@router.post("/mulai")
def mulai_laporan(
    data: LaporanHarianCreate, email_supir: str = Depends(verifikasi_token)
):
    return create_laporan_harian(data, email_supir)


# inspeksi
@router.post("/inspeksi")
def inspeksi_kendaraan(
    laporan_id: str, data: InspeksiCreate, email_supir: str = Depends(verifikasi_token)
):
    return create_inspeksi_kendaraan(laporan_id, data)


# sesicp1
@router.post("/sesi/cp1")
def sesi_checkpoint_1(
    laporan_id: str, data: SesiCP1Create, email_supir: str = Depends(verifikasi_token)
):
    return proses_cp1(laporan_id, data, email_supir)


# sesicp2
@router.put("/sesi/cp2/{sesi_id}")
def sesi_checkpoint_2(
    sesi_id: str, data: SesiCP2Update, email_supir: str = Depends(verifikasi_token)
):
    return proses_cp2(sesi_id, data, email_supir)


# sesicp3
@router.put("/sesi/cp3/{sesi_id}")
def sesi_checkpoint_3(
    sesi_id: str, data: SesiCP3Update, email_supir: str = Depends(verifikasi_token)
):
    return proses_cp3(sesi_id, data, email_supir)


# sesicp4
@router.put("/sesi/cp4/{sesi_id}")
def sesi_checkpoint_4(
    sesi_id: str, data: SesiCP4Update, email_supir: str = Depends(verifikasi_token)
):
    return proses_cp4(sesi_id, data, email_supir)


# uploadselfie
@router.post("/upload-selfie")
async def upload_selfie(
    foto: UploadFile = File(...), email_supir: str = Depends(verifikasi_token)
):
    try:
        ekstensi = foto.filename.split(".")[-1].lower()
        if ekstensi not in ["jpg", "jpeg", "png"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Format file tidak didukung. Harap gunakan JPG, JPEG, atau PNG.",
            )

        nama_prefix = email_supir.split("@")[0]
        nama_file_baru = f"{nama_prefix}_{int(time.time())}.{ekstensi}"

        isi_gambar = await foto.read()

        supabase.storage.from_("selfie_driver").upload(
            file=isi_gambar,
            path=nama_file_baru,
            file_options={"content-type": foto.content_type},
        )

        url_publik = supabase.storage.from_("selfie_driver").get_public_url(
            nama_file_baru
        )

        return {
            "pesan": "Foto validasi kehadiran berhasil diunggah.",
            "url_foto": url_publik,
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan teknis saat mengunggah foto: {str(e)}",
        )
```

[Kembali ke Daftar Isi](#-daftar-isi)
