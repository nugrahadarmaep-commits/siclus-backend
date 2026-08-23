from typing import Optional
from pydantic import BaseModel

# ==========================================
# 1. CETAKAN DATA SESI PERJALANAN (PAGI / SIANG)
# ==========================================
# Skema ini akan dipakai dua kali sehari (Sesi PAGI dan Sesi SIANG).
# Tipe datanya string untuk jam (contoh: "05:50 WIB") agar sinkron dengan Frontend.
class TripSessionCreate(BaseModel):
    tipe_sesi: str  # Wajib diisi "PAGI" atau "SIANG"
    
    # --- DATA BERANGKAT DARI DISHUB ---
    jam_berangkat_kantor: Optional[str] = None 
    km_berangkat_kantor: Optional[int] = None
    
    # --- DATA TIBA DI TITIK START (TERMINAL/SEKOLAH) ---
    jam_berangkat_start: Optional[str] = None
    km_berangkat_start: Optional[int] = None
    
    # --- DATA TIBA DI TITIK FINISH (SEKOLAH/TERMINAL) ---
    jam_tiba_finish: Optional[str] = None
    km_tiba_finish: Optional[int] = None
    
    # --- DATA JUMLAH PENUMPANG ---
    jumlah_penumpang: Optional[int] = 0
    
    # --- DATA KEMBALI KE DISHUB ---
    jam_tiba_kantor: Optional[str] = None
    km_tiba_kantor: Optional[int] = None