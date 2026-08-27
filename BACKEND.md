# SICLUS Backend - Source Code Documentation

Dokumentasi lengkap seluruh file source code proyek **SICLUS Backend** tanpa modifikasi.

---

## 📁 Struktur Direktori Proyek

```text
siclus-backend/
├── .env.example
├── .gitignore
├── .python-version
├── pyproject.toml
├── README.md
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
- [`pyproject.toml`](#pyprojecttoml)
- [`.env.example`](#envexample)
- [`.gitignore`](#gitignore)
- [`.python-version`](#python-version)

### 🚀 Entry Point Aplikasi
- [`app/__init__.py`](#app__init__py)
- [`app/main.py`](#appmainpy)

### 🛡️ Core & Keamanan
- [`app/core/__init__.py`](#appcore__init__py)
- [`app/core/config.py`](#appcoreconfigpy)
- [`app/core/security.py`](#appcoresecuritypy)

### 🗄️ Database
- [`app/db/__init__.py`](#appdb__init__py)
- [`app/db/database.py`](#appdbdatabasepy)

### 📋 Schemas (Pydantic)
- [`app/schemas/__init__.py`](#appschemas__init__py)
- [`app/schemas/user.py`](#appschemasuserpy)
- [`app/schemas/inspeksi.py`](#appschemasinspeksipy)
- [`app/schemas/jadwal.py`](#appschemasjadwalpy)
- [`app/schemas/perjalanan.py`](#appschemasperjalananpy)
- [`app/schemas/laporan.py`](#appschemaslaporanpy)

### ⚙️ Services (Business Logic)
- [`app/services/__init__.py`](#appservices__init__py)
- [`app/services/auth_service.py`](#appservicesauth_servicepy)
- [`app/services/laporan_service.py`](#appserviceslaporan_servicepy)

### 🌐 API Routes (Endpoints)
- [`app/api/__init__.py`](#appapi__init__py)
- [`app/api/routes/__init__.py`](#appapiroutes__init__py)
- [`app/api/routes/auth.py`](#appapiroutesauthpy)
- [`app/api/routes/admin.py`](#appapiroutesadminpy)
- [`app/api/routes/driver.py`](#appapiroutesdriverpy)
- [`app/api/routes/laporan.py`](#appapirouteslaporanpy)

---

## `pyproject.toml`

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

## `.env.example`

```env
# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-supabase-anon-or-service-key

# JWT Security Configuration
SECRET_KEY=your-jwt-secret-key-here

```

[Kembali ke Daftar Isi](#-daftar-isi)

---

## `.gitignore`

```gitignore
# ==========================================
# 1. Environment Variables & Secrets
# ==========================================
.env
.env.*
!.env.example
*.pem
*.key
*.cert

# ==========================================
# 2. Virtual Environments
# ==========================================
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

## `.python-version`

```
3.14

```

