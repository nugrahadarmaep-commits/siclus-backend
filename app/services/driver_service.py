from typing import Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from app.db.database import supabase

WIB = timezone(timedelta(hours=7))


# service: driver lifecycle & multi-assignment resolution
def is_report_completed(report: Dict[str, Any], task_tipe_sesi: str = "SEMUA") -> bool:
    """Memeriksa apakah laporan harian sudah menyelesaikan sesi yang ditugaskan."""
    if not report:
        return False
    sessions = report.get("trip_sessions") or []
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

    clean_tipe = str(task_tipe_sesi or "SEMUA").replace("'", "").strip().upper()
    if clean_tipe == "PAGI":
        return has_pagi
    elif clean_tipe == "SIANG":
        return has_siang
    elif clean_tipe == "BATAL":
        return True
    return has_pagi and has_siang


def get_driver_active_penugasan(
    email_supir: str, tanggal: Optional[str] = None
) -> Dict[str, Any]:
    """
    Mencari penugasan aktif pengemudi hari ini:
    1. Ambil seluruh penugasan pengemudi pada tanggal terkait.
    2. Cocokkan dengan status penyelesaian laporan (daily_reports + trip_sessions).
    3. Pilih penugasan pertama yang belum tuntas.
    4. Jika semua penugasan hari ini sudah tuntas, kembalikan penugasan terakhir.
    """
    if not tanggal:
        tanggal = datetime.now(WIB).strftime("%Y-%m-%d")

    # cari data user pengemudi
    user_res = (
        supabase.table("users")
        .select("id, email, nama")
        .eq("email", email_supir)
        .execute()
    )
    if not user_res.data:
        return {"active": None, "list": [], "id_supir": None, "email_supir": email_supir}

    id_supir = user_res.data[0]["id"]

    # ambil seluruh penugasan pengemudi pada tanggal terkait
    penugasan_res = (
        supabase.table("penugasan")
        .select("*")
        .eq("id_supir", id_supir)
        .eq("tanggal", tanggal)
        .execute()
    )
    penugasan_list = penugasan_res.data or []

    if not penugasan_list:
        return {"active": None, "list": [], "id_supir": id_supir, "email_supir": email_supir}

    # ambil seluruh laporan pengemudi pada tanggal terkait
    reports_res = (
        supabase.table("daily_reports")
        .select("*, trip_sessions(*), inspections(*)")
        .or_(f"id_supir.eq.{email_supir},id_supir.eq.{id_supir}")
        .eq("tanggal", tanggal)
        .execute()
    )
    all_reports = reports_res.data or []

    # cari penugasan yang belum tuntas
    active_task = None
    for task in penugasan_list:
        trayek = task.get("trayek")
        bus = task.get("nopol_kendaraan")

        matching_reports = [
            r for r in all_reports
            if (r.get("trayek") == trayek and r.get("bus") == bus)
        ]

        if not matching_reports:
            active_task = task
            break

        task_tipe = task.get("tipe_sesi") or "SEMUA"
        incomplete_report = next((r for r in matching_reports if not is_report_completed(r, task_tipe)), None)
        if incomplete_report is not None:
            active_task = task
            break

    # jika semua penugasan tuntas, gunakan penugasan terakhir
    if not active_task:
        active_task = penugasan_list[-1]

    return {
        "active": active_task,
        "list": penugasan_list,
        "id_supir": id_supir,
        "email_supir": email_supir,
    }


def get_driver_active_report(
    email_supir: str,
    tanggal: Optional[str] = None,
    trayek: Optional[str] = None,
    bus: Optional[str] = None,
    laporan_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Mengambil laporan harian spesifik atau laporan untuk penugasan aktif saat ini."""
    if not tanggal:
        tanggal = datetime.now(WIB).strftime("%Y-%m-%d")

    # jika ID laporan spesifik diminta
    if laporan_id:
        res = (
            supabase.table("daily_reports")
            .select("*, trip_sessions(*), inspections(*)")
            .eq("id", laporan_id)
            .execute()
        )
        if res.data and len(res.data) > 0:
            rep = res.data[0]
            try:
                pen_q = supabase.table("penugasan").select("*").eq("tanggal", rep.get("tanggal")).execute()
                if pen_q.data:
                    p = next(
                        (x for x in pen_q.data if x.get("trayek") == rep.get("trayek") or x.get("nopol_kendaraan") == rep.get("bus")),
                        pen_q.data[0]
                    )
                    rep["jenis_kendaraan"] = p.get("jenis_kendaraan")
                    rep["kapasitas_penumpang"] = p.get("kapasitas_penumpang")
                    rep["kapasitas"] = p.get("kapasitas_penumpang")
                    rep["penugasan"] = p
            except Exception:
                pass
            return rep
        return None

    # cari id_supir
    user_res = (
        supabase.table("users")
        .select("id")
        .eq("email", email_supir)
        .execute()
    )
    id_supir = user_res.data[0]["id"] if user_res.data else None

    # jika trayek dan bus tidak diberikan, cari berdasarkan penugasan aktif
    if not trayek or not bus:
        penugasan_info = get_driver_active_penugasan(email_supir, tanggal)
        active_task = penugasan_info.get("active")
        if not active_task:
            return None
        trayek = active_task.get("trayek")
        bus = active_task.get("nopol_kendaraan")
    else:
        active_task = None

    # query laporan berdasarkan supir, tanggal, trayek, dan bus
    query = (
        supabase.table("daily_reports")
        .select("*, trip_sessions(*), inspections(*)")
        .or_(f"id_supir.eq.{email_supir},id_supir.eq.{id_supir}")
        .eq("tanggal", tanggal)
    )
    if trayek:
        query = query.eq("trayek", trayek)
    if bus:
        query = query.eq("bus", bus)

    res = query.order("created_at", desc=True).execute()
    reports = res.data or []

    if not reports:
        return None

    selected_rep = None
    # prioritas 1: laporan yang sedang aktif berjalan
    for rep in reports:
        sessions = rep.get("trip_sessions") or []
        if sessions and not is_report_completed(rep):
            selected_rep = rep
            break

    # prioritas 2: laporan yang sudah tuntas penuh
    if not selected_rep:
        for rep in reports:
            if is_report_completed(rep):
                selected_rep = rep
                break

    # prioritas 3: fallback laporan teratas
    if not selected_rep:
        selected_rep = reports[0]

    if selected_rep and active_task:
        selected_rep["jenis_kendaraan"] = active_task.get("jenis_kendaraan")
        selected_rep["kapasitas_penumpang"] = active_task.get("kapasitas_penumpang")
        selected_rep["kapasitas"] = active_task.get("kapasitas_penumpang")
        selected_rep["penugasan"] = active_task

    return selected_rep
