from typing import Optional
from pydantic import BaseModel


# inspeksi kendaraan
class InspeksiCreate(BaseModel):
    tipe_sesi: str
    rem: str
    ac: str
    lampu: str
    klakson: str
    wiper: str
    lampu_rem: str
    bell: str
    pintu: str
    kebersihan: str
    catatan: Optional[str] = ""

