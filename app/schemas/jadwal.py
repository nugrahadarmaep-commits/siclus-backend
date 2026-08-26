from typing import Optional
from pydantic import BaseModel


# ─── SCHEMA: PEMBUATAN JADWAL BARU (CREATE) ───────────────────────────
class JadwalCreate(BaseModel):
    trayek: str
    tipe_sesi: str
    batas_keluar_dishub: str
    batas_tiba_start: str


# ─── SCHEMA: PEMBARUAN JADWAL (UPDATE) ────────────────────────────────
class JadwalUpdate(BaseModel):
    batas_keluar_dishub: Optional[str] = None
    batas_tiba_start: Optional[str] = None
