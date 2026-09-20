from pydantic import BaseModel, Field

# cp 1
class SesiCP1Create(BaseModel):
    tipe_sesi: str
    nopol_kendaraan: str
    km_berangkat_kantor: int
    foto_awal: str

# cp 2 (Tiba di Titik Akhir Rute / Sekolah)
class SesiCP2Update(BaseModel):
    km_tiba_finish: int
    jumlah_penumpang: int = Field(..., ge=0, le=150, description="Kapasitas jumlah penumpang wajar")

# cp 3 (Kembali ke Garasi / Kantor Dishub)
class SesiCP3Update(BaseModel):
    km_tiba_kantor: int
    foto_akhir: str
