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
