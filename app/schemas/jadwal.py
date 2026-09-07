from typing import Optional
from pydantic import BaseModel


# create jadwal baru
class JadwalCreate(BaseModel):
    trayek: str
    tipe_sesi: str
    batas_keluar_dishub: str
    batas_tiba_start: str


# update jadwal
class JadwalUpdate(BaseModel):
    trayek: Optional[str] = None
    tipe_sesi: Optional[str] = None
    batas_keluar_dishub: Optional[str] = None
    batas_tiba_start: Optional[str] = None