[Kembali ke Daftar Isi](#-daftar-isi)

---

## `app/__init__.py`

```python

```

[Kembali ke Daftar Isi](#-daftar-isi)

---

## `app/main.py`

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

# note konfigur fe
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Mengizinkan semua domain (port 5173 dll) untuk fe
    allow_credentials=True,
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

## `app/core/__init__.py`

```python

```

[Kembali ke Daftar Isi](#-daftar-isi)

---

## `app/core/config.py`

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

## `app/core/security.py`

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

## `app/db/__init__.py`

```python

```

[Kembali ke Daftar Isi](#-daftar-isi)

---

## `app/db/database.py`

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

## `app/schemas/__init__.py`

```python

```

[Kembali ke Daftar Isi](#-daftar-isi)

---

## `app/schemas/user.py`

```python
from typing import Optional
from pydantic import BaseModel, EmailStr


# ─── SCHEMA: DATA LOGIN PENGGUNA (REQUEST) ────────────────────────────
# Skema ini memastikan data yang dikirim dari Frontend (Cevin)
# wajib memiliki format email yang valid dan password.
class UserLogin(BaseModel):
    email: EmailStr
    password: str


# ─── SCHEMA: PROFIL PENGGUNA (RESPONSE) ───────────────────────────────
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


# ─── SCHEMA: REGISTRASI SUPIR BARU (REGISTER) ─────────────────────────
# Skema ini bakal dipake sama Admin buat masukin data supir baru ke sistem
class UserRegister(BaseModel):
    id: str
    nama_lengkap: str
    email: EmailStr
    password: str
    role: str = "pengemudi"
    trayek: Optional[str] = None
    bus: Optional[str] = None

# ─── SCHEMA: EDIT DATA SUPIR (UPDATE) ─────────────────────────────────
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

## `app/schemas/inspeksi.py`

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

## `app/schemas/jadwal.py`

```python
from typing import Optional
from pydantic import BaseModel


# ─── SCHEMA: PEMBUATAN JADWAL BARU (CREATE) ───────────────────────────
class JadwalCreate(BaseModel):
    trayek: str
    tipe_sesi: str  # Wajib isi 'PAGI' atau 'SIANG'
    batas_keluar_dishub: str  # Format string, contoh: '05:45'
    batas_tiba_start: str  # Format string, contoh: '06:15'


# ─── SCHEMA: PEMBARUAN JADWAL (UPDATE) ────────────────────────────────
# Trayek dan sesi kaga usah diedit, Admin cukup ngedit jamnya aja.
class JadwalUpdate(BaseModel):
    batas_keluar_dishub: Optional[str] = None
    batas_tiba_start: Optional[str] = None

```

[Kembali ke Daftar Isi](#-daftar-isi)

---

## `app/schemas/perjalanan.py`

```python
from typing import Optional
from pydantic import BaseModel

# ─── SCHEMA: DATA SESI PERJALANAN (PAGI / SIANG) ──────────────────────
# Skema ini akan dipakai dua kali sehari (Sesi PAGI dan Sesi SIANG).
# Tipe datanya string untuk jam (contoh: "05:50 WIB") agar sinkron dengan Frontend.
class TripSessionCreate(BaseModel):
    tipe_sesi: str  # Wajib diisi "PAGI" atau "SIANG"
    
    # ─── DATA BERANGKAT DARI DISHUB ───
    jam_berangkat_kantor: Optional[str] = None 
    km_berangkat_kantor: Optional[int] = None
    
    # ─── DATA TIBA DI TITIK START (TERMINAL/SEKOLAH) ───
    jam_berangkat_start: Optional[str] = None
    km_berangkat_start: Optional[int] = None
    
    # ─── DATA TIBA DI TITIK FINISH (SEKOLAH/TERMINAL) ───
    jam_tiba_finish: Optional[str] = None
    km_tiba_finish: Optional[int] = None
    
    # ─── DATA JUMLAH PENUMPANG ───
    jumlah_penumpang: Optional[int] = 0
    
    # ─── DATA KEMBALI KE DISHUB ───
    jam_tiba_kantor: Optional[str] = None
    km_tiba_kantor: Optional[int] = None
```

[Kembali ke Daftar Isi](#-daftar-isi)

---

## `app/schemas/laporan.py`

```python
from datetime import date
from pydantic import BaseModel


# ─── SCHEMA: INISIALISASI LAPORAN HARIAN (CREATE) ─────────────────────
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

## `app/services/__init__.py`

```python

```

[Kembali ke Daftar Isi](#-daftar-isi)

---

## `app/services/auth_service.py`

```python
from fastapi import HTTPException, status
from app.schemas.user import UserLogin
from app.core.security import create_access_token
from app.db.database import supabase


def proses_login_supir(data_login: UserLogin):
    # 1. Mencari data pengguna di database berdasarkan email
    try:
        response = (
            supabase.table("users").select("*").eq("email", data_login.email).execute()
        )
        db_user_list = response.data
    except Exception as e:
        # Mengembalikan pesan error aktual dari server database untuk keperluan debugging
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

    # 3. Validasi Kata Sandi (Tanpa Enkripsi - Mode Pengembangan)
    if data_login.password != db_user["password"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kredensial tidak valid. Kata sandi salah.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 4. Pembuatan Token Akses (JWT)
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

## `app/services/laporan_service.py`

```python
from fastapi import HTTPException, status
from app.db.database import supabase
from app.schemas.laporan import LaporanHarianCreate
from app.schemas.inspeksi import InspeksiCreate
from app.schemas.perjalanan import TripSessionCreate


# Fungsi untuk membuat entri laporan harian baru di database
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
            detail=f"Terjadi kesalahan teknis saat menyimpan inisialisasi laporan harian: {str(e)}",
        )


# Fungsi untuk menyimpan hasil pengecekan fisik kendaraan
def create_inspeksi_kendaraan(laporan_id: str, data: InspeksiCreate):
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
            detail=f"Terjadi kesalahan teknis saat menyimpan data inspeksi kendaraan: {str(e)}",
        )


# fungsi untuk menyimpan sesi perjalanan
def create_sesi_perjalanan(laporan_id: str, data: TripSessionCreate):
    # ─── LOGIKA: EVALUASI KETERLAMBATAN OTOMATIS ──────────────────────
    status_telat = "TEPAT WAKTU"

    if data.jam_berangkat_start:
        jam_bersih = (
            data.jam_berangkat_start.replace(" WIB", "").replace(" wib", "").strip()
        )

        if data.tipe_sesi.upper() == "PAGI":
            if jam_bersih > "06:15":
                status_telat = "TERLAMBAT"

        elif data.tipe_sesi.upper() == "SIANG":
            if jam_bersih > "15:00":
                status_telat = "TERLAMBAT"

    # ─── PROSES: PENYIMPANAN DATA KE DATABASE ─────────────────────────
    try:
        response = (
            supabase.table("trip_sessions")
            .insert(
                {
                    "laporan_id": laporan_id,
                    "tipe_sesi": data.tipe_sesi,
                    "jam_berangkat_kantor": data.jam_berangkat_kantor,
                    "km_berangkat_kantor": data.km_berangkat_kantor,
                    "jam_berangkat_start": data.jam_berangkat_start,
                    "km_berangkat_start": data.km_berangkat_start,
                    "jam_tiba_finish": data.jam_tiba_finish,
                    "km_tiba_finish": data.km_tiba_finish,
                    "jumlah_penumpang": data.jumlah_penumpang,
                    "jam_tiba_kantor": data.jam_tiba_kantor,
                    "km_tiba_kantor": data.km_tiba_kantor,
                    "status_waktu": status_telat,
                }
            )
            .execute()
        )

        return response.data[0]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan teknis saat merekam data sesi perjalanan: {str(e)}",
        )

```

[Kembali ke Daftar Isi](#-daftar-isi)

---

## `app/api/__init__.py`

```python

```

[Kembali ke Daftar Isi](#-daftar-isi)

---

## `app/api/routes/__init__.py`

```python

```

[Kembali ke Daftar Isi](#-daftar-isi)

---

## `app/api/routes/auth.py`

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

## `app/api/routes/admin.py`

```python

from io import BytesIO
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import pandas as pd
from app.core.config import settings
from app.db.database import supabase
from app.schemas.user import UserRegister, UserUpdate
from app.schemas.jadwal import JadwalCreate, JadwalUpdate
from app.core.security import get_password_hash

router = APIRouter()
security = HTTPBearer()


# ─── FUNGSI KEAMANAN: VERIFIKASI HAK AKSES ADMIN ──────────────────────
def verifikasi_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Fungsi otorisasi khusus (Role-Based Access Control) untuk Administrator.
    Memvalidasi keberadaan token sekaligus memastikan 'role' pengguna adalah 'admin'.
    """
    token = credentials.credentials
    try:
        # Dekode token JWT
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )

        email_user = payload.get("sub")
        role_user = payload.get("role")

        # Validasi Role: Jika bukan admin, tolak akses (403 Forbidden)
        if role_user != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Akses ditolak. Endpoint ini secara eksklusif hanya untuk Administrator.",
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


# ─── ENDPOINT: DASHBOARD ADMIN (TESTING) ──────────────────────────────
@router.get("/dashboard")
def dashboard_admin(email_admin: str = Depends(verifikasi_admin)):
    """
    Endpoint uji coba untuk memastikan verifikasi Admin berjalan dengan baik.
    """
    return {"pesan": f"Selamat datang di Dasbor VIP, {email_admin}!"}


# ─── ENDPOINT: REKAPITULASI DATA (HALAMAN ADMIN) ──────────────────────
@router.get("/rekap")
def get_rekap_laporan(email_admin: str = Depends(verifikasi_admin)):
    """
    Menarik seluruh data laporan harian, termasuk detail inspeksi
    dan sesi perjalanan pengemudi. Data ini digunakan untuk
    ditampilkan pada tabel antarmuka dasbor Administrator.
    """
    try:
        # Menarik data laporan utama beserta relasinya (inspeksi dan sesi)
        # Tanda (*) di dalam kurung berarti menarik semua kolom dari tabel terkait
        response = (
            supabase.table("daily_reports")
            .select("*, inspections(*), trip_sessions(*)")
            .execute()
        )

        return {
            "pesan": "Data rekapitulasi berhasil ditarik.",
            "total_data": len(response.data),
            "data": response.data,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan teknis saat menarik data rekapitulasi: {str(e)}",
        )


# ─── ENDPOINT: UNDUH LAPORAN EXCEL (.xlsx) ────────────────────────────
@router.get("/export-excel")
def export_rekap_excel(email_admin: str = Depends(verifikasi_admin)):
    """
    Mengonversi data laporan operasional menjadi format file Excel (.xlsx)
    yang siap diunduh oleh Administrator.
    """
    try:
        # 1. Menarik data laporan utama beserta relasinya
        response = (
            supabase.table("daily_reports")
            .select("*, inspections(*), trip_sessions(*)")
            .execute()
        )

        data_laporan = response.data

        if not data_laporan:
            raise HTTPException(status_code=404, detail="Data laporan masih kosong.")

        # 2. Menyiapkan kerangka data (struktur baris dan kolom) untuk Excel
        tabel_excel = []

        for baris in data_laporan:
            # Mengambil sesi perjalanan pertama untuk simplifikasi laporan
            sesi_list = baris.get("trip_sessions", [])
            sesi = sesi_list[0] if sesi_list else {}

            # Memetakan kolom sesuai kebutuhan instansi
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

        # 3. Mengonversi data kerangka menjadi DataFrame Pandas (Tabel Virtual)
        df = pd.DataFrame(tabel_excel)

        # 4. Membuat file Excel di dalam memori sistem (RAM) tanpa menyimpannya di hard disk
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Rekap_Laporan_Siclus")

        buffer.seek(0)  # Mengembalikan pointer memori ke awal file

        # 5. Mengirimkan file Excel sebagai bentuk unduhan (attachment)
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": "attachment; filename=Rekap_Laporan_Siclus.xlsx"
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan teknis saat membuat dokumen Excel: {str(e)}",
        )


# ─── ENDPOINT: LIHAT SEMUA AKUN SUPIR (READ) ──────────────────────────
@router.get("/users")
def get_semua_supir(email_admin: str = Depends(verifikasi_admin)):
    """
    Menarik seluruh daftar pengguna yang memiliki role sebagai 'pengemudi'.
    """
    try:
        response = (
            supabase.table("users")
            .select("id, nama, email, trayek, bus, foto_profil")
            .eq("role", "pengemudi")
            .execute()
        )

        return {
            "pesan": "Daftar pengemudi berhasil ditarik.",
            "total": len(response.data),
            "data": response.data,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Terjadi kesalahan: {str(e)}")


# ─── ENDPOINT: TAMBAH AKUN SUPIR BARU (CREATE) ────────────────────────
@router.post("/users")
def tambah_supir_baru(data: UserRegister, email_admin: str = Depends(verifikasi_admin)):
    """
    Mendaftarkan akun pengemudi baru. Kata sandi akan dienkripsi (hashing)
    sebelum disimpan ke dalam database.
    """
    try:
        # Enkripsi password sebelum masuk database
        hashed_pw = get_password_hash(data.password)

        response = (
            supabase.table("users")
            .insert(
                {
                    "id": data.id,
                    "nama": data.nama_lengkap,  # Mapping dari schema ke kolom database
                    "email": data.email,
                    "password": hashed_pw,
                    "role": data.role,
                    "trayek": data.trayek,
                    "bus": data.bus,
                }
            )
            .execute()
        )

        # Hapus tampilan password di response demi keamanan
        user_terdaftar = response.data[0]
        user_terdaftar.pop("password", None)

        return {"pesan": "Akun pengemudi berhasil dibuat.", "data": user_terdaftar}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal menambah supir: {str(e)}")


# ─── ENDPOINT: EDIT DATA SUPIR (UPDATE) ───────────────────────────────
@router.put("/users/{user_id}")
def edit_data_supir(
    user_id: str, data: UserUpdate, email_admin: str = Depends(verifikasi_admin)
):
    """
    Memperbarui data penugasan atau profil pengemudi berdasarkan ID.
    """
    try:
        # Hanya ambil data yang diisi oleh Admin (tidak None)
        update_data = {}
        if data.nama_lengkap:
            update_data["nama"] = data.nama_lengkap
        if data.email:
            update_data["email"] = data.email
        if data.trayek:
            update_data["trayek"] = data.trayek
        if data.bus:
            update_data["bus"] = data.bus

        if not update_data:
            raise HTTPException(
                status_code=400, detail="Tidak ada data yang dikirim untuk diubah."
            )

        response = (
            supabase.table("users").update(update_data).eq("id", user_id).execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=404,
                detail=f"Pengemudi dengan ID {user_id} tidak ditemukan.",
            )

        return {
            "pesan": "Data pengemudi berhasil diperbarui.",
            "data": response.data[0],
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal memperbarui data: {str(e)}")


# ─── ENDPOINT: HAPUS AKUN SUPIR (DELETE) ──────────────────────────────
@router.delete("/users/{user_id}")
def hapus_supir(user_id: str, email_admin: str = Depends(verifikasi_admin)):
    """
    Menghapus akun pengemudi dari sistem secara permanen berdasarkan ID.
    """
    try:
        response = supabase.table("users").delete().eq("id", user_id).execute()

        if not response.data:
            raise HTTPException(
                status_code=404,
                detail=f"Pengemudi dengan ID {user_id} tidak ditemukan.",
            )

        return {
            "pesan": f"Akun pengemudi dengan ID {user_id} berhasil dihapus permanen."
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal menghapus supir: {str(e)}")


# ─── ENDPOINT: LIHAT SEMUA JADWAL (READ) ──────────────────────────────
@router.get("/jadwal")
def get_semua_jadwal(email_admin: str = Depends(verifikasi_admin)):
    """
    Menarik semua data batas waktu operasional (cut-off time) dari seluruh trayek.
    """
    try:
        response = supabase.table("schedules").select("*").order("trayek").execute()
        return {
            "pesan": "Daftar jadwal operasional berhasil ditarik.",
            "total": len(response.data),
            "data": response.data,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Terjadi kesalahan: {str(e)}")


# ─── ENDPOINT: BIKIN JADWAL BARU (CREATE) ─────────────────────────────
@router.post("/jadwal")
def tambah_jadwal_baru(
    data: JadwalCreate, email_admin: str = Depends(verifikasi_admin)
):
    """
    Menambahkan aturan batas waktu baru untuk sebuah trayek dan sesi tertentu.
    """
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

        return {
            "pesan": "Jadwal operasional baru berhasil ditambahkan.",
            "data": response.data[0],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal menambah jadwal: {str(e)}")


# ─── ENDPOINT: EDIT JADWAL (UPDATE) ───────────────────────────────────
@router.put("/jadwal/{jadwal_id}")
def edit_jadwal(
    jadwal_id: int, data: JadwalUpdate, email_admin: str = Depends(verifikasi_admin)
):
    """
    Memperbarui batas waktu toleransi pada jadwal yang sudah ada berdasarkan ID.
    """
    try:
        update_data = {}
        if data.batas_keluar_dishub:
            update_data["batas_keluar_dishub"] = data.batas_keluar_dishub
        if data.batas_tiba_start:
            update_data["batas_tiba_start"] = data.batas_tiba_start

        if not update_data:
            raise HTTPException(
                status_code=400,
                detail="Tidak ada data waktu yang dikirim untuk diubah.",
            )

        response = (
            supabase.table("schedules")
            .update(update_data)
            .eq("id", jadwal_id)
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=404, detail=f"Jadwal dengan ID {jadwal_id} tidak ditemukan."
            )

        return {
            "pesan": "Batas waktu jadwal berhasil diperbarui.",
            "data": response.data[0],
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Gagal memperbarui jadwal: {str(e)}"
        )

```

[Kembali ke Daftar Isi](#-daftar-isi)

---

## `app/api/routes/driver.py`

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

## `app/api/routes/laporan.py`

```python
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import time

from app.schemas.laporan import LaporanHarianCreate
from app.schemas.inspeksi import InspeksiCreate
from app.schemas.perjalanan import TripSessionCreate
from app.services.laporan_service import (
    create_laporan_harian,
    create_inspeksi_kendaraan,
    create_sesi_perjalanan,
)
from app.core.config import settings
from app.db.database import supabase

router = APIRouter()
security = HTTPBearer()


# ─── FUNGSI KEAMANAN: VERIFIKASI TOKEN JWT ────────────────────────────
def verifikasi_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Fungsi otorisasi yang dieksekusi sebelum endpoint utama diproses.
    Bertugas melakukan dekode JWT dan memvalidasi kredensial pengguna.
    """
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

        # Mengembalikan email pengemudi jika autentikasi berhasil
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


# ─── ENDPOINT: INISIALISASI LAPORAN HARIAN ────────────────────────────
@router.post("/mulai")
def mulai_laporan(
    data: LaporanHarianCreate, email_supir: str = Depends(verifikasi_token)
):
    """
    Membuat entri data awal untuk laporan harian operasional pengemudi.
    """
    hasil = create_laporan_harian(data, email_supir)
    return hasil


# ─── ENDPOINT: PENGISIAN DATA INSPEKSI ────────────────────────────────
@router.post("/inspeksi")
def inspeksi_kendaraan(
    laporan_id: str, data: InspeksiCreate, email_supir: str = Depends(verifikasi_token)
):
    """
    Menyimpan hasil pemeriksaan kelaikan kondisi fisik kendaraan.
    """
    hasil = create_inspeksi_kendaraan(laporan_id, data)
    return hasil


# ─── ENDPOINT: PENGISIAN SESI PERJALANAN ──────────────────────────────
@router.post("/sesi")
def sesi_perjalanan(
    laporan_id: str,
    data: TripSessionCreate,
    email_supir: str = Depends(verifikasi_token),
):
    """
    Merekam data odometer dan waktu operasi untuk rute perjalanan pengemudi.
    """
    hasil = create_sesi_perjalanan(laporan_id, data)
    return hasil


# ─── ENDPOINT: UNGGAH FOTO KEHADIRAN (SELFIE) ─────────────────────────
@router.post("/upload-selfie")
async def upload_selfie(
    foto: UploadFile = File(...), email_supir: str = Depends(verifikasi_token)
):
    """
    Menerima file gambar (selfie) untuk validasi kehadiran,
    mengunggahnya ke infrastruktur penyimpanan (Storage),
    dan mengembalikan URL akses publik.
    """
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

        response = supabase.storage.from_("selfie_driver").upload(
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

---
