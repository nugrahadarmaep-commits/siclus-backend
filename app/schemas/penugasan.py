from typing import Optional
from pydantic import BaseModel
from datetime import date


class PenugasanCreate(BaseModel):
    id_supir: str
    tanggal: date
    nopol_kendaraan: str
    jenis_kendaraan: str
    kapasitas_penumpang: int
    trayek: str


class PenugasanUpdate(BaseModel):
    id_supir: Optional[str] = None
    tanggal: Optional[date] = None
    nopol_kendaraan: Optional[str] = None
    jenis_kendaraan: Optional[str] = None
    kapasitas_penumpang: Optional[int] = None
    trayek: Optional[str] = None
