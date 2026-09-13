# ==============================================================================
# SERVICE: DRIVER LIFECYCLE & MULTI-ASSIGNMENT RESOLUTION
# ==============================================================================

from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
from app.db.database import supabase

WIB = timezone(timedelta(hours=7))


def is_report_completed(report: Dict[str, Any]) -> bool:
    """Memeriksa apakah laporan harian sudah menyelesaikan sesi PAGI dan SIANG."""
    if not report:
        return False
    sessions = report.get("trip_sessions") or []
    has_pagi = any(
        (s.get("tipe_sesi") or "").upper() == "PAGI"
        and s.get("km_tiba_kantor") is not None
        for s in sessions
    )
    has_siang = any(
        (s.get("tipe_sesi") or "").upper() == "SIANG"
        and s.get("km_tiba_kantor") is not None
        for s in sessions
    )
    return has_pagi and has_siang


def get_driver_active_penugasan(
    email_supir: str, tanggal: Optional[str] = None
) -> Dict[str, Any]:
    """
    Mencari penugasan aktif pengemudi hari ini:
    1. Ambil seluruh penugasan pengemudi pada tanggal terkait.
    2. Cocokkan dengan status penyelesaian laporan (daily_reports + trip_sessions).
    3. Pilih penugasan pertama yang BELUM tuntas (baik belum ada laporan maupun sedang berjalan).
    4. Jika SEMUA penugasan hari ini sudah tuntas, kembalikan penugasan terakhir
       agar halaman pengemudi menampilkan status 'Operasional Selesai' untuk penugasan tersebut.
    """
    if not tanggal:
        tanggal = datetime.now(WIB).strftime("%Y-%m-%d")

    # 1. Cari data user pengemudi
    user_res = (
        supabase.table("users")
        .select("id, email, nama")
        .eq("email", email_supir)
        .execute()
    )
    if not user_res.data:
        return {"active": None, "list": [], "id_supir": None, "email_supir": email_supir}

    id_supir = user_res.data[0]["id"]

    # 2. Ambil seluruh penugasan pengemudi pada tanggal terkait
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

    # 3. Ambil seluruh laporan pengemudi pada tanggal terkait
    reports_res = (
        supabase.table("daily_reports")
        .select("*, trip_sessions(*), inspections(*)")
        .or_(f"id_supir.eq.{email_supir},id_supir.eq.{id_supir}")
        .eq("tanggal", tanggal)
        .execute()
    )
    all_reports = reports_res.data or []

    # 4. Cari penugasan yang belum tuntas
    active_task = None
    for task in penugasan_list:
        trayek = task.get("trayek")
        bus = task.get("nopol_kendaraan")

        matching_reports = [
            r for r in all_reports
            if (r.get("trayek") == trayek and r.get("bus") == bus)
        ]

        if not matching_reports:
            # Belum ada laporan untuk penugasan ini -> Jadikan penugasan aktif
            active_task = task
            break

        # Cek apakah ada laporan yang belum tuntas kedua sesi
        incomplete_report = next((r for r in matching_reports if not is_report_completed(r)), None)
        if incomplete_report is not None:
            active_task = task
            break

    # 5. Jika semua penugasan sudah tuntas, gunakan penugasan terakhir
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
    """
    Mengambil laporan harian spesifik atau laporan untuk penugasan aktif saat ini.
    """
    if not tanggal:
        tanggal = datetime.now(WIB).strftime("%Y-%m-%d")

    # Jika ID laporan spesifik diminta
    if laporan_id:
        res = (
            supabase.table("daily_reports")
            .select("*, trip_sessions(*), inspections(*)")
            .eq("id", laporan_id)
            .execute()
        )
        if res.data and len(res.data) > 0:
            return res.data[0]
        return None

    # Cari id_supir
    user_res = (
        supabase.table("users")
        .select("id")
        .eq("email", email_supir)
        .execute()
    )
    id_supir = user_res.data[0]["id"] if user_res.data else None

    # Jika trayek dan bus tidak diberikan, cari berdasarkan penugasan aktif
    if not trayek or not bus:
        penugasan_info = get_driver_active_penugasan(email_supir, tanggal)
        active_task = penugasan_info.get("active")
        if not active_task:
            return None
        trayek = active_task.get("trayek")
        bus = active_task.get("nopol_kendaraan")

    # Query laporan berdasarkan supir, tanggal, trayek, dan bus
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

    # Prioritaskan laporan yang belum tuntas
    for rep in reports:
        if not is_report_completed(rep):
            return rep

    return reports[0]
