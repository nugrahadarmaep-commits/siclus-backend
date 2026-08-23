from typing import Optional
from pydantic import BaseModel


# inspeksi setiap parts kendaraan
class InspeksiCreate(BaseModel):
    rem: str
    ac: str
    lampu: str
    klakson: str
    wiper: str
    lampu_rem: str
    bell: str
    pintu: str
    kebersihan: str

    # opsional catatan kerusakan
    catatan: Optional[str] = None
