from datetime import datetime, timezone
from typing import Optional
from fastapi import HTTPException, status
from app.db.database import supabase
from app.schemas.penugasan import PenugasanCreate, PenugasanUpdate
from app.services.admin_dashboard_service import _get_user_lookup_map


def _sync_schedule(trayek: str, tipe_sesi: str, jadwal: Optional[dict]):
    """Sinkronisasi jadwal operasional ke tabel schedules."""
    if not jadwal or not trayek:
        return

    form = str(jadwal.get("jam_formulir_pengisian") or "").strip()[:5]
    keluar = str(jadwal.get("batas_keluar_dishub") or "").strip()[:5]
    kembali = str(jadwal.get("batas_kembali_dishub") or "").strip()[:5]
    val_keluar = f"{form}|{keluar}" if form else keluar

    try:
        cek = (
            supabase.table("schedules")
            .select("id")
            .ilike("trayek", trayek)
            .eq("tipe_sesi", tipe_sesi)
            .execute()
        )
        payload = {
            "batas_keluar_dishub": val_keluar,
            "batas_tiba_start": kembali,
        }
        if cek.data:
            supabase.table("schedules").update(payload).eq("id", cek.data[0]["id"]).execute()
        else:
            supabase.table("schedules").insert({
                "trayek": trayek,
                "tipe_sesi": tipe_sesi,
                **payload,
            }).execute()
    except Exception as err:
        print(f"Warning sync schedule {tipe_sesi}:", err)


