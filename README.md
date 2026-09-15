# SICLUS Backend ⚡

**SICLUS Backend** adalah RESTful API berkinerja tinggi yang dibangun menggunakan **FastAPI**, **Pydantic v2**, dan **Supabase (PostgreSQL)** untuk melayani sistem pelaporan operasional bus sekolah Dinas Perhubungan.

---

## 🏗️ Arsitektur & Struktur Folder (Modular Clean Code)

Backend ini dirancang dengan prinsip **Domain-Driven Modular Services** untuk mempermudah debugging dan penambahan fitur baru:

```text
siclus-backend/
├── app/
│   ├── api/
│   │   ├── dependencies.py          # Dependency injection (Auth, JWT, Role Checker)
│   │   └── routes/                  # API Endpoints per domain
│   │       ├── auth.py              # Login & registrasi token
│   │       ├── admin_dashboard_routes.py # Statistik & KPI operasional
│   │       ├── admin_penugasan_routes.py # CRUD jadwal & penugasan bus
│   │       ├── admin_users_routes.py     # Master data pengguna & supir
│   │       ├── driver.py            # Profil & penugasan supir
│   │       └── laporan.py           # Sesi perjalanan, CP1-CP3, inspeksi & upload foto
│   ├── core/                        # Konfigurasi aplikasi & enkripsi
│   │   ├── config.py
│   │   └── security.py
│   ├── db/                          # Koneksi client Supabase
│   │   └── database.py
│   ├── schemas/                     # Skema validasi data request & response Pydantic
│   │   ├── inspeksi.py
│   │   ├── laporan.py
│   │   ├── penugasan.py
│   │   └── user.py
│   ├── services/                    # Business Logic Layer per domain
│   │   ├── admin_dashboard_service.py
│   │   ├── admin_penugasan_service.py
│   │   ├── admin_users_service.py
│   │   ├── auth_service.py
│   │   ├── driver_service.py
│   │   └── laporan_service.py
│   └── main.py                      # Inisialisasi FastAPI & pendaftaran router
├── .env.example                     # Template konfigurasi environment
├── create_admin.py                  # Skrip pembuatan akun admin pertama
├── pyproject.toml                   # Konfigurasi proyek & dependensi (uv / pip)
└── README.md
```

---

## 🛠️ Panduan Memulai (Getting Started)

### 1. Prasyarat
- Python 3.12 atau lebih baru
- Package manager [uv](https://github.com/astral-sh/uv) (direkomendasikan) atau pip standard

### 2. Instalasi
```bash
# Clone repository
git clone https://github.com/nugrahadarmaep-commits/siclus-backend.git
cd siclus-backend

# Buat virtual environment & install dependensi menggunakan uv
uv sync
```
*(Atau jika menggunakan pip standard)*:
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

pip install -e .
```

### 3. Konfigurasi Environment
Salin file `.env.example` menjadi `.env`:
```bash
cp .env.example .env
```
Isi konfigurasi Supabase dan Secret Key JWT Anda:
```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-supabase-anon-or-service-key
SECRET_KEY=your-jwt-secret-key-here
```

### 4. Menjalankan Server
Gunakan `uv` untuk menjalankan server dalam mode pengembangan:
```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Server akan aktif di `http://localhost:8000`.

Dokumentasi interaktif OpenAPI (Swagger UI) dapat diakses melalui:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### 5. Membuat Akun Admin Pertama
Jalankan skrip pembantu untuk mendaftarkan akun administrator ke database Supabase:
```bash
uv run python create_admin.py
```
