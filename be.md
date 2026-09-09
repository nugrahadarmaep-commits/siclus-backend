# SICLUS Backend - Source Code Documentation

Dokumentasi lengkap seluruh file source code proyek **SICLUS Backend** terbaru (Update 9 September 2026, 12:00 WIB) murni tanpa modifikasi kode sumber.

---

## 📁 Struktur Direktori Proyek

```text
siclus-backend/
├── .env.example
├── .gitignore
├── .python-version
├── create_admin.py
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
    │   ├── penugasan.py
    │   ├── perjalanan.py
    │   └── user.py
    └── services/
        ├── __init__.py
        ├── admin_service.py
        ├── auth_service.py
        └── laporan_service.py
```

---

## 📑 Daftar Isi

### 🛠️ CLI Management Tools
- [`create_admin.py`](#1-create_adminpy)

### ⚙️ Konfigurasi & Lingkungan
- [`pyproject.toml`](#2-pyprojecttoml)
- [`.env.example`](#3-envexample)
- [`.gitignore`](#4-gitignore)
- [`.python-version`](#5-python-version)

### 🚀 Entry Point Aplikasi
- [`app/__init__.py`](#6-app__init__py)
- [`app/main.py`](#7-appmainpy)

### 🛡️ Core & Keamanan
- [`app/core/__init__.py`](#8-appcore__init__py)
- [`app/core/config.py`](#9-appcoreconfigpy)
- [`app/core/security.py`](#10-appcoresecuritypy)

### 🗄️ Database
- [`app/db/__init__.py`](#11-appdb__init__py)
- [`app/db/database.py`](#12-appdbdatabasepy)

### 📋 Schemas (Pydantic Models)
- [`app/schemas/__init__.py`](#13-appschemas__init__py)
- [`app/schemas/user.py`](#14-appschemasuserpy)
- [`app/schemas/inspeksi.py`](#15-appschemasinspeksipy)
- [`app/schemas/jadwal.py`](#16-appschemasjadwalpy)
- [`app/schemas/penugasan.py`](#17-appschemaspenugasanpy)
- [`app/schemas/perjalanan.py`](#18-appschemasperjalananpy)
- [`app/schemas/laporan.py`](#19-appschemaslaporanpy)

### ⚙️ Services (Business Logic)
- [`app/services/__init__.py`](#20-appservices__init__py)
- [`app/services/admin_service.py`](#21-appservicesadmin_servicepy)
- [`app/services/auth_service.py`](#22-appservicesauth_servicepy)
- [`app/services/laporan_service.py`](#23-appserviceslaporan_servicepy)

### 🌐 API Routes (Endpoints)
- [`app/api/__init__.py`](#24-appapi__init__py)
- [`app/api/routes/__init__.py`](#25-appapiroutes__init__py)
- [`app/api/routes/auth.py`](#26-appapiroutesauthpy)
- [`app/api/routes/admin.py`](#27-appapiroutesadminpy)
- [`app/api/routes/driver.py`](#28-appapiroutesdriverpy)
- [`app/api/routes/laporan.py`](#29-appapirouteslaporanpy)

---

## 1. `create_admin.py`

```python
"""
SICLUS CLI Management Tool: Admin Account Provisioning
"""

import sys
import getpass
import argparse
import re
from typing import Optional, Tuple
from email_validator import validate_email, EmailNotValidError

from app.core.security import get_password_hash
from app.db.database import supabase


def generate_next_admin_id() -> str:
    """
    Menghasilkan ID Admin secara otomatis dengan format ADMxxx (misal: ADM001 -> ADM002).
    Mencegah human error saat menentukan ID manual.
    """
    try:
        res = (
            supabase.table("users")
            .select("id")
            .ilike("id", "ADM%")
            .order("id", desc=True)
            .limit(20)
            .execute()
        )

        max_num = 0
        if res.data:
            for row in res.data:
                match = re.match(r"^ADM(\d+)$", str(row.get("id", "")).strip().upper())
                if match:
                    val = int(match.group(1))
                    if val > max_num:
                        max_num = val

        next_id = f"ADM{max_num + 1:03d}"
        return next_id
    except Exception:
        return "ADM001"


def validate_input(email: str, password: str) -> Tuple[bool, str]:
    """Validasi ketat input email dan kompleksitas password."""
    # 1. Validasi RFC Email
    try:
        valid = validate_email(email, check_deliverability=False)
        email_clean = valid.normalized
    except EmailNotValidError as e:
        return False, f"Format email tidak valid: {str(e)}"

    # 2. Validasi Kekuatan Password
    if len(password) < 8:
        return False, "Password minimal 8 karakter demi standar keamanan production."
    if not any(char.isdigit() for char in password):
        return False, "Password harus mengandung minimal 1 angka."
    if not any(char.isalpha() for char in password):
        return False, "Password harus mengandung minimal 1 huruf."

    return True, email_clean


def check_existing_user(admin_id: str, email: str) -> Tuple[bool, Optional[str]]:
    """Cek keunikan akun di database Supabase."""
    try:
        res = (
            supabase.table("users")
            .select("id, email")
            .or_(f"id.eq.{admin_id},email.eq.{email}")
            .execute()
        )
        if res.data:
            for user in res.data:
                if user.get("id") == admin_id:
                    return True, f"ID Admin '{admin_id}' sudah digunakan."
                if user.get("email") == email:
                    return True, f"Email '{email}' sudah terdaftar pada user lain."
        return False, None
    except Exception as e:
        return True, f"Gagal menghubungi server database: {str(e)}"


def prompt_user_data(args: argparse.Namespace) -> Tuple[str, str, str, str]:
    """Mengumpulkan dan memvalidasi data user baik dari argumen CLI atau interaktif."""
    # Handle ID
    default_id = generate_next_admin_id()
    if args.id:
        admin_id = args.id.strip().upper()
    else:
        id_input = input(f"ID Admin [{default_id}]: ").strip().upper()
        admin_id = id_input if id_input else default_id

    # Handle Nama
    nama = args.nama.strip() if args.nama else input("Nama Lengkap Admin: ").strip()
    while not nama:
        print("[!] Nama tidak boleh kosong.")
        nama = input("Nama Lengkap Admin: ").strip()

    # Handle Email
    email_raw = args.email.strip() if args.email else input("Alamat Email: ").strip()
    while True:
        is_valid, res = validate_input(email_raw, "dummyPassword123")
        if is_valid:
            email = res
            break
        print(f"[!] {res}")
        email_raw = input("Alamat Email: ").strip()

    # Handle Password (Masked)
    if args.password:
        password = args.password
        is_valid, msg = validate_input(email, password)
        if not is_valid:
            print(f"[X] {msg}")
            sys.exit(1)
    else:
        while True:
            password = getpass.getpass("Password Baru (min. 8 karakter, huruf & angka): ").strip()
            is_valid, msg = validate_input(email, password)
            if not is_valid:
                print(f"[!] {msg}")
                continue

            confirm = getpass.getpass("Konfirmasi Password: ").strip()
            if password != confirm:
                print("[!] Konfirmasi password tidak cocok. Silakan ulangi.")
                continue
            break

    return admin_id, nama, email, password


def create_admin():
    parser = argparse.ArgumentParser(
        description="SICLUS Backend CLI - Registrasi Akun Administrator",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--id", help="ID Akun Admin kustom (opsional, auto-generated jika kosong)")
    parser.add_argument("--nama", help="Nama Lengkap Admin")
    parser.add_argument("--email", help="Email Akun Admin")
    parser.add_argument("--password", help="Password Admin (opsional, gunakan mode interaktif jika ingin aman)")

    args = parser.parse_args()

    print("\n" + "=" * 55)
    print("      SICLUS OPERATIONAL SYSTEM - PROVISI ADMIN      ")
    print("=" * 55)

    try:
        admin_id, nama, email, password = prompt_user_data(args)

        print("\n[*] Memvalidasi status duplikasi di Supabase...")
        exists, err_msg = check_existing_user(admin_id, email)
        if exists:
            print(f"[X] Gagal: {err_msg}")
            sys.exit(1)

        print("[*] Melakukan enkripsi password (Bcrypt)...")
        hashed_password = get_password_hash(password)

        payload = {
            "id": admin_id,
            "nama": nama,
            "email": email,
            "password": hashed_password,
            "role": "admin",
            "trayek": None,
            "bus": None,
            "foto_profil": None,
        }

        print("[*] Menyimpan record admin ke tabel 'users'...")
        res = supabase.table("users").insert(payload).execute()

        if res.data:
            print("\n" + "-" * 55)
            print(" [V] SUKSES: Akun Administrator Berhasil Dibuat!")
            print("-" * 55)
            print(f" ID Akun    : {admin_id}")
            print(f" Nama       : {nama}")
            print(f" Email      : {email}")
            print(f" Role       : admin")
            print(" Status     : Aktif & Terotentikasi")
            print("-" * 55)
            print(" Akun ini sekarang dapat langsung login ke Dashboard Admin.\n")
        else:
            print("[X] Terjadi kesalahan: Data tidak berhasil disimpan.")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n[!] Proses dibatalkan oleh pengguna (Ctrl+C).")
        sys.exit(0)
    except Exception as e:
        print(f"\n[X] Fatal Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    create_admin()
```

[Kembali ke Daftar Isi](#-daftar-isi)

---

## 2. `pyproject.toml`

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
    "pillow>=12.3.0",
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

## 3. `.env.example`

```env
# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-supabase-anon-or-service-key

# JWT Security Configuration
SECRET_KEY=your-jwt-secret-key-here
```

[Kembali ke Daftar Isi](#-daftar-isi)

---

## 4. `.gitignore`

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

## 5. `.python-version`

```text
3.14
```

[Kembali ke Daftar Isi](#-daftar-isi)

---

## 6. `app/__init__.py`

```python

```

[Kembali ke Daftar Isi](#-daftar-isi)

---

## 7. `app/main.py`

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

## 8. `app/core/__init__.py`

```python

```

[Kembali ke Daftar Isi](#-daftar-isi)

---

## 9. `app/core/config.py`

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

## 10. `app/core/security.py`

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

## 11. `app/db/__init__.py`

```python

```

[Kembali ke Daftar Isi](#-daftar-isi)

---

## 12. `app/db/database.py`

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

## 13. `app/schemas/__init__.py`

```python

```

[Kembali ke Daftar Isi](#-daftar-isi)

---

## 14. `app/schemas/user.py`

```python
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


# update profil pribadi admin (nama)
class AdminProfileUpdate(BaseModel):
    nama_lengkap: str
```

[Kembali ke Daftar Isi](#-daftar-isi)

---

## 15. `app/schemas/inspeksi.py`

```python
from typing import Optional
from pydantic import BaseModel


# inspeksi kendaraan
class InspeksiCreate(BaseModel):
    tipe_sesi: str
    rem: str
    ac: str
    lampu: str
    klakson: str
    wiper: str
    lampu_rem: str
    bell: str
    pintu: str
    kebersihan: str
    mesin: str
    catatan: Optional[str] = ""
```

[Kembali ke Daftar Isi](#-daftar-isi)

---

## 16. `app/schemas/jadwal.py`

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

## 17. `app/schemas/penugasan.py`

```python
from typing import Optional
from pydantic import BaseModel
from datetime import date


class PenugasanCreate(BaseModel):
    id_supir: str
    tanggal: date
    nopol_kendaraan: str
    jenis_kendaraan: str
    kapasitas_penumpang: int
    trayek: str


class PenugasanUpdate(BaseModel):
    id_supir: Optional[str] = None
    tanggal: Optional[date] = None
    nopol_kendaraan: Optional[str] = None
    jenis_kendaraan: Optional[str] = None
    kapasitas_penumpang: Optional[int] = None
    trayek: Optional[str] = None
```

[Kembali ke Daftar Isi](#-daftar-isi)

---

## 18. `app/schemas/perjalanan.py`

```python
from pydantic import BaseModel

# cp 1
class SesiCP1Create(BaseModel):
    tipe_sesi: str
    nopol_kendaraan: str
    km_berangkat_kantor: int
    foto_awal: str

# cp 2
class SesiCP3Update(BaseModel):
    km_tiba_finish: int
    jumlah_penumpang: int

# cp 3
class SesiCP4Update(BaseModel):
    km_tiba_kantor: int
    foto_akhir: str
```

[Kembali ke Daftar Isi](#-daftar-isi)

---

## 19. `app/schemas/laporan.py`

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

## 20. `app/services/__init__.py`

```python

```

[Kembali ke Daftar Isi](#-daftar-isi)

---

## 21. `app/services/admin_service.py`

```python
# ==============================================================================
# SERVICE: ADMINISTRATOR OPERATIONS
# ==============================================================================

from io import BytesIO
from typing import Optional
from datetime import date
import time
import pandas as pd
from fastapi import HTTPException, status, UploadFile
from fastapi.responses import StreamingResponse

from app.db.database import supabase
from app.core.security import get_password_hash
from app.schemas.user import UserRegister, UserUpdate, AdminProfileUpdate
from app.schemas.jadwal import JadwalCreate, JadwalUpdate
from app.schemas.penugasan import PenugasanCreate, PenugasanUpdate


# ==============================================================================
# DASHBOARD & STATISTIK OPERASIONAL
# ==============================================================================

def get_dashboard_metrics():
    """Menghitung metrik kehadiran dan keterlambatan driver hari ini."""
    try:
        tanggal_hari_ini = str(date.today())

        # Hitung total armada driver terdaftar
        users_res = (
            supabase.table("users")
            .select("id")
            .in_("role", ["pengemudi", "driver", "DRIVER", "Driver"])
            .execute()
        )
        total_supir = len(users_res.data)

        # Hitung laporan yang masuk hari ini
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal hitung metrik dashboard: {str(e)}",
        )


# ==============================================================================
# REKAPITULASI & LAPORAN OPERASIONAL
# ==============================================================================
def get_rekap_operasional():
    """Mengambil seluruh data rekap harian lengkap beserta inspeksi dan sesi."""
    try:
        response = (
            supabase.table("daily_reports")
            .select("*, inspections(*), trip_sessions(*), users(nama, trayek, bus)")
            .execute()
        )
        return {
            "pesan": "Rekapitulasi ditarik.",
            "total_data": len(response.data),
            "data": response.data,
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


def get_riwayat_harian_grouped():
    """Mengambil riwayat laporan operasional yang dikelompokkan berdasarkan tanggal."""
    try:
        response = (
            supabase.table("daily_reports")
            .select("*, users(nama), trip_sessions(status_waktu, tipe_sesi)")
            .order("tanggal", desc=True)
            .execute()
        )

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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


def export_rekap_to_excel(id_supir: Optional[str] = None):
    """Menghasilkan file Excel rekapan operasional harian untuk diunduh."""
    try:
        query = supabase.table("daily_reports").select(
            "*, inspections(*), trip_sessions(*), users(nama)"
        )

        if id_supir:
            query = query.eq("id_supir", id_supir)

        response = query.execute()
        data_laporan = response.data

        if not data_laporan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data laporan kosong.")

        tabel_excel = []
        for baris in data_laporan:
            sesi_list = baris.get("trip_sessions", [])
            sesi = sesi_list[0] if sesi_list else {}
            user_info = baris.get("users") or {}
            nama_driver = user_info.get("nama") or baris.get("id_supir") or "-"

            tabel_excel.append(
                {
                    "Tanggal Operasional": baris.get("tanggal"),
                    "Nama Driver": nama_driver,
                    "ID Driver": baris.get("id_supir"),
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
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal export Excel: {str(e)}",
        )


# ==============================================================================
# MANAJEMEN AKUN DRIVER (SUPIR)
# ==============================================================================
def get_all_drivers():
    """Mengambil daftar seluruh akun pengemudi/driver."""
    try:
        response = (
            supabase.table("users")
            .select("id, nama, email, trayek, bus, foto_profil")
            .in_("role", ["pengemudi", "driver", "DRIVER", "Driver"])
            .execute()
        )
        return {
            "pesan": "Daftar pengemudi ditarik.",
            "total": len(response.data),
            "data": response.data,
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


def create_driver(data: UserRegister):
    """Menambahkan akun supir/driver baru oleh admin."""
    if not data.id.strip() or not data.email.strip() or not data.password.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Data tidak boleh kosong.")

    # Validasi keunikan ID dan Email
    if supabase.table("users").select("id").eq("id", data.id).execute().data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ID sudah terdaftar.")
    if supabase.table("users").select("id").eq("email", data.email).execute().data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email sudah dipakai.")

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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


def update_driver(user_id: str, data: UserUpdate):
    """Memperbarui informasi akun supir/driver."""
    try:
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tidak ada data diubah.")

        if "nama_lengkap" in update_data:
            update_data["nama"] = update_data.pop("nama_lengkap")

        if "password" in update_data:
            pw = str(update_data["password"]).strip()
            if pw:
                update_data["password"] = get_password_hash(pw)
            else:
                update_data.pop("password")

        response = (
            supabase.table("users").update(update_data).eq("id", user_id).execute()
        )
        if not response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supir tidak ditemukan.")

        user_diperbarui = response.data[0]
        user_diperbarui.pop("password", None)
        return {"pesan": "Data diperbarui.", "data": user_diperbarui}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


def delete_driver(user_id: str):
    """Menghapus akun supir/driver dari sistem."""
    try:
        response = supabase.table("users").delete().eq("id", user_id).execute()
        if not response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supir tidak ditemukan.")
        return {"pesan": f"Akun {user_id} dihapus."}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ==============================================================================
# MANAJEMEN JADWAL OPERASIONAL
# ==============================================================================
def get_all_schedules():
    """Mengambil daftar seluruh jadwal operasional."""
    try:
        response = supabase.table("schedules").select("*").order("trayek").execute()
        return {
            "pesan": "Jadwal ditarik.",
            "total": len(response.data),
            "data": response.data,
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


def create_schedule(data: JadwalCreate):
    """Menambahkan jadwal rute baru."""
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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


def update_schedule(jadwal_id: str, data: JadwalUpdate):
    """Memperbarui jadwal rute operasional."""
    try:
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tidak ada data diubah.")

        if "tipe_sesi" in update_data and update_data["tipe_sesi"]:
            update_data["tipe_sesi"] = update_data["tipe_sesi"].upper()

        response = (
            supabase.table("schedules")
            .update(update_data)
            .eq("id", jadwal_id)
            .execute()
        )
        if not response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Jadwal tidak ditemukan.")
        return {"pesan": "Jadwal diperbarui.", "data": response.data[0]}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


def delete_schedule(jadwal_id: str):
    """Menghapus jadwal operasional."""
    try:
        response = (
            supabase.table("schedules")
            .delete()
            .eq("id", jadwal_id)
            .execute()
        )
        if not response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Jadwal tidak ditemukan.")
        return {"pesan": f"Jadwal {jadwal_id} berhasil dihapus."}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ==============================================================================
# PROFIL PRIBADI ADMIN
# ==============================================================================
def update_admin_profile(email_admin: str, data: AdminProfileUpdate):

    """Memperbarui informasi identitas profil admin (nama lengkap)."""
    try:
        nama_baru = data.nama_lengkap.strip()
        if not nama_baru:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nama lengkap tidak boleh kosong.",
            )

        res = (
            supabase.table("users")
            .update({"nama": nama_baru})
            .eq("email", email_admin)
            .execute()
        )
        if not res.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Akun admin tidak ditemukan.",
            )

        user_info = res.data[0]
        user_info.pop("password", None)
        return {
            "pesan": "Profil admin berhasil diperbarui.",
            "data": user_info,
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


async def update_admin_avatar(email_admin: str, foto: UploadFile):
    """Mengunggah dan memperbarui foto profil admin."""
    try:
        ekstensi = foto.filename.split(".")[-1].lower() if "." in foto.filename else ""
        if ekstensi not in ["jpg", "jpeg", "png", "webp"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Format tidak didukung. Gunakan JPG, JPEG, PNG, atau WEBP.",
            )

        isi_gambar = await foto.read()
        nama_prefix = email_admin.split("@")[0]
        nama_file_baru = f"admin_avatar_{nama_prefix}_{int(time.time())}.{ekstensi}"

        supabase.storage.from_("foto_profil").upload(
            file=isi_gambar,
            path=nama_file_baru,
            file_options={"content-type": foto.content_type},
        )

        url_publik = supabase.storage.from_("foto_profil").get_public_url(nama_file_baru)

        supabase.table("users").update({"foto_profil": url_publik}).eq(
            "email", email_admin
        ).execute()

        return {
            "pesan": "Foto profil admin berhasil diupdate",
            "foto_profil": url_publik,
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ==============================================================================
# MANAJEMEN PENUGASAN KENDARAAN (HARIAN)
# ==============================================================================
def get_semua_penugasan():
    """Mengambil daftar seluruh penugasan harian."""
    try:
        response = (
            supabase.table("penugasan")
            .select("*, users(nama, email)")
            .order("tanggal", desc=True)
            .execute()
        )
        return {
            "pesan": "Daftar penugasan ditarik.",
            "total": len(response.data),
            "data": response.data,
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


def create_penugasan_harian(data: PenugasanCreate):
    """Admin membuat penugasan kendaraan untuk supir pada hari tertentu."""
    try:
        # Cek apakah supir ada
        user = supabase.table("users").select("id").eq("id", data.id_supir).execute()
        if not user.data:
            raise HTTPException(status_code=404, detail="Supir tidak ditemukan.")

        # Cek apakah sudah ada penugasan di tanggal yang sama untuk supir ini
        cek = (
            supabase.table("penugasan")
            .select("id")
            .eq("id_supir", data.id_supir)
            .eq("tanggal", str(data.tanggal))
            .execute()
        )
        
        if cek.data:
            # Update jika sudah ada
            res = (
                supabase.table("penugasan")
                .update(
                    {
                        "nopol_kendaraan": data.nopol_kendaraan,
                        "jenis_kendaraan": data.jenis_kendaraan,
                        "kapasitas_penumpang": data.kapasitas_penumpang,
                        "trayek": data.trayek,
                    }
                )
                .eq("id", cek.data[0]["id"])
                .execute()
            )
            pesan = "Penugasan diperbarui."
        else:
            # Insert baru
            res = (
                supabase.table("penugasan")
                .insert(
                    {
                        "id_supir": data.id_supir,
                        "tanggal": str(data.tanggal),
                        "nopol_kendaraan": data.nopol_kendaraan,
                        "jenis_kendaraan": data.jenis_kendaraan,
                        "kapasitas_penumpang": data.kapasitas_penumpang,
                        "trayek": data.trayek,
                    }
                )
                .execute()
            )
            pesan = "Penugasan dibuat."
            
        return {"pesan": pesan, "data": res.data[0]}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
```

[Kembali ke Daftar Isi](#-daftar-isi)

---

## 22. `app/services/auth_service.py`

```python
# ==============================================================================
# SERVICE: AUTENTIKASI PENGGUNA (LOGIN & TOKEN)
# ==============================================================================

from fastapi import HTTPException, status
from app.schemas.user import UserLogin
from app.core.security import create_access_token, verify_password
from app.db.database import supabase


def proses_login_supir(data_login: UserLogin):

    # 1. Ambil identitas login (bisa dikirim via field 'id' atau 'email')
    login_id = (data_login.id or data_login.email or "").strip()
    if not login_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kredensial tidak valid. ID Driver atau Email wajib diisi.",
        )

    # 2. Mencari data pengguna di database (prioritas: jika ada '@' cari email, selain itu cari ID)
    try:
        if "@" in login_id:
            response = (
                supabase.table("users").select("*").eq("email", login_id).execute()
            )
        else:
            response = (
                supabase.table("users").select("*").eq("id", login_id).execute()
            )

        db_user_list = response.data

        # Fallback pencarian silang jika percobaan pertama belum menemukan akun
        if not db_user_list:
            if "@" in login_id:
                alt_response = supabase.table("users").select("*").eq("id", login_id).execute()
            else:
                alt_response = supabase.table("users").select("*").eq("email", login_id).execute()
            db_user_list = alt_response.data

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan pada koneksi database: {str(e)}",
        )

    # 3. Validasi ketersediaan pengguna
    if not db_user_list:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kredensial tidak valid. ID Driver atau Email tidak ditemukan.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    db_user = db_user_list[0]

    # 4. Validasi Kata Sandi
    if not verify_password(data_login.password, db_user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kredensial tidak valid. Kata sandi salah.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 5. Token Akses (JWT)
    isi_tiket = {
        "sub": db_user["email"],
        "id": db_user["id"],
        "role": db_user["role"],
    }
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
            "foto_profil": db_user.get("foto_profil"),
        },
    }
```

[Kembali ke Daftar Isi](#-daftar-isi)

---

## 23. `app/services/laporan_service.py`

```python
# ==============================================================================
# SERVICE: LAPORAN & INSPEKSI OPERASIONAL PENGEMUDI
# ==============================================================================

from fastapi import HTTPException, status
from datetime import datetime, timezone, timedelta
from app.db.database import supabase
from app.schemas.laporan import LaporanHarianCreate
from app.schemas.inspeksi import InspeksiCreate
from app.schemas.perjalanan import (
    SesiCP1Create,
    SesiCP3Update,
    SesiCP4Update,
)

# Waktu WIB (UTC+7) untuk acuan backend
WIB = timezone(timedelta(hours=7))


# ==============================================================================
# INISIALISASI LAPORAN HARIAN
# ==============================================================================
def create_laporan_harian(data: LaporanHarianCreate, id_supir: str):
    try:
        cek_laporan = (
            supabase.table("daily_reports")
            .select("*")
            .eq("id_supir", id_supir)
            .eq("tanggal", str(data.tanggal))
            .execute()
        )
        
        if cek_laporan.data:
            return cek_laporan.data[0]
            
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
        if response.data:
            return response.data[0]
        raise HTTPException(status_code=500, detail="Gagal membuat record laporan harian baru.")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal inisialisasi laporan: {str(e)}",
        )


# ==============================================================================
# INSPEKSI KONDISI FISIK ARMADA BUS
# ==============================================================================
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
                    "tipe_sesi": data.tipe_sesi.upper(),
                    "rem": data.rem,
                    "ac": data.ac,
                    "lampu": data.lampu,
                    "klakson": data.klakson,
                    "wiper": data.wiper,
                    "lampu_rem": data.lampu_rem,
                    "bell": data.bell,
                    "pintu": data.pintu,
                    "kebersihan": data.kebersihan,
                    "catatan": data.catatan or "",
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


# ==============================================================================
# PROSES CHECKPOINT 1: KELUAR GARASI DISHUB
# ==============================================================================
def proses_cp1(laporan_id: str, data: SesiCP1Create, email_supir: str):
    cek = supabase.table("daily_reports").select("id").eq("id", laporan_id).execute()
    if not cek.data:
        raise HTTPException(status_code=404, detail="Laporan harian tidak valid.")

    waktu_sekarang = datetime.now(WIB)
    jam_teks = waktu_sekarang.strftime("%H:%M")

    # Cek radar keterlambatan CP1
    status_waktu = "TEPAT WAKTU"
    laporan = (
        supabase.table("daily_reports").select("trayek").eq("id", laporan_id).execute()
    )
    if not laporan.data or not laporan.data[0].get("trayek"):
        raise HTTPException(status_code=404, detail="Data trayek tidak ditemukan.")
    trayek = laporan.data[0]["trayek"]

    jadwal = (
        supabase.table("schedules")
        .select("batas_keluar_dishub")
        .ilike("trayek", trayek)
        .eq("tipe_sesi", data.tipe_sesi.upper())
        .execute()
    )

    if jadwal.data and jadwal.data[0].get("batas_keluar_dishub"):
        batas_maksimal = str(jadwal.data[0]["batas_keluar_dishub"]).strip()[:5]
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


# ==============================================================================
# PROSES CHECKPOINT 3: SELESAI TITIK AKHIR RUTE
# ==============================================================================
def proses_cp3(sesi_id: str, data: SesiCP3Update, email_supir: str):
    # Validasi CP1 (Karena CP2 sudah ditiadakan)
    sesi = (
        supabase.table("trip_sessions")
        .select("jam_berangkat_kantor")
        .eq("id", sesi_id)
        .execute()
    )
    if not sesi.data or not sesi.data[0].get("jam_berangkat_kantor"):
        raise HTTPException(
            status_code=403,
            detail="Gagal: Selesaikan Check Point 1 (Keluar Garasi) terlebih dahulu!",
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


# ==============================================================================
# PROSES CHECKPOINT 4: KEMBALI KE GARASI DISHUB
# ==============================================================================
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

## 24. `app/api/__init__.py`

```python

```

[Kembali ke Daftar Isi](#-daftar-isi)

---

## 25. `app/api/routes/__init__.py`

```python

```

[Kembali ke Daftar Isi](#-daftar-isi)

---

## 26. `app/api/routes/auth.py`

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

## 27. `app/api/routes/admin.py`

```python
# ==============================================================================
# ROUTE: ADMINISTRATOR
# ==============================================================================

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

from app.core.config import settings
from app.schemas.user import UserRegister, UserUpdate, AdminProfileUpdate
from app.schemas.jadwal import JadwalCreate, JadwalUpdate
from app.schemas.penugasan import PenugasanCreate, PenugasanUpdate
from app.services import admin_service
router = APIRouter()
security = HTTPBearer()


# ==============================================================================
# VERIFIKASI KEAMANAN ADMIN
# ==============================================================================
def verifikasi_admin(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
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
                detail="Akses ditolak. Endpoint eksklusif untuk Administrator.",
            )
        return email_user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Sesi kedaluwarsa.")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token tidak valid.")


# ==============================================================================
# DASHBOARD & REKAP OPERASIONAL
# ==============================================================================
@router.get(
    "/dashboard",
    tags=["Admin - Dashboard & Rekap"],
    summary="Statistik Ringkasan Dashboard",
)
def get_dashboard(email_admin: str = Depends(verifikasi_admin)):
    return admin_service.get_dashboard_metrics()


@router.get(
    "/rekap",
    tags=["Admin - Dashboard & Rekap"],
    summary="Rekapitulasi Operasional Keseluruhan",
)
def get_rekap(email_admin: str = Depends(verifikasi_admin)):
    return admin_service.get_rekap_operasional()


@router.get(
    "/riwayat-harian",
    tags=["Admin - Dashboard & Rekap"],
    summary="Riwayat Operasional per Tanggal",
)
def get_riwayat_harian(email_admin: str = Depends(verifikasi_admin)):
    return admin_service.get_riwayat_harian_grouped()


@router.get(
    "/export-excel",
    tags=["Admin - Dashboard & Rekap"],
    summary="Unduh Laporan Format Excel (.xlsx)",
)
def export_excel(
    id_supir: Optional[str] = None, email_admin: str = Depends(verifikasi_admin)
):
    return admin_service.export_rekap_to_excel(id_supir=id_supir)


# ==============================================================================
# MANAJEMEN AKUN DRIVER (SUPIR)
# ==============================================================================
@router.get(
    "/users",
    tags=["Admin - Manajemen Pengemudi"],
    summary="Daftar Seluruh Akun Pengemudi",
)
def get_semua_driver(email_admin: str = Depends(verifikasi_admin)):
    return admin_service.get_all_drivers()


@router.post(
    "/users",
    tags=["Admin - Manajemen Pengemudi"],
    summary="Tambah Akun Pengemudi Baru",
)
def tambah_driver(data: UserRegister, email_admin: str = Depends(verifikasi_admin)):
    return admin_service.create_driver(data)


@router.put(
    "/users/{user_id}",
    tags=["Admin - Manajemen Pengemudi"],
    summary="Perbarui Data Akun Pengemudi",
)
def edit_driver(
    user_id: str, data: UserUpdate, email_admin: str = Depends(verifikasi_admin)
):
    return admin_service.update_driver(user_id, data)


@router.delete(
    "/users/{user_id}",
    tags=["Admin - Manajemen Pengemudi"],
    summary="Hapus Akun Pengemudi",
)
def hapus_driver(user_id: str, email_admin: str = Depends(verifikasi_admin)):
    return admin_service.delete_driver(user_id)


# ==============================================================================
# MANAJEMEN JADWAL OPERASIONAL
# ==============================================================================
@router.get(
    "/jadwal",
    tags=["Admin - Manajemen Jadwal"],
    summary="Daftar Seluruh Jadwal Operasional",
)
def get_semua_jadwal(email_admin: str = Depends(verifikasi_admin)):
    return admin_service.get_all_schedules()


@router.post(
    "/jadwal",
    tags=["Admin - Manajemen Jadwal"],
    summary="Tambah Jadwal Rute Baru",
)
def tambah_jadwal(data: JadwalCreate, email_admin: str = Depends(verifikasi_admin)):
    return admin_service.create_schedule(data)


@router.put(
    "/jadwal/{jadwal_id}",
    tags=["Admin - Manajemen Jadwal"],
    summary="Perbarui Jadwal Operasional",
)
def edit_jadwal(
    jadwal_id: str, data: JadwalUpdate, email_admin: str = Depends(verifikasi_admin)
):
    return admin_service.update_schedule(jadwal_id, data)


@router.delete(
    "/jadwal/{jadwal_id}",
    tags=["Admin - Manajemen Jadwal"],
    summary="Hapus Jadwal Operasional",
)
def hapus_jadwal(jadwal_id: str, email_admin: str = Depends(verifikasi_admin)):
    return admin_service.delete_schedule(jadwal_id)


# ==============================================================================
# PROFIL AKUN ADMIN
# ==============================================================================
@router.put(
    "/profil",
    tags=["Admin - Profil"],
    summary="Perbarui Nama Profil Administrator",
)
def update_profil_admin(
    data: AdminProfileUpdate, email_admin: str = Depends(verifikasi_admin)
):
    return admin_service.update_admin_profile(email_admin, data)


@router.put(
    "/profil/foto",
    tags=["Admin - Profil"],
    summary="Unggah Foto Profil Administrator",
)
async def update_foto_profil_admin(
    foto: UploadFile = File(...), email_admin: str = Depends(verifikasi_admin)
):
    return await admin_service.update_admin_avatar(email_admin, foto)

# ==============================================================================
# MANAJEMEN PENUGASAN KENDARAAN (HARIAN)
# ==============================================================================
@router.get(
    "/penugasan",
    tags=["Admin - Penugasan"],
    summary="Lihat Semua Penugasan Kendaraan Harian",
)
def get_semua_penugasan(email_admin: str = Depends(verifikasi_admin)):
    return admin_service.get_semua_penugasan()


@router.post(
    "/penugasan",
    tags=["Admin - Penugasan"],
    summary="Buat/Update Penugasan Kendaraan Harian untuk Supir",
)
def create_penugasan_harian(
    data: PenugasanCreate, email_admin: str = Depends(verifikasi_admin)
):
    return admin_service.create_penugasan_harian(data)
```

[Kembali ke Daftar Isi](#-daftar-isi)

---

## 28. `app/api/routes/driver.py`

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

## 29. `app/api/routes/laporan.py`

```python
# ==============================================================================
# ROUTE: LAPORAN OPERASIONAL PENGEMUDI (DRIVER)
# ==============================================================================

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import time

from app.schemas.laporan import LaporanHarianCreate
from app.schemas.inspeksi import InspeksiCreate
from app.schemas.perjalanan import (
    SesiCP1Create,
    SesiCP3Update,
    SesiCP4Update,
)
from app.services.laporan_service import (
    create_laporan_harian,
    create_inspeksi_kendaraan,
    proses_cp1,
    proses_cp3,
    proses_cp4,
)
from app.core.config import settings
from app.db.database import supabase

router = APIRouter()
security = HTTPBearer()


# ==============================================================================
# VERIFIKASI KEAMANAN PENGEMUDI (TOKEN JWT)
# ==============================================================================
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


# ==============================================================================
# INISIALISASI LAPORAN HARIAN
# ==============================================================================
@router.post(
    "/mulai",
    tags=["Pengemudi - Operasional Harian"],
    summary="Mulai Sesi Laporan Harian Pengemudi",
)
def mulai_laporan(
    data: LaporanHarianCreate, email_supir: str = Depends(verifikasi_token)
):
    return create_laporan_harian(data, email_supir)


# ==============================================================================
# INSPEKSI KELAYAKAN ARMADA BUS
# ==============================================================================
@router.post(
    "/inspeksi",
    tags=["Pengemudi - Operasional Harian"],
    summary="Kirim Hasil Inspeksi Armada Bus",
)
def inspeksi_kendaraan(
    laporan_id: str, data: InspeksiCreate, email_supir: str = Depends(verifikasi_token)
):
    return create_inspeksi_kendaraan(laporan_id, data)


# ==============================================================================
# CHECKPOINT 1: KELUAR GARASI DISHUB
# ==============================================================================
@router.post(
    "/sesi/cp1",
    tags=["Pengemudi - Operasional Harian"],
    summary="Simpan Checkpoint 1 (Keluar Garasi Dishub)",
)
def sesi_checkpoint_1(
    laporan_id: str, data: SesiCP1Create, email_supir: str = Depends(verifikasi_token)
):
    return proses_cp1(laporan_id, data, email_supir)





# ==============================================================================
# CHECKPOINT 3: SELESAI TITIK AKHIR RUTE
# ==============================================================================
@router.put(
    "/sesi/cp3/{sesi_id}",
    tags=["Pengemudi - Operasional Harian"],
    summary="Simpan Checkpoint 3 (Selesai Titik Finish Rute)",
)
def sesi_checkpoint_3(
    sesi_id: str, data: SesiCP3Update, email_supir: str = Depends(verifikasi_token)
):
    return proses_cp3(sesi_id, data, email_supir)


# ==============================================================================
# CHECKPOINT 4: KEMBALI KE GARASI DISHUB
# ==============================================================================
@router.put(
    "/sesi/cp4/{sesi_id}",
    tags=["Pengemudi - Operasional Harian"],
    summary="Simpan Checkpoint 4 (Kembali Masuk Garasi Dishub)",
)
def sesi_checkpoint_4(
    sesi_id: str, data: SesiCP4Update, email_supir: str = Depends(verifikasi_token)
):
    return proses_cp4(sesi_id, data, email_supir)


# ==============================================================================
# VALIDASI SWAFOTO (SELFIE) KEHADIRAN
# ==============================================================================
@router.post(
    "/upload-selfie",
    tags=["Pengemudi - Operasional Harian"],
    summary="Unggah Swafoto (Selfie) Kehadiran Pengemudi",
)
async def upload_selfie(
    foto: UploadFile = File(...), email_supir: str = Depends(verifikasi_token)
):


    try:
        ekstensi = foto.filename.split(".")[-1].lower() if "." in foto.filename else ""
        if ekstensi not in ["jpg", "jpeg", "png", "webp"]:
            if foto.content_type in ["image/jpeg", "image/jpg"]:
                ekstensi = "jpg"
            elif foto.content_type == "image/png":
                ekstensi = "png"
            elif foto.content_type == "image/webp":
                ekstensi    = "webp"
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Format file tidak didukung. Harap gunakan JPG, JPEG, PNG, atau WEBP.",
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