def get_semua_penugasan():
    """Mengambil daftar penugasan harian beserta jadwal operasional auto-expire."""
    try:
        user_map = _get_user_lookup_map()
        hari_ini = datetime.now().strftime("%Y-%m-%d")

        try:
            supabase.table("penugasan").delete().lt("tanggal", hari_ini).execute()
        except Exception as e_clean:
            print("Auto-clean penugasan lama warning:", e_clean)

        response = (
            supabase.table("penugasan")
            .select("*")
            .gte("tanggal", hari_ini)
            .order("tanggal", desc=True)
            .execute()
        )
        penugasan_list = response.data or []

        # Ambil schedules untuk lookup jadwal per trayek
        try:
            sched_res = supabase.table("schedules").select("*").execute()
            sched_list = sched_res.data or []
        except Exception:
            sched_list = []

        sched_map = {}
        for s in sched_list:
            t = (s.get("trayek") or "").strip().lower()
            sesi = (s.get("tipe_sesi") or "").strip().upper()
            raw_keluar = str(s.get("batas_keluar_dishub") or "")
            kembali = str(s.get("batas_tiba_start") or "")[:5]

            if "|" in raw_keluar:
                parts = raw_keluar.split("|", 1)
                buka_formulir = parts[0][:5]
                keluar = parts[1][:5]
            else:
                buka_formulir = raw_keluar[:5]
                keluar = raw_keluar[:5]

            s_parsed = {
                **s,
                "jam_formulir_pengisian": buka_formulir,
                "batas_keluar_dishub": keluar,
                "batas_kembali_dishub": kembali,
                "batas_tiba_start": kembali,
            }

            if t not in sched_map:
                sched_map[t] = {}
            sched_map[t][sesi] = s_parsed

        # Ambil laporan hari ini untuk mengecek status operasional
        try:
            today_reports_res = (
                supabase.table("daily_reports")
                .select("id, id_supir, trayek, bus, trip_sessions(*)")
                .eq("tanggal", hari_ini)
                .execute()
            )
            today_reports = today_reports_res.data or []
        except Exception:
            today_reports = []

        for p in penugasan_list:
            supir = user_map.get(p.get("id_supir"), {})
            foto_supir = supir.get("foto_profil") or None
            p["foto_profil"] = foto_supir
            p["users"] = {
                "nama": supir.get("nama") or p.get("id_supir") or "-",
                "email": supir.get("email", "-"),
                "foto_profil": foto_supir,
            }
            trayek_key = (p.get("trayek") or "").strip().lower()
            t_sched = sched_map.get(trayek_key, {})
            p["jadwal_pagi"] = t_sched.get(
                "PAGI",
                {
                    "jam_formulir_pengisian": "",
                    "batas_keluar_dishub": "",
                    "batas_kembali_dishub": "",
                    "batas_tiba_start": "",
                },
            )
            p["jadwal_siang"] = t_sched.get(
                "SIANG",
                {
                    "jam_formulir_pengisian": "",
                    "batas_keluar_dishub": "",
                    "batas_kembali_dishub": "",
                    "batas_tiba_start": "",
                },
            )

            # Hitung status operasional penugasan (MENUNGGU, BERJALAN, SELESAI)
            matching_rep = next(
                (
                    r for r in today_reports
                    if (r.get("id_supir") == p.get("id_supir") or r.get("id_supir") == supir.get("email"))
                    and (r.get("trayek") == p.get("trayek") and r.get("bus") == p.get("nopol_kendaraan"))
                ),
                None,
            )

            tipe_clean = str(p.get("tipe_sesi") or "SEMUA").replace("'", "").strip().upper()
            if tipe_clean not in ["PAGI", "SIANG", "SEMUA", "BATAL"]:
                tipe_clean = "SEMUA"
            p["tipe_sesi"] = tipe_clean

            status_operasional = "MENUNGGU"
            if tipe_clean == "BATAL":
                status_operasional = "BATAL"
            elif matching_rep:
                sessions = matching_rep.get("trip_sessions", [])
                pagi_done = any(
                    (s.get("tipe_sesi") or "").upper() == "PAGI"
                    and (s.get("jam_tiba_kantor") or s.get("km_tiba_kantor") is not None)
                    for s in sessions
                )
                siang_done = any(
                    (s.get("tipe_sesi") or "").upper() == "SIANG"
                    and (s.get("jam_tiba_kantor") or s.get("km_tiba_kantor") is not None)
                    for s in sessions
                )
                sudah_berangkat = any(bool(s.get("jam_berangkat_kantor")) for s in sessions)

                if tipe_clean == "PAGI":
                    is_selesai = pagi_done
                elif tipe_clean == "SIANG":
                    is_selesai = siang_done
                else:
                    is_selesai = pagi_done and siang_done

                if is_selesai:
                    status_operasional = "SELESAI"
                elif sudah_berangkat:
                    status_operasional = "BERJALAN"
                else:
                    status_operasional = "MENUNGGU"

            p["status_operasional"] = status_operasional

        return {
            "pesan": "Daftar penugasan ditarik.",
            "total": len(penugasan_list),
            "data": penugasan_list,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


def create_penugasan_harian(data: PenugasanCreate):
    """Admin membuat penugasan kendaraan dan jadwal cut-off untuk supir pada hari tertentu."""
    try:
        user = supabase.table("users").select("id").eq("id", data.id_supir).execute()
        if not user.data:
            raise HTTPException(status_code=404, detail="Supir tidak ditemukan.")

        nopol_clean = (data.nopol_kendaraan or "").strip().upper()
        jenis_clean = (data.jenis_kendaraan or "").strip().upper()
        trayek_clean = (data.trayek or "").strip().upper()
        kapasitas_clean = min(60, max(1, int(data.kapasitas_penumpang or 0))) if data.kapasitas_penumpang else 0

        tipe_clean = str(data.tipe_sesi or "SEMUA").replace("'", "").strip().upper()
        if tipe_clean not in ["PAGI", "SIANG", "SEMUA"]:
            tipe_clean = "SEMUA"

        res = (
            supabase.table("penugasan")
            .insert(
                {
                    "id_supir": data.id_supir,
                    "tanggal": str(data.tanggal),
                    "nopol_kendaraan": nopol_clean,
                    "jenis_kendaraan": jenis_clean,
                    "kapasitas_penumpang": kapasitas_clean,
                    "trayek": trayek_clean,
                    "tipe_sesi": tipe_clean,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            .execute()
        )

        # Sinkronisasi jadwal operasional sesi pagi dan siang
        _sync_schedule(data.trayek, "PAGI", data.jadwal_pagi)
        _sync_schedule(data.trayek, "SIANG", data.jadwal_siang)

        return {"pesan": "Penugasan dibuat.", "data": res.data[0]}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


def update_penugasan_harian(id_penugasan: str, data: PenugasanUpdate):
    """Admin memperbarui data penugasan kendaraan dan jadwal cut-off untuk supir."""
    try:
        cek = supabase.table("penugasan").select("*").eq("id", id_penugasan).execute()
        if not cek.data:
            raise HTTPException(
                status_code=404, detail="Data penugasan tidak ditemukan."
            )

        penugasan_item = cek.data[0]
        supir_id = penugasan_item.get("id_supir")
        tgl = penugasan_item.get("tanggal")
        target_trayek = penugasan_item.get("trayek")
        target_bus = penugasan_item.get("nopol_kendaraan")

        if supir_id and tgl:
            try:
                rep_query = (
                    supabase.table("daily_reports")
                    .select("id, trip_sessions(*)")
                    .eq("id_supir", supir_id)
                    .eq("tanggal", str(tgl))
                )
                if target_trayek:
                    rep_query = rep_query.eq("trayek", target_trayek)
                if target_bus:
                    rep_query = rep_query.eq("bus", target_bus)

                rep_check = rep_query.execute()
                for rep in rep_check.data or []:
                    sessions = rep.get("trip_sessions", [])
                    has_departed = any(bool(s.get("jam_berangkat_kantor")) for s in sessions)
                    if has_departed:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Penugasan tidak dapat diubah karena driver telah mengirim formulir keberangkatan operasional.",
                        )
            except HTTPException:
                raise
            except Exception as e_check:
                print("Warning check running session on update:", e_check)

        update_payload = {}
        if data.id_supir is not None:
            user = (
                supabase.table("users").select("id").eq("id", data.id_supir).execute()
            )
            if not user.data:
                raise HTTPException(status_code=404, detail="Supir tidak ditemukan.")
            update_payload["id_supir"] = data.id_supir

        if data.tanggal is not None:
            update_payload["tanggal"] = str(data.tanggal)
        if data.nopol_kendaraan is not None:
            update_payload["nopol_kendaraan"] = str(data.nopol_kendaraan).strip().upper()
        if data.jenis_kendaraan is not None:
            update_payload["jenis_kendaraan"] = str(data.jenis_kendaraan).strip().upper()
        if data.kapasitas_penumpang is not None:
            update_payload["kapasitas_penumpang"] = min(60, max(1, int(data.kapasitas_penumpang)))
        if data.trayek is not None:
            update_payload["trayek"] = str(data.trayek).strip().upper()
        if data.tipe_sesi is not None:
            tipe_clean = str(data.tipe_sesi).replace("'", "").strip().upper()
            if tipe_clean in ["PAGI", "SIANG", "SEMUA", "BATAL"]:
                update_payload["tipe_sesi"] = tipe_clean

        if update_payload:
            res = (
                supabase.table("penugasan")
                .update(update_payload)
                .eq("id", id_penugasan)
                .execute()
            )
        else:
            res = cek

        # Sinkronisasi jadwal operasional sesi pagi dan siang
        active_trayek = data.trayek or penugasan_item.get("trayek")
        _sync_schedule(active_trayek, "PAGI", data.jadwal_pagi)
        _sync_schedule(active_trayek, "SIANG", data.jadwal_siang)

        updated_record = (
            res.data[0] if (res.data and len(res.data) > 0) else cek.data[0]
        )
        return {"pesan": "Penugasan diperbarui.", "data": updated_record}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


def delete_penugasan_harian(id_penugasan: str):
    """Admin menghapus data penugasan kendaraan beserta cascade delete laporan terkait."""
    try:
        cek = supabase.table("penugasan").select("*").eq("id", id_penugasan).execute()
        if not cek.data:
            raise HTTPException(
                status_code=404, detail="Data penugasan tidak ditemukan."
            )

        penugasan_item = cek.data[0]
        id_supir = penugasan_item.get("id_supir")
        tanggal = penugasan_item.get("tanggal")
        target_trayek = penugasan_item.get("trayek")
        target_bus = penugasan_item.get("nopol_kendaraan")

        # Validasi: jika driver telah mengirim formulir keberangkatan, tolak penghapusan
        if id_supir and tanggal:
            try:
                rep_query = (
                    supabase.table("daily_reports")
                    .select("id, trip_sessions(*)")
                    .eq("id_supir", id_supir)
                    .eq("tanggal", str(tanggal))
                )
                if target_trayek:
                    rep_query = rep_query.eq("trayek", target_trayek)
                if target_bus:
                    rep_query = rep_query.eq("bus", target_bus)

                rep_check = rep_query.execute()
                for rep in rep_check.data or []:
                    sessions = rep.get("trip_sessions", [])
                    has_departed = any(bool(s.get("jam_berangkat_kantor")) for s in sessions)
                    if has_departed:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Penugasan tidak dapat dihapus karena driver telah memulai perjalanan operasional.",
                        )
            except HTTPException:
                raise
            except Exception as e_chk:
                print("Warning check running on delete:", e_chk)

        # Cascade cleanup: hapus daily_reports supir ini pada tanggal penugasan spesifik
        if id_supir and tanggal:
            try:
                user_email = id_supir
                user_res = (
                    supabase.table("users")
                    .select("email")
                    .eq("id", id_supir)
                    .execute()
                )
                if user_res.data:
                    user_email = user_res.data[0]["email"]

                rep_query = (
                    supabase.table("daily_reports")
                    .select("id")
                    .or_(f"id_supir.eq.{user_email},id_supir.eq.{id_supir}")
                    .eq("tanggal", str(tanggal))
                )
                if target_trayek:
                    rep_query = rep_query.eq("trayek", target_trayek)
                if target_bus:
                    rep_query = rep_query.eq("bus", target_bus)

                reports_res = rep_query.execute()
                reports = reports_res.data or []
                for rep in reports:
                    rep_id = rep.get("id")
                    if rep_id:
                        supabase.table("trip_sessions").delete().eq(
                            "laporan_id", rep_id
                        ).execute()
                        supabase.table("inspections").delete().eq(
                            "laporan_id", rep_id
                        ).execute()
                        supabase.table("daily_reports").delete().eq(
                            "id", rep_id
                        ).execute()
            except Exception as e_cascade:
                print("Warning cascade delete laporan:", e_cascade)

        supabase.table("penugasan").delete().eq("id", id_penugasan).execute()
        return {
            "pesan": "Penugasan dan laporan terkait berhasil dibersihkan.",
            "id": id_penugasan,
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


def batalkan_operasional_penugasan(id_penugasan: str, alasan: str = ""):
    """Admin membatalkan sisa operasional supir di tengah hari tanpa menghapus histori laporan dinas."""
    try:
        cek = supabase.table("penugasan").select("*").eq("id", id_penugasan).execute()
        if not cek.data:
            raise HTTPException(
                status_code=404, detail="Data penugasan tidak ditemukan."
            )

        penugasan_item = cek.data[0]
        id_supir = penugasan_item.get("id_supir")
        tanggal = penugasan_item.get("tanggal")
        target_trayek = penugasan_item.get("trayek")
        target_bus = penugasan_item.get("nopol_kendaraan")

        # Cek apakah supir sudah menyelesaikan pagi
        pagi_done = False
        if id_supir and tanggal:
            try:
                rep_query = (
                    supabase.table("daily_reports")
                    .select("id, trip_sessions(*)")
                    .eq("id_supir", id_supir)
                    .eq("tanggal", str(tanggal))
                )
                if target_trayek:
                    rep_query = rep_query.eq("trayek", target_trayek)
                if target_bus:
                    rep_query = rep_query.eq("bus", target_bus)

                rep_check = rep_query.execute()
                for rep in rep_check.data or []:
                    sessions = rep.get("trip_sessions", [])
                    if any(
                        (s.get("tipe_sesi") or "").upper() == "PAGI"
                        and (s.get("jam_tiba_kantor") or s.get("km_tiba_kantor") is not None)
                        for s in sessions
                    ):
                        pagi_done = True
                        break
            except Exception as e_chk:
                print("Warning check sessions on cancel:", e_chk)

        # Jika sudah selesai pagi, set tipe_sesi = PAGI agar terhitung SELESAI
        # Jika belum selesai pagi sama sekali, tandai BATAL
        new_tipe = "PAGI" if pagi_done else "BATAL"

        res = (
            supabase.table("penugasan")
            .update({"tipe_sesi": new_tipe})
            .eq("id", id_penugasan)
            .execute()
        )

        return {
            "pesan": f"Operasional berhasil dibatalkan. Status sesi diatur ke {new_tipe}.",
            "data": res.data[0] if res.data else cek.data[0],
            "tipe_sesi": new_tipe,
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
