# ==============================================================================
# SERVICE: LAPORAN & INSPEKSI OPERASIONAL PENGEMUDI
# ==============================================================================

from fastapi import HTTPException, status
from datetime import datetime, timezone, timedelta
from app.db.database import supabase
from app.schemas.laporan import LaporanHarianCreate
from app.schemas.inspeksi import InspeksiCreate
from app.schemas.perjalanan import (
    SesiCP1Create,
    SesiCP3Update,
    SesiCP4Update,
)

# Waktu WIB (UTC+7) untuk acuan backend
WIB = timezone(timedelta(hours=7))


# ==============================================================================
# INISIALISASI LAPORAN HARIAN
# ==============================================================================
def create_laporan_harian(data: LaporanHarianCreate, id_supir: str):
    try:
        cek_laporan = (
            supabase.table("daily_reports")
            .select("*")
            .eq("id_supir", id_supir)
            .eq("tanggal", str(data.tanggal))
            .execute()
        )
        
        if cek_laporan.data:
            return cek_laporan.data[0]
            
        response = (
            supabase.table("daily_reports")
            .insert(
                {
                    "tanggal": str(data.tanggal),
                    "id_supir": id_supir,
                    "trayek": data.trayek,
                    "bus": data.bus,
                }
            )
            .execute()
        )
        if response.data:
            return response.data[0]
        raise HTTPException(status_code=500, detail="Gagal membuat record laporan harian baru.")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal inisialisasi laporan: {str(e)}",
        )


# ==============================================================================
# INSPEKSI KONDISI FISIK ARMADA BUS
# ==============================================================================
def create_inspeksi_kendaraan(laporan_id: str, data: InspeksiCreate):
    cek = supabase.table("daily_reports").select("id").eq("id", laporan_id).execute()
    if not cek.data:
        raise HTTPException(status_code=404, detail="Laporan harian belum dibuat!")

    try:
        response = (
            supabase.table("inspections")
            .insert(
                {
                    "laporan_id": laporan_id,
                    "tipe_sesi": data.tipe_sesi.upper(),
                    "rem": data.rem,
                    "ac": data.ac,
                    "lampu": data.lampu,
                    "klakson": data.klakson,
                    "wiper": data.wiper,
                    "lampu_rem": data.lampu_rem,
                    "bell": data.bell,
                    "pintu": data.pintu,
                    "kebersihan": data.kebersihan,
                    "catatan": data.catatan or "",
                }
            )
            .execute()
        )
        return response.data[0]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal simpan inspeksi: {str(e)}",
        )


# ==============================================================================
# PROSES CHECKPOINT 1: KELUAR GARASI DISHUB
# ==============================================================================
def proses_cp1(laporan_id: str, data: SesiCP1Create, email_supir: str):
    cek = supabase.table("daily_reports").select("id").eq("id", laporan_id).execute()
    if not cek.data:
        raise HTTPException(status_code=404, detail="Laporan harian tidak valid.")

    waktu_sekarang = datetime.now(WIB)
    jam_teks = waktu_sekarang.strftime("%H:%M")

    # Cek radar keterlambatan CP1
    status_waktu = "TEPAT WAKTU"
    laporan = (
        supabase.table("daily_reports").select("trayek").eq("id", laporan_id).execute()
    )
    if not laporan.data or not laporan.data[0].get("trayek"):
        raise HTTPException(status_code=404, detail="Data trayek tidak ditemukan.")
    trayek = laporan.data[0]["trayek"]

    jadwal = (
        supabase.table("schedules")
        .select("batas_keluar_dishub")
        .ilike("trayek", trayek)
        .eq("tipe_sesi", data.tipe_sesi.upper())
        .execute()
    )

    if jadwal.data and jadwal.data[0].get("batas_keluar_dishub"):
        batas_maksimal = str(jadwal.data[0]["batas_keluar_dishub"]).strip()[:5]
        if jam_teks > batas_maksimal:
            status_waktu = "TERLAMBAT"

    try:
        response = (
            supabase.table("trip_sessions")
            .insert(
                {
                    "laporan_id": laporan_id,
                    "tipe_sesi": data.tipe_sesi.upper(),
                    "nopol_kendaraan": data.nopol_kendaraan,
                    "km_berangkat_kantor": data.km_berangkat_kantor,
                    "foto_awal": data.foto_awal,
                    "jam_berangkat_kantor": waktu_sekarang.isoformat(),
                    "status_waktu": status_waktu,
                }
            )
            .execute()
        )
        return {"pesan": "Check Point 1 Selesai", "data": response.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal CP1: {str(e)}")


# ==============================================================================
# PROSES CHECKPOINT 3: SELESAI TITIK AKHIR RUTE
# ==============================================================================
def proses_cp3(sesi_id: str, data: SesiCP3Update, email_supir: str):
    # Validasi CP1 (Karena CP2 sudah ditiadakan)
    sesi = (
        supabase.table("trip_sessions")
        .select("jam_berangkat_kantor")
        .eq("id", sesi_id)
        .execute()
    )
    if not sesi.data or not sesi.data[0].get("jam_berangkat_kantor"):
        raise HTTPException(
            status_code=403,
            detail="Gagal: Selesaikan Check Point 1 (Keluar Garasi) terlebih dahulu!",
        )

    waktu_sekarang = datetime.now(WIB).isoformat()
    try:
        response = (
            supabase.table("trip_sessions")
            .update(
                {
                    "km_tiba_finish": data.km_tiba_finish,
                    "jumlah_penumpang": data.jumlah_penumpang,
                    "jam_tiba_finish": waktu_sekarang,
                }
            )
            .eq("id", sesi_id)
            .execute()
        )
        return {"pesan": "Check Point 3 Selesai", "data": response.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal CP3: {str(e)}")


# ==============================================================================
# PROSES CHECKPOINT 4: KEMBALI KE GARASI DISHUB
# ==============================================================================
def proses_cp4(sesi_id: str, data: SesiCP4Update, email_supir: str):
    # Validasi CP3
    sesi = (
        supabase.table("trip_sessions")
        .select("jam_tiba_finish")
        .eq("id", sesi_id)
        .execute()
    )
    if not sesi.data or not sesi.data[0].get("jam_tiba_finish"):
        raise HTTPException(
            status_code=403,
            detail="Gagal: Selesaikan Check Point 3 (Selesai Rute) terlebih dahulu!",
        )

    waktu_sekarang = datetime.now(WIB).isoformat()
    try:
        response = (
            supabase.table("trip_sessions")
            .update(
                {
                    "km_tiba_kantor": data.km_tiba_kantor,
                    "foto_akhir": data.foto_akhir,
                    "jam_tiba_kantor": waktu_sekarang,
                }
            )
            .eq("id", sesi_id)
            .execute()
        )
        return {"pesan": "Shift Laporan Selesai & Ditutup!", "data": response.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal CP4: {str(e)}")

