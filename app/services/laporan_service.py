from fastapi import HTTPException, status
from app.db.database import supabase
from app.schemas.laporan import LaporanHarianCreate
from app.schemas.inspeksi import InspeksiCreate
from app.schemas.perjalanan import TripSessionCreate


# ─── FUNGSI 1: BIKIN LAPORAN HARIAN ──────────────────────
def create_laporan_harian(data: LaporanHarianCreate, id_supir: str):
    try:
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
        return response.data[0]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan teknis saat menyimpan inisialisasi laporan harian: {str(e)}",
        )


# ─── FUNGSI 2: SIMPAN INSPEKSI ───────────
def create_inspeksi_kendaraan(laporan_id: str, data: InspeksiCreate):
    # 1. CEK DULU LAPORANNYA ADA APA KAGA DI DATABASE
    cek_laporan = (
        supabase.table("daily_reports").select("id").eq("id", laporan_id).execute()
    )
    if not cek_laporan.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Laporan dengan ID {laporan_id} tidak ditemukan. Silakan tekan 'Mulai Laporan' terlebih dahulu.",
        )

    # 2. KALO ADA, BARU MASUKIN DATANYA
    try:
        response = (
            supabase.table("inspections")
            .insert(
                {
                    "laporan_id": laporan_id,
                    "rem": data.rem,
                    "ac": data.ac,
                    "lampu": data.lampu,
                    "klakson": data.klakson,
                    "wiper": data.wiper,
                    "lampu_rem": data.lampu_rem,
                    "bell": data.bell,
                    "pintu": data.pintu,
                    "kebersihan": data.kebersihan,
                    "catatan": data.catatan,
                }
            )
            .execute()
        )
        return response.data[0]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan teknis saat menyimpan data inspeksi kendaraan: {str(e)}",
        )


# ─── FUNGSI 3: SIMPAN SESI ───────────────
def create_sesi_perjalanan(laporan_id: str, data: TripSessionCreate):
    # 1. CEK DULU LAPORANNYA ADA APA KAGA DI DATABASE
    cek_laporan = (
        supabase.table("daily_reports").select("id").eq("id", laporan_id).execute()
    )
    if not cek_laporan.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Laporan dengan ID {laporan_id} tidak ditemukan. Silakan tekan 'Mulai Laporan' terlebih dahulu.",
        )

    # 2. LOGIKA: EVALUASI KETERLAMBATAN OTOMATIS
    status_telat = "TEPAT WAKTU"

    if data.jam_berangkat_start:
        jam_bersih = (
            data.jam_berangkat_start.replace(" WIB", "").replace(" wib", "").strip()
        )

        if data.tipe_sesi.upper() == "PAGI":
            if jam_bersih > "06:15":
                status_telat = "TERLAMBAT"

        elif data.tipe_sesi.upper() == "SIANG":
            if jam_bersih > "15:00":
                status_telat = "TERLAMBAT"

    # 3. PROSES: PENYIMPANAN DATA KE DATABASE
    try:
        response = (
            supabase.table("trip_sessions")
            .insert(
                {
                    "laporan_id": laporan_id,
                    "tipe_sesi": data.tipe_sesi,
                    "jam_berangkat_kantor": data.jam_berangkat_kantor,
                    "km_berangkat_kantor": data.km_berangkat_kantor,
                    "jam_berangkat_start": data.jam_berangkat_start,
                    "km_berangkat_start": data.km_berangkat_start,
                    "jam_tiba_finish": data.jam_tiba_finish,
                    "km_tiba_finish": data.km_tiba_finish,
                    "jumlah_penumpang": data.jumlah_penumpang,
                    "jam_tiba_kantor": data.jam_tiba_kantor,
                    "km_tiba_kantor": data.km_tiba_kantor,
                    "status_waktu": status_telat,
                }
            )
            .execute()
        )
        return response.data[0]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan teknis saat merekam data sesi perjalanan: {str(e)}",
        )
