import time
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from app.api.dependencies import verifikasi_pengemudi
from app.db.database import supabase
from app.services.driver_service import get_driver_active_penugasan

router = APIRouter()


# profil pengemudi
@router.get(
    "/profil",
    tags=["Pengemudi - Akun & Jadwal"],
    summary="Data Profil Pengemudi Aktif",
)
def get_profil_pengemudi(email_supir: str = Depends(verifikasi_pengemudi)):
    try:
        response = (
            supabase.table("users")
            .select("id, nama, email, role, trayek, bus, foto_profil")
            .eq("email", email_supir)
            .execute()
        )
        data_user = response.data
        if not data_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Data profil pengemudi tidak ditemukan di dalam sistem.",
            )
        return {"pesan": "Data profil berhasil ditarik.", "data": data_user[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan teknis saat menarik data profil: {str(e)}",
        )


# unggah foto profil pengemudi
@router.put(
    "/profil/foto",
    tags=["Pengemudi - Akun & Jadwal"],
    summary="Unggah Foto Profil Pengemudi",
)
async def update_foto_profil(
    foto: UploadFile = File(...), email_supir: str = Depends(verifikasi_pengemudi)
):
    try:
        ekstensi = foto.filename.split(".")[-1].lower()
        if ekstensi not in ["jpg", "jpeg", "png", "webp"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Format tidak didukung. Gunakan JPG, JPEG, PNG, atau WEBP.",
            )

        nama_prefix = email_supir.split("@")[0]
        nama_file_baru = f"avatar_{nama_prefix}_{int(time.time())}.{ekstensi}"

        isi_gambar = await foto.read()
        supabase.storage.from_("foto_profil").upload(
            file=isi_gambar,
            path=nama_file_baru,
            file_options={"content-type": foto.content_type},
        )

        url_publik = supabase.storage.from_("foto_profil").get_public_url(nama_file_baru)

        supabase.table("users").update({"foto_profil": url_publik}).eq(
            "email", email_supir
        ).execute()

        return {"pesan": "Foto profil berhasil diperbarui!", "foto_profil": url_publik}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan teknis saat memperbarui foto: {str(e)}",
        )


# histori riwayat perjalanan pengemudi
@router.get(
    "/riwayat",
    tags=["Pengemudi - Akun & Jadwal"],
    summary="Histori Riwayat Operasional Pengemudi",
)
def get_riwayat_pengemudi(email_supir: str = Depends(verifikasi_pengemudi)):
    try:
        user_res = (
            supabase.table("users")
            .select("id")
            .eq("email", email_supir)
            .execute()
        )
        id_supir = user_res.data[0]["id"] if user_res.data else None

        query = supabase.table("daily_reports").select("*, trip_sessions(*), inspections(*)")
        if id_supir:
            query = query.or_(f"id_supir.eq.{email_supir},id_supir.eq.{id_supir}")
        else:
            query = query.eq("id_supir", email_supir)

        response = query.order("tanggal", desc=True).order("created_at", desc=True).execute()
        data_riwayat = response.data or []

        # Ambil data penugasan supir untuk melengkapi jenis_kendaraan & kapasitas kendaraan
        try:
            penugasan_q = supabase.table("penugasan").select("*")
            if id_supir:
                penugasan_q = penugasan_q.or_(f"id_supir.eq.{email_supir},id_supir.eq.{id_supir}")
            else:
                penugasan_q = penugasan_q.eq("id_supir", email_supir)
            penugasan_res = penugasan_q.execute()
            penugasan_list = penugasan_res.data or []
        except Exception as e_pen:
            print("Warning fetch penugasan riwayat:", e_pen)
            penugasan_list = []

        for lap in data_riwayat:
            lap_tgl = str(lap.get("tanggal") or "")
            lap_trayek = (lap.get("trayek") or "").strip().upper()
            lap_bus = (lap.get("bus") or "").strip().upper()

            # Cocokkan penugasan spesifik berdasarkan tanggal dan rute/bus
            matched_task = next(
                (
                    p for p in penugasan_list
                    if str(p.get("tanggal") or "") == lap_tgl
                    and (
                        (p.get("trayek") or "").strip().upper() == lap_trayek
                        or (p.get("nopol_kendaraan") or "").strip().upper() == lap_bus
                    )
                ),
                next(
                    (p for p in penugasan_list if str(p.get("tanggal") or "") == lap_tgl),
                    None
                )
            )

            jenis = (matched_task.get("jenis_kendaraan") if matched_task else None) or "BUS"
            kapasitas = (matched_task.get("kapasitas_penumpang") if matched_task else None) or 50

            lap["jenis_kendaraan"] = jenis
            lap["kapasitas_penumpang"] = kapasitas
            lap["kapasitas"] = kapasitas
            lap["penugasan"] = matched_task

        return {
            "pesan": "Riwayat perjalanan berhasil ditarik.",
            "total_riwayat": len(data_riwayat),
            "data": data_riwayat,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan teknis saat menarik riwayat: {str(e)}",
        )


