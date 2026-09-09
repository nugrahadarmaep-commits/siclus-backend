from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.auth import router as auth_router
from app.api.routes.laporan import router as laporan_router
from app.api.routes.admin import router as admin_router
from app.api.routes.driver import router as driver_router

# ─── DEFINISI TAGS METADATA (DOKUMENTASI OPENAPI / SWAGGER) ─────────────────
tags_metadata = [
    {
        "name": "Autentikasi",
        "description": "Layanan masuk sistem (Login) dan penerbitan token akses JWT.",
    },
    {
        "name": "Admin - Dashboard & Rekap",
        "description": "Pantauan operasional harian, statistik keterlambatan, dan ekspor rekapan ke Excel.",
    },
    {
        "name": "Admin - Manajemen Pengemudi",
        "description": "Kelola data akun pengemudi/supir (Pendaftaran, Perubahan Data, Hapus Akun).",
    },
    {
        "name": "Admin - Manajemen Jadwal",
        "description": "Pengaturan batas waktu keberangkatan Dishub dan kedatangan di titik awal rute.",
    },
    {
        "name": "Admin - Profil",
        "description": "Pengelolaan data profil mandiri administrator dan pembaruan foto profil.",
    },
    {
        "name": "Pengemudi - Operasional Harian",
        "description": "Alur pelaporan operasional supir: Checkpoint 1 sampai 4, inspeksi armada, dan swafoto (selfie).",
    },
    {
        "name": "Pengemudi - Akun & Jadwal",
        "description": "Informasi profil supir aktif, jadwal penugasan rute, dan riwayat operasional harian.",
    },
]

# ─── INISIALISASI MESIN UTAMA ───────────────────────────────────────────────
app = FastAPI(
    title="SICLUS API - Sistem Informasi Catatan & Laporan Pengemudi Bus",
    description="Backend API resmi untuk manajemen operasional, inspeksi kendaraan, dan rekapitulasi kehadiran pengemudi.",
    version="1.0.0",
    openapi_tags=tags_metadata,
)

# ─── KONFIGURASI KEAMANAN CORS ──────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── PENDAFTARAN ROUTER MESIN ───────────────────────────────────────────────
app.include_router(auth_router, prefix="/api/auth")
app.include_router(admin_router, prefix="/api/admin")
app.include_router(laporan_router, prefix="/api/laporan")
app.include_router(driver_router, prefix="/api/driver")


@app.get("/", tags=["Pemeriksaan Sistem"])
def status_sistem():
    """Memeriksa status operasional mesin backend."""
    return {"status": "Mesin SICLUS berjalan normal", "versi": "1.0.0"}

