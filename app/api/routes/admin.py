from io import BytesIO
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import pandas as pd
from app.core.config import settings
from app.db.database import supabase
from datetime import date
from app.schemas.user import UserRegister, UserUpdate
from app.schemas.jadwal import JadwalCreate, JadwalUpdate
from app.core.security import get_password_hash

router = APIRouter()
security = HTTPBearer()


# ─── FUNGSI KEAMANAN: VERIFIKASI HAK AKSES ADMIN ──────────────────────
def verifikasi_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Fungsi otorisasi khusus (Role-Based Access Control) untuk Administrator.
    Memvalidasi keberadaan token sekaligus memastikan 'role' pengguna adalah 'admin'.
    """
    token = credentials.credentials
    try:
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


# ─── ENDPOINT: DASHBOARD ADMIN ────────────────────────────
@router.get("/dashboard")
def dashboard_admin(email_admin: str = Depends(verifikasi_admin)):
    """
    Menarik ringkasan data operasional harian secara umum.
    Menghitung: Total supir terdaftar, supir jalan (hadir), absen, dan telat HARI INI.
    """
    try:
        tanggal_hari_ini = str(date.today())

        # 1. Cari Total Supir Terdaftar di Sistem
        users_res = (
            supabase.table("users").select("id").eq("role", "pengemudi").execute()
        )
        total_supir = len(users_res.data)

        # 2. Cari Laporan Hari Ini beserta sesi perjalanannya
        # Ini buat tau siapa aja yang udah absen selfie/jalan hari ini
        reports_res = (
            supabase.table("daily_reports")
            .select("id, id_supir, trip_sessions(status_waktu)")
            .eq("tanggal", tanggal_hari_ini)
            .execute()
        )
        data_laporan_hari_ini = reports_res.data

        # 3. Hitung Matematika Dasarnya
        total_jalan = len(data_laporan_hari_ini)
        total_absen = total_supir - total_jalan
        if total_absen < 0:
            total_absen = 0  # Jaga-jaga biar kaga minus

        # 4. Hitung Berapa Supir yang Terlambat Hari Ini
        total_telat = 0
        for laporan in data_laporan_hari_ini:
            sesi_list = laporan.get("trip_sessions", [])
            for sesi in sesi_list:
                if sesi.get("status_waktu") == "TERLAMBAT":
                    total_telat += 1
                    break  # Cukup dihitung 1 kali per supir meskipun telat pagi dan siang

        return {
            "pesan": "Data metrik dashboard berhasil ditarik.",
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
            detail=f"Terjadi kesalahan saat menghitung metrik dashboard: {str(e)}",
        )


# ─── ENDPOINT: REKAPITULASI DATA (HALAMAN ADMIN) ──────────────────────
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


# ─── ENDPOINT: UNDUH LAPORAN EXCEL (.xlsx) ────────────────────────────
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


# ─── ENDPOINT: LIHAT SEMUA AKUN SUPIR (READ) ──────────────────────────
@router.get("/users")
def get_semua_supir(email_admin: str = Depends(verifikasi_admin)):
    """
    Menarik seluruh daftar pengguna yang memiliki role sebagai 'pengemudi'.
    """
    try:
        response = (
            supabase.table("users")
            .select("id, nama, email, trayek, bus, foto_profil")
            .eq("role", "pengemudi")
            .execute()
        )

        return {
            "pesan": "Daftar pengemudi berhasil ditarik.",
            "total": len(response.data),
            "data": response.data,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Terjadi kesalahan: {str(e)}")


# ─── ENDPOINT: TAMBAH AKUN SUPIR BARU (CREATE) ────────────────────────
@router.post("/users")
def tambah_supir_baru(data: UserRegister, email_admin: str = Depends(verifikasi_admin)):
    """
    Mendaftarkan akun pengemudi baru. Kata sandi akan dienkripsi (hashing)
    sebelum disimpan ke dalam database.
    """

    if (
        not data.id.strip()
        or not data.nama_lengkap.strip()
        or not data.email.strip()
        or not data.password.strip()
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Gagal. ID, Nama, Email, dan Password tidak boleh kosong atau hanya berisi spasi!",
        )

    cek_id = supabase.table("users").select("id").eq("id", data.id).execute()
    if cek_id.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Gagal. ID Pengemudi '{data.id}' sudah terdaftar di sistem.",
        )

    cek_email = supabase.table("users").select("id").eq("email", data.email).execute()
    if cek_email.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Gagal. Email '{data.email}' sudah terdaftar untuk pengguna lain.",
        )

    try:
        hashed_pw = get_password_hash(data.password)

        response = (
            supabase.table("users")
            .insert(
                {
                    "id": data.id,
                    "nama": data.nama_lengkap,
                    "email": data.email,
                    "password": hashed_pw,
                    "role": data.role,
                    "trayek": data.trayek,
                    "bus": data.bus,
                }
            )
            .execute()
        )

        user_terdaftar = response.data[0]
        user_terdaftar.pop("password", None)

        return {"pesan": "Akun pengemudi berhasil dibuat.", "data": user_terdaftar}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal menambah supir: {str(e)}")


# ─── ENDPOINT: EDIT DATA SUPIR (UPDATE) ───────────────────────────────
@router.put("/users/{user_id}")
def edit_data_supir(
    user_id: str, data: UserUpdate, email_admin: str = Depends(verifikasi_admin)
):
    """
    Memperbarui data penugasan atau profil pengemudi berdasarkan ID.
    """
    try:
        # Hanya ambil data yang diisi oleh Admin (tidak None)
        update_data = {}
        if data.nama_lengkap:
            update_data["nama"] = data.nama_lengkap
        if data.email:
            update_data["email"] = data.email
        if data.trayek:
            update_data["trayek"] = data.trayek
        if data.bus:
            update_data["bus"] = data.bus

        if not update_data:
            raise HTTPException(
                status_code=400, detail="Tidak ada data yang dikirim untuk diubah."
            )

        response = (
            supabase.table("users").update(update_data).eq("id", user_id).execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=404,
                detail=f"Pengemudi dengan ID {user_id} tidak ditemukan.",
            )

        return {
            "pesan": "Data pengemudi berhasil diperbarui.",
            "data": response.data[0],
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal memperbarui data: {str(e)}")


# ─── ENDPOINT: HAPUS AKUN SUPIR (DELETE) ──────────────────────────────
@router.delete("/users/{user_id}")
def hapus_supir(user_id: str, email_admin: str = Depends(verifikasi_admin)):
    """
    Menghapus akun pengemudi dari sistem secara permanen berdasarkan ID.
    """
    try:
        response = supabase.table("users").delete().eq("id", user_id).execute()

        if not response.data:
            raise HTTPException(
                status_code=404,
                detail=f"Pengemudi dengan ID {user_id} tidak ditemukan.",
            )

        return {
            "pesan": f"Akun pengemudi dengan ID {user_id} berhasil dihapus permanen."
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal menghapus supir: {str(e)}")


# ─── ENDPOINT: LIHAT SEMUA JADWAL (READ) ──────────────────────────────
@router.get("/jadwal")
def get_semua_jadwal(email_admin: str = Depends(verifikasi_admin)):
    """
    Menarik semua data batas waktu operasional (cut-off time) dari seluruh trayek.
    """
    try:
        response = supabase.table("schedules").select("*").order("trayek").execute()
        return {
            "pesan": "Daftar jadwal operasional berhasil ditarik.",
            "total": len(response.data),
            "data": response.data,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Terjadi kesalahan: {str(e)}")


# ─── ENDPOINT: BIKIN JADWAL BARU (CREATE) ─────────────────────────────
@router.post("/jadwal")
def tambah_jadwal_baru(
    data: JadwalCreate, email_admin: str = Depends(verifikasi_admin)
):
    """
    Menambahkan aturan batas waktu baru untuk sebuah trayek dan sesi tertentu.
    """
    try:
        response = (
            supabase.table("schedules")
            .insert(
                {
                    "trayek": data.trayek,
                    "tipe_sesi": data.tipe_sesi.upper(),
                    "batas_keluar_dishub": data.batas_keluar_dishub,
                    "batas_tiba_start": data.batas_tiba_start,
                }
            )
            .execute()
        )

        return {
            "pesan": "Jadwal operasional baru berhasil ditambahkan.",
            "data": response.data[0],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal menambah jadwal: {str(e)}")


# ─── ENDPOINT: EDIT JADWAL (UPDATE) ───────────────────────────────────
@router.put("/jadwal/{jadwal_id}")
def edit_jadwal(
    jadwal_id: int, data: JadwalUpdate, email_admin: str = Depends(verifikasi_admin)
):
    """
    Memperbarui batas waktu toleransi pada jadwal yang sudah ada berdasarkan ID.
    """
    try:
        update_data = {}
        if data.batas_keluar_dishub:
            update_data["batas_keluar_dishub"] = data.batas_keluar_dishub
        if data.batas_tiba_start:
            update_data["batas_tiba_start"] = data.batas_tiba_start

        if not update_data:
            raise HTTPException(
                status_code=400,
                detail="Tidak ada data waktu yang dikirim untuk diubah.",
            )

        response = (
            supabase.table("schedules")
            .update(update_data)
            .eq("id", jadwal_id)
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=404, detail=f"Jadwal dengan ID {jadwal_id} tidak ditemukan."
            )

        return {
            "pesan": "Batas waktu jadwal berhasil diperbarui.",
            "data": response.data[0],
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Gagal memperbarui jadwal: {str(e)}"
        )
