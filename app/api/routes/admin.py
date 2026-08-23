from io import BytesIO
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import pandas as pd
from app.core.config import settings
from app.db.database import supabase

router = APIRouter()
security = HTTPBearer()


# ==========================================
# FUNGSI KEAMANAN: VERIFIKASI HAK AKSES ADMIN
# ==========================================
def verifikasi_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Fungsi otorisasi khusus (Role-Based Access Control) untuk Administrator.
    Memvalidasi keberadaan token sekaligus memastikan 'role' pengguna adalah 'admin'.
    """
    token = credentials.credentials
    try:
        # Dekode token JWT
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )

        email_user = payload.get("sub")
        role_user = payload.get("role")

        # Validasi Role: Jika bukan admin, tolak akses (403 Forbidden)
        if role_user != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Akses ditolak. Endpoint ini secara eksklusif hanya untuk Administrator.",
            )

        return email_user

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesi telah kedaluwarsa. Silakan login kembali.",
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token autentikasi tidak valid atau telah dimanipulasi.",
        )


# ==========================================
# ENDPOINT: DASHBOARD ADMIN (TESTING)
# ==========================================
@router.get("/dashboard")
def dashboard_admin(email_admin: str = Depends(verifikasi_admin)):
    """
    Endpoint uji coba untuk memastikan verifikasi Admin berjalan dengan baik.
    """
    return {"pesan": f"Selamat datang di Dasbor VIP, {email_admin}!"}


# ==========================================
# ENDPOINT: REKAPITULASI DATA (HALAMAN ADMIN)
# ==========================================
@router.get("/rekap")
def get_rekap_laporan(email_admin: str = Depends(verifikasi_admin)):
    """
    Menarik seluruh data laporan harian, termasuk detail inspeksi
    dan sesi perjalanan pengemudi. Data ini digunakan untuk
    ditampilkan pada tabel antarmuka dasbor Administrator.
    """
    try:
        # Menarik data laporan utama beserta relasinya (inspeksi dan sesi)
        # Tanda (*) di dalam kurung berarti menarik semua kolom dari tabel terkait
        response = (
            supabase.table("daily_reports")
            .select("*, inspections(*), trip_sessions(*)")
            .execute()
        )

        return {
            "pesan": "Data rekapitulasi berhasil ditarik.",
            "total_data": len(response.data),
            "data": response.data,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan teknis saat menarik data rekapitulasi: {str(e)}",
        )


# ==========================================
# ENDPOINT: UNDUH LAPORAN EXCEL (.xlsx)
# ==========================================
@router.get("/export-excel")
def export_rekap_excel(email_admin: str = Depends(verifikasi_admin)):
    """
    Mengonversi data laporan operasional menjadi format file Excel (.xlsx)
    yang siap diunduh oleh Administrator.
    """
    try:
        # 1. Menarik data laporan utama beserta relasinya
        response = (
            supabase.table("daily_reports")
            .select("*, inspections(*), trip_sessions(*)")
            .execute()
        )

        data_laporan = response.data

        if not data_laporan:
            raise HTTPException(status_code=404, detail="Data laporan masih kosong.")

        # 2. Menyiapkan kerangka data (struktur baris dan kolom) untuk Excel
        tabel_excel = []

        for baris in data_laporan:
            # Mengambil sesi perjalanan pertama untuk simplifikasi laporan
            sesi_list = baris.get("trip_sessions", [])
            sesi = sesi_list[0] if sesi_list else {}

            # Memetakan kolom sesuai kebutuhan instansi
            tabel_excel.append(
                {
                    "Tanggal Operasional": baris.get("tanggal"),
                    "ID Pengemudi": baris.get("id_supir"),
                    "Trayek": baris.get("trayek"),
                    "Armada Bus": baris.get("bus"),
                    "Tipe Sesi": sesi.get("tipe_sesi", "-"),
                    "Jam Keluar Dishub": sesi.get("jam_berangkat_kantor", "-"),
                    "Jam Tiba di Sekolah": sesi.get("jam_berangkat_start", "-"),
                    "Status Kedisiplinan": sesi.get("status_waktu", "-"),
                }
            )

        # 3. Mengonversi data kerangka menjadi DataFrame Pandas (Tabel Virtual)
        df = pd.DataFrame(tabel_excel)

        # 4. Membuat file Excel di dalam memori sistem (RAM) tanpa menyimpannya di hard disk
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Rekap_Laporan_Siclus")

        buffer.seek(0)  # Mengembalikan pointer memori ke awal file

        # 5. Mengirimkan file Excel sebagai bentuk unduhan (attachment)
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": "attachment; filename=Rekap_Laporan_Siclus.xlsx"
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan teknis saat membuat dokumen Excel: {str(e)}",
        )
