from typing import Optional
from pydantic import BaseModel


# inspeksi setiap parts kendaraan
class InspeksiCreate(BaseModel):
    tipe_sesi: str  # <-- TAMBAHAN BARU
    rem: str
    ac: str
    lampu: str
    klakson: str
    wiper: str
    lampu_rem: str
    bell: str
    pintu: str
    kebersihan: str
    catatan: str
<<<<<<< HEAD
    tipe_sesi: str
=======
    tipe_sesi: str
>>>>>>> 2013a4f (chore: save progress sebelum pull)
