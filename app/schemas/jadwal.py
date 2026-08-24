from typing import Optional
from pydantic import BaseModel


# ==========================================
# 1. CETAKAN UNTUK BIKIN JADWAL BARU (POST)
# ==========================================
class JadwalCreate(BaseModel):
    trayek: str
    tipe_sesi: str  # Wajib isi 'PAGI' atau 'SIANG'
    batas_keluar_dishub: str  # Format string, contoh: '05:45'
    batas_tiba_start: str  # Format string, contoh: '06:15'


# ==========================================
# 2. CETAKAN UNTUK EDIT JADWAL (PUT)
# ==========================================
# Trayek dan sesi kaga usah diedit, Admin cukup ngedit jamnya aja.
class JadwalUpdate(BaseModel):
    batas_keluar_dishub: Optional[str] = None
    batas_tiba_start: Optional[str] = None