# jadwal penugasan operasional pengemudi
@router.get(
    "/jadwal",
    tags=["Pengemudi - Akun & Jadwal"],
    summary="Jadwal Penugasan Operasional Pengemudi",
)
def get_jadwal_hari_ini(email_supir: str = Depends(verifikasi_pengemudi)):
    """Menampilkan batas toleransi waktu keberangkatan dan kedatangan berdasarkan rute."""
    try:
        user_response = (
            supabase.table("users").select("id").eq("email", email_supir).execute()
        )
        if not user_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Data akun pengemudi tidak ditemukan.",
            )

        trayek_supir = None
        bus_supir = None

        try:
            penugasan_info = get_driver_active_penugasan(email_supir)
            active_task = penugasan_info.get("active")
            if active_task:
                trayek_supir = active_task.get("trayek")
                bus_supir = active_task.get("nopol_kendaraan")
        except Exception as e_penugasan:
            print("Warning cek penugasan jadwal:", e_penugasan)

        if not trayek_supir:
            return []

        jadwal_response = (
            supabase.table("schedules")
            .select("*")
            .ilike("trayek", trayek_supir)
            .execute()
        )
        jadwal_list = jadwal_response.data or []

        enriched_list = []
        for j in jadwal_list:
            sesi = (j.get("tipe_sesi") or "PAGI").upper()
            raw_keluar = str(j.get("batas_keluar_dishub") or "").strip()
            kembali = str(j.get("batas_tiba_start") or "").strip()[:5]

            if "|" in raw_keluar:
                parts = raw_keluar.split("|", 1)
                buka_formulir = parts[0].strip()[:5]
                keluar = parts[1].strip()[:5]
            else:
                buka_formulir = raw_keluar[:5]
                keluar = raw_keluar[:5]

            enriched_list.append(
                {
                    **j,
                    "tipe_sesi": sesi,
                    "jam_formulir_pengisian": buka_formulir,
                    "batas_keluar_dishub": keluar,
                    "batas_kembali_dishub": kembali,
                    "batas_tiba_start": kembali,
                }
            )

        return {
            "pesan": f"Jadwal operasional untuk rute {trayek_supir} berhasil ditarik.",
            "trayek": trayek_supir,
            "bus": bus_supir,
            "data": enriched_list,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan teknis saat menarik jadwal operasional: {str(e)}",
        )


# penugasan kendaraan hari ini
@router.get(
    "/penugasan/hari-ini",
    tags=["Pengemudi - Akun & Jadwal"],
    summary="Data Penugasan Kendaraan Hari Ini (Sugesti)",
)
def get_penugasan_hari_ini(email_supir: str = Depends(verifikasi_pengemudi)):
    """Menarik data penugasan kendaraan hari ini untuk pengemudi aktif."""
    try:
        penugasan_info = get_driver_active_penugasan(email_supir)
        active_task = penugasan_info.get("active")
        penugasan_list = penugasan_info.get("list") or []

        if not active_task:
            return {
                "pesan": "Belum ada penugasan kendaraan untuk Anda hari ini.",
                "data": None,
                "penugasan_list": [],
            }

        return {
            "pesan": "Data penugasan kendaraan hari ini berhasil ditarik.",
            "data": active_task,
            "penugasan_list": penugasan_list,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal menarik data penugasan: {str(e)}",
        )
