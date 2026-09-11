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
    ban: str
    pintu: str
    kebersihan: str
    mesin: str
    catatan: Optional[str] = ""

