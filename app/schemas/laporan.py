from datetime import date
from pydantic import BaseModel


# inisialisasi harian laporan
# Skema ini adalah cangkang utama untuk hari tersebut.
# ID Supir tidak perlu dikirim dari Frontend karena akan diambil otomatis
# dari tiket JWT (Token) demi keamanan.
class LaporanHarianCreate(BaseModel):
    tanggal: date
    trayek: str
    bus: str
