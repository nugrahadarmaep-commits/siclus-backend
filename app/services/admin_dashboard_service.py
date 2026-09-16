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

        # Hitung total armada driver terdaftar
        users_res = (
            supabase.table("users")
            .select("id")
            .in_("role", ["pengemudi", "driver", "DRIVER", "Driver"])
            .execute()
        )
        total_supir = len(users_res.data or [])

        # Hitung laporan yang masuk hari ini
        reports_res = (
            supabase.table("daily_reports")
            .select("id, id_supir, trip_sessions(status_waktu)")
            .eq("tanggal", tanggal_hari_ini)
            .execute()
        )
        data_laporan_hari_ini = reports_res.data or []

        total_jalan = len(data_laporan_hari_ini)
        total_absen = max(0, total_supir - total_jalan)

        total_telat = 0
        for laporan in data_laporan_hari_ini:
            sesi_list = laporan.get("trip_sessions", [])
            for sesi in sesi_list:
                if sesi.get("status_waktu") == "TERLAMBAT":
                    total_telat += 1
                    break

        return {
            "pesan": "Metrik dashboard ditarik.",
            "data": {
                "tanggal": tanggal_hari_ini,
                "total_supir_terdaftar": total_supir,
                "total_supir_jalan": total_jalan,
                "total_supir_absen": total_absen,
                "total_supir_telat": total_telat,
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal hitung metrik dashboard: {str(e)}",
        )

def get_operasional_hari_ini():
    """Mengambil laporan operasional dan seluruh sesi untuk HARI INI."""
    try:
        tanggal_hari_ini = str(date.today())
        user_map = _get_user_lookup_map()
        
        # Select all columns from trip_sessions so frontend has all timestamps
        response = (
            supabase.table("daily_reports")
            .select("*, trip_sessions(*)")
            .eq("tanggal", tanggal_hari_ini)
            .order("created_at", desc=True)
            .execute()
        )

        laporan_list = response.data or []
        for laporan in laporan_list:
            supir = user_map.get(laporan.get("id_supir"), {})
            laporan["users"] = {
                "nama": supir.get("nama") or laporan.get("id_supir") or "-",
                "email": supir.get("email", "-"),
                "foto_profil": supir.get("foto_profil") or None,
            }

        return {
            "pesan": "Data operasional hari ini ditarik.",
            "data": laporan_list
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
