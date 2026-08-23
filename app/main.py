from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.auth import router as auth_router
from app.api.routes.laporan import router as laporan_router
from app.api.routes.admin import router as admin_router

# Inisialisasi Mesin Utama
app = FastAPI(
    title="SICLUS API",
    description="API Endpoint untuk Sistem Inspeksi & Catatan Laporan Sopir",
    version="1.0.0"
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

# test
@app.get("/")
def root():
    return {"status": "mesin siclus berjalan!"}