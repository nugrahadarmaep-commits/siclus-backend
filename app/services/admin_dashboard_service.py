from typing import Optional
from datetime import date
from fastapi import HTTPException, status
from app.db.database import supabase


def _get_user_lookup_map():
    """Mengambil peta profil supir untuk in-memory join aman tanpa ketergantungan Foreign Key."""
    try:
        res = (
            supabase.table("users")
            .select("id, nama, email, trayek, bus, role, foto_profil")
            .execute()
        )
        user_map = {}
        for u in res.data or []:
            if u.get("id"):
                user_map[u["id"]] = u
            if u.get("email"):
                user_map[u["email"]] = u
        return user_map
    except Exception:
        return {}


def get_dashboard_metrics():
    """Menghitung metrik kehadiran dan keterlambatan driver hari ini."""
    try:
        tanggal_hari_ini = str(date.today())

        # 1. Hitung total armada driver terdaftar di sistem
        users_res = (
            supabase.table("users")
            .select("id")
            .in_("role", ["pengemudi", "driver", "DRIVER", "Driver"])
            .execute()
        )
        total_supir = len(users_res.data or [])

        user_map = _get_user_lookup_map()

        def _canonical_id(ident):
            if not ident:
                return None
            u = user_map.get(ident)
            return u.get("id") if u else ident

        # 2. Hitung penugasan resmi hari ini (berdasarkan akun driver unik)
        penugasan_res = (
            supabase.table("penugasan")
            .select("id, id_supir, tipe_sesi")
            .eq("tanggal", tanggal_hari_ini)
            .execute()
        )
        penugasan_list = penugasan_res.data or []
        distinct_penugasan_supir_ids = set(
            _canonical_id(p.get("id_supir"))
            for p in penugasan_list
            if _canonical_id(p.get("id_supir"))
        )

        # 3. Hitung laporan yang masuk hari ini beserta trip_sessions
        reports_res = (
            supabase.table("daily_reports")
            .select("id, id_supir, trip_sessions(*)")
            .eq("tanggal", tanggal_hari_ini)
            .execute()
        )
        data_laporan_hari_ini = reports_res.data or []
        distinct_laporan_supir_ids = set(
            _canonical_id(r.get("id_supir"))
            for r in data_laporan_hari_ini
            if _canonical_id(r.get("id_supir"))
        )

        # Seluruh akun driver unik yang bertugas hari ini
        all_assigned_supir_ids = (
            distinct_penugasan_supir_ids | distinct_laporan_supir_ids
        )
        total_ditugaskan = len(all_assigned_supir_ids)

        # Hitung supir unik yang sudah SELESAI OPERASIONAL penuh (pagi & siang selesai)
        # dan supir unik yang terlambat
        selesai_supir_ids = set()
        supir_telat_set = set()

        for supir_id in all_assigned_supir_ids:
            # Ambil seluruh laporan milik supir ini hari ini
            supir_reports = [
                r
                for r in data_laporan_hari_ini
                if _canonical_id(r.get("id_supir")) == supir_id
            ]
            if not supir_reports:
                continue

            pagi_selesai = any(
                (sesi.get("tipe_sesi") or "").upper() == "PAGI"
                and (
                    sesi.get("jam_tiba_kantor")
                    or sesi.get("km_tiba_kantor") is not None
                )
                for rep in supir_reports
                for sesi in (rep.get("trip_sessions") or [])
            )
            siang_selesai = any(
                (sesi.get("tipe_sesi") or "").upper() == "SIANG"
                and (
                    sesi.get("jam_tiba_kantor")
                    or sesi.get("km_tiba_kantor") is not None
                )
                for rep in supir_reports
                for sesi in (rep.get("trip_sessions") or [])
            )

            # Cek tipe_sesi supir ini dari penugasan hari ini
            supir_tasks = [
                p
                for p in penugasan_list
                if _canonical_id(p.get("id_supir")) == supir_id
            ]
            task_tipe = "SEMUA"
            if supir_tasks:
                task_tipe = (
                    str(supir_tasks[0].get("tipe_sesi") or "SEMUA")
                    .replace("'", "")
                    .strip()
                    .upper()
                )

            is_selesai = False
            if task_tipe == "PAGI":
                is_selesai = pagi_selesai
            elif task_tipe == "SIANG":
                is_selesai = siang_selesai
            elif task_tipe == "BATAL":
                is_selesai = True
            else:
                is_selesai = pagi_selesai and siang_selesai

            if is_selesai:
                selesai_supir_ids.add(supir_id)

            if any(
                sesi.get("status_waktu") == "TERLAMBAT"
                for rep in supir_reports
                for sesi in (rep.get("trip_sessions") or [])
            ):
                supir_telat_set.add(supir_id)

        # Box 2 (Sedang Beroperasi): Akun driver bertugas dikurangi akun driver yang sudah SELESAI
        sedang_beroperasi = max(0, total_ditugaskan - len(selesai_supir_ids))

        # Box 1 (Driver): Total Driver di DB dikurangi Driver yang sedang aktif beroperasi (driver selesai bertugas kembali ke pool)
        driver_siaga = max(0, total_supir - sedang_beroperasi)

        # Box 3 (Driver Terlambat): Dihitung per 1 akun driver unik
        total_supir_telat = len(supir_telat_set)

        return {
            "pesan": "Metrik dashboard ditarik.",
            "data": {
                "tanggal": tanggal_hari_ini,
                "total_supir_terdaftar": total_supir,
                "total_supir_siaga": driver_siaga,
                "total_supir_ditugaskan": total_ditugaskan,
                "total_supir_jalan": sedang_beroperasi,
                "total_supir_absen": driver_siaga,
                "total_supir_telat": total_supir_telat,
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal hitung metrik dashboard: {str(e)}",
        )


def get_operasional_hari_ini():
    """Mengambil laporan operasional dan seluruh sesi untuk HARI INI berbasis penugasan resmi."""
    try:
        tanggal_hari_ini = str(date.today())
        user_map = _get_user_lookup_map()

        # 1. Ambil seluruh penugasan resmi hari ini
        penugasan_res = (
            supabase.table("penugasan")
            .select("*")
            .eq("tanggal", tanggal_hari_ini)
            .order("created_at", desc=False)
            .execute()
        )
        penugasan_list = penugasan_res.data or []

        # 2. Ambil seluruh laporan perjalanan hari ini beserta trip_sessions
        response = (
            supabase.table("daily_reports")
            .select("*, trip_sessions(*)")
            .eq("tanggal", tanggal_hari_ini)
            .order("created_at", desc=True)
            .execute()
        )
        reports_list = response.data or []

        # 3. Gabungkan penugasan dengan laporan yang cocok
        operasional_list = []
        matched_report_ids = set()

        for task in penugasan_list:
            id_supir = task.get("id_supir")
            trayek = task.get("trayek")
            bus = task.get("nopol_kendaraan")
            supir = user_map.get(id_supir, {})

            # Cari laporan yang cocok (berdasarkan supir & rute/nopol)
            matching_rep = next(
                (
                    r
                    for r in reports_list
                    if (
                        r.get("id_supir") == id_supir
                        or r.get("id_supir") == supir.get("email")
                    )
                    and r.get("trayek") == trayek
                    and r.get("bus") == bus
                ),
                None,
            )
            if not matching_rep:
                matching_rep = next(
                    (
                        r
                        for r in reports_list
                        if (
                            r.get("id_supir") == id_supir
                            or r.get("id_supir") == supir.get("email")
                        )
                        and r.get("id") not in matched_report_ids
                    ),
                    None,
                )

            task_tipe = (
                str(task.get("tipe_sesi") or "SEMUA").replace("'", "").strip().upper()
            )
            if matching_rep:
                matched_report_ids.add(matching_rep.get("id"))
                item = {
                    **matching_rep,
                    "penugasan_id": task.get("id"),
                    "tipe_sesi": task_tipe,
                    "trayek": task.get("trayek") or matching_rep.get("trayek"),
                    "bus": task.get("nopol_kendaraan") or matching_rep.get("bus"),
                    "jenis_kendaraan": task.get("jenis_kendaraan"),
                    "kapasitas": task.get("kapasitas_penumpang"),
                    "foto_profil": supir.get("foto_profil") or None,
                    "users": {
                        "nama": supir.get("nama")
                        or matching_rep.get("id_supir")
                        or "-",
                        "email": supir.get("email", "-"),
                        "foto_profil": supir.get("foto_profil") or None,
                    },
                }
            else:
                # Driver ditugaskan tapi belum mengirim laporan
                item = {
                    "id": f"task_{task.get('id')}",
                    "penugasan_id": task.get("id"),
                    "tipe_sesi": task_tipe,
                    "id_supir": id_supir,
                    "tanggal": tanggal_hari_ini,
                    "trayek": trayek or "-",
                    "bus": bus or "-",
                    "jenis_kendaraan": task.get("jenis_kendaraan"),
                    "kapasitas": task.get("kapasitas_penumpang"),
                    "foto_profil": supir.get("foto_profil") or None,
                    "trip_sessions": [],
                    "users": {
                        "nama": supir.get("nama") or id_supir or "-",
                        "email": supir.get("email", "-"),
                        "foto_profil": supir.get("foto_profil") or None,
                    },
                }
            operasional_list.append(item)

        # Sertakan laporan hari ini yang tidak terikat di penugasan (jika ada)
        for r in reports_list:
            if r.get("id") not in matched_report_ids:
                supir = user_map.get(r.get("id_supir"), {})
                operasional_list.append(
                    {
                        **r,
                        "foto_profil": supir.get("foto_profil") or None,
                        "users": {
                            "nama": supir.get("nama") or r.get("id_supir") or "-",
                            "email": supir.get("email", "-"),
                            "foto_profil": supir.get("foto_profil") or None,
                        },
                    }
                )

        return {
            "pesan": "Data operasional hari ini ditarik.",
            "data": operasional_list,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


def get_rekap_operasional():
    """Mengambil seluruh data rekap harian lengkap beserta inspeksi dan sesi."""
    try:
        user_map = _get_user_lookup_map()
        response = (
            supabase.table("daily_reports")
            .select("*, inspections(*), trip_sessions(*)")
            .order("tanggal", desc=True)
            .execute()
        )
        laporan_list = response.data or []
        for lap in laporan_list:
            supir = user_map.get(lap.get("id_supir"), {})
            lap["users"] = {
                "id": supir.get("id") or lap.get("id_supir"),
                "nama": supir.get("nama") or lap.get("id_supir") or "-",
                "trayek": supir.get("trayek") or lap.get("trayek"),
                "bus": supir.get("bus") or lap.get("bus"),
                "email": supir.get("email", "-"),
                "foto_profil": supir.get("foto_profil") or None,
            }

        return {
            "pesan": "Rekapitulasi ditarik.",
            "total_data": len(laporan_list),
            "data": laporan_list,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
