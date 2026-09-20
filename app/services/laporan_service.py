from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, status
from app.db.database import supabase
from app.schemas.laporan import LaporanHarianCreate
from app.schemas.inspeksi import InspeksiCreate
from app.schemas.perjalanan import (
    SesiCP1Create,
    SesiCP2Update,
    SesiCP3Update,
)

WIB = timezone(timedelta(hours=7))


# inisialisasi laporan harian
def create_laporan_harian(data: LaporanHarianCreate, id_supir: str):
    try:
        # resolusi identitas supir
        user_res = (
            supabase.table("users")
            .select("id, email, nama")
            .or_(f"email.eq.{id_supir},id.eq.{id_supir}")
            .execute()
        )
        user_data = user_res.data[0] if user_res.data else None
        driver_id = user_data["id"] if user_data else id_supir
        driver_email = user_data["email"] if user_data else id_supir

        # validasi penugasan resmi dari admin
        penugasan_query = (
            supabase.table("penugasan")
            .select("*")
            .or_(f"id_supir.eq.{driver_id},id_supir.eq.{driver_email}")
            .eq("tanggal", str(data.tanggal))
        )
        if data.trayek:
            penugasan_query = penugasan_query.ilike("trayek", data.trayek.strip())
        if data.bus:
            penugasan_query = penugasan_query.ilike("nopol_kendaraan", data.bus.strip())

        cek_penugasan = penugasan_query.execute()
        if not cek_penugasan.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tidak ada penugasan kendaraan resmi dari Admin untuk Anda pada rute ini hari ini.",
            )

        penugasan_matched = cek_penugasan.data[0]
        canonical_trayek = penugasan_matched.get("trayek") or data.trayek
        canonical_bus = penugasan_matched.get("nopol_kendaraan") or data.bus

        # periksa laporan yang sudah berjalan untuk penugasan ini
        query = (
            supabase.table("daily_reports")
            .select("*, trip_sessions(*)")
            .or_(f"id_supir.eq.{driver_id},id_supir.eq.{driver_email}")
            .eq("tanggal", str(data.tanggal))
        )
        if canonical_trayek:
            query = query.ilike("trayek", canonical_trayek.strip())
        if canonical_bus:
            query = query.ilike("bus", canonical_bus.strip())

        cek_laporan = query.order("created_at", desc=True).execute()

        if cek_laporan.data:
            for rep in cek_laporan.data:
                sessions = rep.get("trip_sessions") or []
                has_pagi = any(
                    (s.get("tipe_sesi") or "").upper() == "PAGI"
                    and (s.get("km_tiba_kantor") is not None or s.get("jam_tiba_kantor") is not None)
                    for s in sessions
                )
                has_siang = any(
                    (s.get("tipe_sesi") or "").upper() == "SIANG"
                    and (s.get("km_tiba_kantor") is not None or s.get("jam_tiba_kantor") is not None)
                    for s in sessions
                )

                # jika ada laporan yang belum tuntas, gunakan kembali
                if not (has_pagi and has_siang):
                    return rep

            # jika seluruh sesi telah selesai, cegah pembuatan laporan ganda
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Operasional penugasan Anda hari ini telah SELESAI. Tidak dapat membuat laporan baru tanpa penugasan baru dari Admin.",
            )

        # buat laporan baru jika belum pernah dibuat
        payload = {
            "tanggal": str(data.tanggal),
            "id_supir": driver_id,
            "trayek": canonical_trayek,
            "bus": canonical_bus,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        response = supabase.table("daily_reports").insert(payload).execute()
        if response.data:
            return response.data[0]
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Gagal membuat record laporan harian baru.",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal inisialisasi laporan: {str(e)}",
        )


# inspeksi kendaraan
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
                    "ban": data.ban,
                    "pintu": data.pintu,
                    "kebersihan": data.kebersihan,
                    "mesin": data.mesin,
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


# proses checkpoint 1: keluar garasi dishub
def proses_cp1(laporan_id: str, data: SesiCP1Create, email_supir: str):
    cek = supabase.table("daily_reports").select("id").eq("id", laporan_id).execute()
    if not cek.data:
        raise HTTPException(status_code=404, detail="Laporan harian tidak valid.")

    waktu_sekarang = datetime.now(WIB)
    jam_teks = waktu_sekarang.strftime("%H:%M")

    # periksa keterlambatan keberangkatan berdasarkan jadwal
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

    if jadwal.data:
        raw_keluar = str(jadwal.data[0].get("batas_keluar_dishub") or "").strip()
        if "|" in raw_keluar:
            buka_teks, batas_keluar = raw_keluar.split("|", 1)
        else:
            buka_teks = ""
            batas_keluar = raw_keluar

        # validasi jam buka form
        buka_teks = buka_teks.strip()[:5]
        if buka_teks and buka_teks != "00:00" and jam_teks < buka_teks:
            raise HTTPException(
                status_code=403,
                detail=f"Sesi {data.tipe_sesi.upper()} belum dibuka. Jadwal buka pukul {buka_teks} WIB.",
            )

        # validasi keterlambatan
        batas_keluar = batas_keluar.strip()[:5]
        if batas_keluar and batas_keluar != "00:00" and jam_teks > batas_keluar:
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


# proses checkpoint 2: selesai titik akhir rute / sekolah
def proses_cp2(sesi_id: str, data: SesiCP2Update, email_supir: str):
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
        return {"pesan": "Check Point 2 Selesai", "data": response.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal CP2: {str(e)}")


# proses checkpoint 3: kembali ke garasi dishub
def proses_cp3(sesi_id: str, data: SesiCP3Update, email_supir: str):
    sesi = (
        supabase.table("trip_sessions")
        .select("jam_tiba_finish")
        .eq("id", sesi_id)
        .execute()
    )
    if not sesi.data or not sesi.data[0].get("jam_tiba_finish"):
        raise HTTPException(
            status_code=403,
            detail="Gagal: Selesaikan Check Point 2 (Selesai Rute) terlebih dahulu!",
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
        raise HTTPException(status_code=500, detail=f"Gagal CP3: {str(e)}")
