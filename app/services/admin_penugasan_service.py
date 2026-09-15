from datetime import datetime, timezone
from fastapi import HTTPException, status
from app.db.database import supabase
from app.schemas.penugasan import PenugasanCreate, PenugasanUpdate
from app.services.admin_dashboard_service import _get_user_lookup_map

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

        for p in penugasan_list:
            supir = user_map.get(p.get("id_supir"), {})
            p["users"] = {
                "nama": supir.get("nama") or p.get("id_supir") or "-",
                "email": supir.get("email", "-"),
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
        # Cek apakah supir ada
        user = supabase.table("users").select("id").eq("id", data.id_supir).execute()
        if not user.data:
            raise HTTPException(status_code=404, detail="Supir tidak ditemukan.")

        # penugasan baru sesuai dengan kemauan admin
        nopol_clean = (data.nopol_kendaraan or "").strip().upper()
        jenis_clean = (data.jenis_kendaraan or "").strip().upper()
        trayek_clean = (data.trayek or "").strip().upper()
        kapasitas_clean = min(60, max(1, int(data.kapasitas_penumpang or 0))) if data.kapasitas_penumpang else 0

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
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            .execute()
        )
        pesan = "Penugasan dibuat."

        # Sinkronisasi Jadwal Operasional Sesi Pagi jika disertakan
        if data.jadwal_pagi and data.trayek:
            form_pagi = str(
                data.jadwal_pagi.get("jam_formulir_pengisian") or ""
            ).strip()[:5]
            keluar_pagi = str(
                data.jadwal_pagi.get("batas_keluar_dishub") or ""
            ).strip()[:5]
            kembali_pagi = str(
                data.jadwal_pagi.get("batas_kembali_dishub") or ""
            ).strip()[:5]
            val_keluar_pagi = f"{form_pagi}|{keluar_pagi}" if form_pagi else keluar_pagi

            try:
                cek_pagi = (
                    supabase.table("schedules")
                    .select("id")
                    .ilike("trayek", data.trayek)
                    .eq("tipe_sesi", "PAGI")
                    .execute()
                )
                if cek_pagi.data:
                    supabase.table("schedules").update(
                        {
                            "batas_keluar_dishub": val_keluar_pagi,
                            "batas_tiba_start": kembali_pagi,
                        }
                    ).eq("id", cek_pagi.data[0]["id"]).execute()
                else:
                    supabase.table("schedules").insert(
                        {
                            "trayek": data.trayek,
                            "tipe_sesi": "PAGI",
                            "batas_keluar_dishub": val_keluar_pagi,
                            "batas_tiba_start": kembali_pagi,
                        }
                    ).execute()
            except Exception as e_pagi:
                print("Warning simpan jadwal pagi:", e_pagi)

        # Sinkronisasi Jadwal Operasional Sesi Siang jika disertakan
        if data.jadwal_siang and data.trayek:
            form_siang = str(
                data.jadwal_siang.get("jam_formulir_pengisian") or ""
            ).strip()[:5]
            keluar_siang = str(
                data.jadwal_siang.get("batas_keluar_dishub") or ""
            ).strip()[:5]
            kembali_siang = str(
                data.jadwal_siang.get("batas_kembali_dishub") or ""
            ).strip()[:5]
            val_keluar_siang = (
                f"{form_siang}|{keluar_siang}" if form_siang else keluar_siang
            )

            try:
                cek_siang = (
                    supabase.table("schedules")
                    .select("id")
                    .ilike("trayek", data.trayek)
                    .eq("tipe_sesi", "SIANG")
                    .execute()
                )
                if cek_siang.data:
                    supabase.table("schedules").update(
                        {
                            "batas_keluar_dishub": val_keluar_siang,
                            "batas_tiba_start": kembali_siang,
                        }
                    ).eq("id", cek_siang.data[0]["id"]).execute()
                else:
                    supabase.table("schedules").insert(
                        {
                            "trayek": data.trayek,
                            "tipe_sesi": "SIANG",
                            "batas_keluar_dishub": val_keluar_siang,
                            "batas_tiba_start": kembali_siang,
                        }
                    ).execute()
            except Exception as e_siang:
                print("Warning simpan jadwal siang:", e_siang)

        return {"pesan": pesan, "data": res.data[0]}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


def update_penugasan_harian(id_penugasan: str, data: PenugasanUpdate):
    """Admin memperbarui data penugasan kendaraan dan jadwal cut-off untuk supir."""
    try:
        # Cek apakah penugasan ada
        cek = supabase.table("penugasan").select("*").eq("id", id_penugasan).execute()
        if not cek.data:
            raise HTTPException(
                status_code=404, detail="Data penugasan tidak ditemukan."
            )

        update_payload = {}
        if data.id_supir is not None:
            # Cek apakah supir baru valid
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

        if update_payload:
            res = (
                supabase.table("penugasan")
                .update(update_payload)
                .eq("id", id_penugasan)
                .execute()
            )
        else:
            res = cek

        # Sinkronisasi Jadwal Operasional Sesi Pagi jika disertakan
        target_trayek = data.trayek or cek.data[0].get("trayek")
        if data.jadwal_pagi and target_trayek:
            form_pagi = str(
                data.jadwal_pagi.get("jam_formulir_pengisian") or ""
            ).strip()[:5]
            keluar_pagi = str(
                data.jadwal_pagi.get("batas_keluar_dishub") or ""
            ).strip()[:5]
            kembali_pagi = str(
                data.jadwal_pagi.get("batas_kembali_dishub") or ""
            ).strip()[:5]
            val_keluar_pagi = f"{form_pagi}|{keluar_pagi}" if form_pagi else keluar_pagi

            try:
                cek_pagi = (
                    supabase.table("schedules")
                    .select("id")
                    .ilike("trayek", target_trayek)
                    .eq("tipe_sesi", "PAGI")
                    .execute()
                )
                if cek_pagi.data:
                    supabase.table("schedules").update(
                        {
                            "batas_keluar_dishub": val_keluar_pagi,
                            "batas_tiba_start": kembali_pagi,
                        }
                    ).eq("id", cek_pagi.data[0]["id"]).execute()
                else:
                    supabase.table("schedules").insert(
                        {
                            "trayek": target_trayek,
                            "tipe_sesi": "PAGI",
                            "batas_keluar_dishub": val_keluar_pagi,
                            "batas_tiba_start": kembali_pagi,
                        }
                    ).execute()
            except Exception as e_pagi:
                print("Warning update jadwal pagi:", e_pagi)

        # Sinkronisasi Jadwal Operasional Sesi Siang jika disertakan
        if data.jadwal_siang and target_trayek:
            form_siang = str(
                data.jadwal_siang.get("jam_formulir_pengisian") or ""
            ).strip()[:5]
            keluar_siang = str(
                data.jadwal_siang.get("batas_keluar_dishub") or ""
            ).strip()[:5]
            kembali_siang = str(
                data.jadwal_siang.get("batas_kembali_dishub") or ""
            ).strip()[:5]
            val_keluar_siang = (
                f"{form_siang}|{keluar_siang}" if form_siang else keluar_siang
            )

            try:
                cek_siang = (
                    supabase.table("schedules")
                    .select("id")
                    .ilike("trayek", target_trayek)
                    .eq("tipe_sesi", "SIANG")
                    .execute()
                )
                if cek_siang.data:
                    supabase.table("schedules").update(
                        {
                            "batas_keluar_dishub": val_keluar_siang,
                            "batas_tiba_start": kembali_siang,
                        }
                    ).eq("id", cek_siang.data[0]["id"]).execute()
                else:
                    supabase.table("schedules").insert(
                        {
                            "trayek": target_trayek,
                            "tipe_sesi": "SIANG",
                            "batas_keluar_dishub": val_keluar_siang,
                            "batas_tiba_start": kembali_siang,
                        }
                    ).execute()
            except Exception as e_siang:
                print("Warning update jadwal siang:", e_siang)

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

        # Cascade Cleanup: Cari daily_reports supir ini pada tanggal penugasan spesifik untuk trayek dan armada ini
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
                        # 1. Hapus trip_sessions
                        supabase.table("trip_sessions").delete().eq(
                            "laporan_id", rep_id
                        ).execute()
                        # 2. Hapus inspections
                        supabase.table("inspections").delete().eq(
                            "laporan_id", rep_id
                        ).execute()
                        # 3. Hapus daily_reports
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
