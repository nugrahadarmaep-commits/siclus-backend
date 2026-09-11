# ==============================================================================
# SERVICE: ADMINISTRATOR OPERATIONS
# ==============================================================================

from io import BytesIO
from typing import Optional
from datetime import date
import time
import pandas as pd
from fastapi import HTTPException, status, UploadFile
from fastapi.responses import StreamingResponse

from app.db.database import supabase
from app.core.security import get_password_hash
from app.schemas.user import UserRegister, UserUpdate, AdminProfileUpdate
from app.schemas.jadwal import JadwalCreate, JadwalUpdate
from app.schemas.penugasan import PenugasanCreate, PenugasanUpdate

# ==============================================================================
# DASHBOARD & STATISTIK OPERASIONAL
# ==============================================================================


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
        total_supir = len(users_res.data)

        # Hitung laporan yang masuk hari ini
        reports_res = (
            supabase.table("daily_reports")
            .select("id, id_supir, trip_sessions(status_waktu)")
            .eq("tanggal", tanggal_hari_ini)
            .execute()
        )
        data_laporan_hari_ini = reports_res.data

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


# ==============================================================================
# REKAPITULASI & LAPORAN OPERASIONAL
# ==============================================================================
def _get_user_lookup_map():
    """Mengambil peta profil supir untuk in-memory join aman tanpa ketergantungan Foreign Key."""
    try:
        res = (
            supabase.table("users")
            .select("id, nama, email, trayek, bus, role")
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
                "nama": supir.get("nama") or lap.get("id_supir") or "-",
                "trayek": supir.get("trayek") or lap.get("trayek"),
                "bus": supir.get("bus") or lap.get("bus"),
                "email": supir.get("email", "-"),
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


def get_riwayat_harian_grouped():
    """Mengambil riwayat laporan operasional yang dikelompokkan berdasarkan tanggal."""
    try:
        user_map = _get_user_lookup_map()
        response = (
            supabase.table("daily_reports")
            .select("*, trip_sessions(status_waktu, tipe_sesi)")
            .order("tanggal", desc=True)
            .execute()
        )

        grup_tanggal = {}
        for laporan in response.data or []:
            supir = user_map.get(laporan.get("id_supir"), {})
            laporan["users"] = {
                "nama": supir.get("nama") or laporan.get("id_supir") or "-",
                "email": supir.get("email", "-"),
            }
            tgl = laporan.get("tanggal")
            if tgl not in grup_tanggal:
                grup_tanggal[tgl] = []
            grup_tanggal[tgl].append(laporan)

        hasil_format = [
            {"tanggal": tgl, "laporan": isi} for tgl, isi in grup_tanggal.items()
        ]

        return {"pesan": "Riwayat harian ditarik.", "data": hasil_format}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


def export_rekap_to_excel(id_supir: Optional[str] = None):
    """Menghasilkan file Excel rekapan operasional harian untuk diunduh."""
    try:
        user_map = _get_user_lookup_map()
        query = supabase.table("daily_reports").select(
            "*, inspections(*), trip_sessions(*)"
        )

        if id_supir:
            query = query.eq("id_supir", id_supir)

        response = query.execute()
        data_laporan = response.data

        if not data_laporan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Data laporan kosong."
            )

        tabel_excel = []
        for baris in data_laporan:
            sesi_list = baris.get("trip_sessions", [])
            sesi = sesi_list[0] if sesi_list else {}
            supir = user_map.get(baris.get("id_supir"), {})
            nama_driver = supir.get("nama") or baris.get("id_supir") or "-"

            tabel_excel.append(
                {
                    "Tanggal Operasional": baris.get("tanggal"),
                    "Nama Driver": nama_driver,
                    "ID Driver": baris.get("id_supir"),
                    "Trayek": baris.get("trayek"),
                    "Armada Bus": baris.get("bus"),
                    "Tipe Sesi": sesi.get("tipe_sesi", "-"),
                    "Jam Keluar Dishub": sesi.get("jam_berangkat_kantor", "-"),
                    "Jam Tiba di Sekolah": sesi.get("jam_berangkat_start", "-"),
                    "Status Kedisiplinan": sesi.get("status_waktu", "-"),
                }
            )

        df = pd.DataFrame(tabel_excel)
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Rekap_Siclus")

        buffer.seek(0)
        nama_file = f"Rekap_{id_supir}.xlsx" if id_supir else "Rekap_Semua_Supir.xlsx"

        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={nama_file}"},
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal export Excel: {str(e)}",
        )


# ==============================================================================
# MANAJEMEN AKUN DRIVER (SUPIR)
# ==============================================================================
def get_all_drivers():
    """Mengambil daftar seluruh akun pengemudi/driver."""
    try:
        response = (
            supabase.table("users")
            .select("id, nama, email, trayek, bus, foto_profil")
            .in_("role", ["pengemudi", "driver", "DRIVER", "Driver"])
            .execute()
        )
        return {
            "pesan": "Daftar pengemudi ditarik.",
            "total": len(response.data),
            "data": response.data,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


def create_driver(data: UserRegister):
    """Menambahkan akun supir/driver baru oleh admin."""
    if not data.id.strip() or not data.email.strip() or not data.password.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Data tidak boleh kosong."
        )

    # Validasi keunikan ID dan Email
    if supabase.table("users").select("id").eq("id", data.id).execute().data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="ID sudah terdaftar."
        )
    if supabase.table("users").select("id").eq("email", data.email).execute().data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email sudah dipakai."
        )

    try:
        response = (
            supabase.table("users")
            .insert(
                {
                    "id": data.id,
                    "nama": data.nama_lengkap,
                    "email": data.email,
                    "password": get_password_hash(data.password),
                    "role": data.role,
                    "trayek": data.trayek,
                    "bus": data.bus,
                }
            )
            .execute()
        )
        user_terdaftar = response.data[0]
        user_terdaftar.pop("password", None)
        return {"pesan": "Akun dibuat.", "data": user_terdaftar}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


def update_driver(user_id: str, data: UserUpdate):
    """Memperbarui informasi akun supir/driver."""
    try:
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Tidak ada data diubah."
            )

        if "nama_lengkap" in update_data:
            update_data["nama"] = update_data.pop("nama_lengkap")

        if "password" in update_data:
            pw = str(update_data["password"]).strip()
            if pw:
                update_data["password"] = get_password_hash(pw)
            else:
                update_data.pop("password")

        response = (
            supabase.table("users").update(update_data).eq("id", user_id).execute()
        )
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Supir tidak ditemukan."
            )

        user_diperbarui = response.data[0]
        user_diperbarui.pop("password", None)
        return {"pesan": "Data diperbarui.", "data": user_diperbarui}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


def delete_driver(user_id: str):
    """Menghapus akun supir/driver dari sistem."""
    try:
        response = supabase.table("users").delete().eq("id", user_id).execute()
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Supir tidak ditemukan."
            )
        return {"pesan": f"Akun {user_id} dihapus."}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


# ==============================================================================
# MANAJEMEN JADWAL OPERASIONAL
# ==============================================================================
def get_all_schedules():
    """Mengambil daftar seluruh jadwal operasional."""
    try:
        response = supabase.table("schedules").select("*").order("trayek").execute()
        return {
            "pesan": "Jadwal ditarik.",
            "total": len(response.data),
            "data": response.data,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


def create_schedule(data: JadwalCreate):
    """Menambahkan jadwal rute baru."""
    try:
        response = (
            supabase.table("schedules")
            .insert(
                {
                    "trayek": data.trayek,
                    "tipe_sesi": data.tipe_sesi.upper(),
                    "jam_formulir_pengisian": data.jam_formulir_pengisian,
                    "batas_keluar_dishub": data.batas_keluar_dishub,
                    "batas_tiba_start": data.batas_tiba_start,
                }
            )
            .execute()
        )
        return {"pesan": "Jadwal ditambahkan.", "data": response.data[0]}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


def update_schedule(jadwal_id: str, data: JadwalUpdate):
    """Memperbarui jadwal rute operasional."""
    try:
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Tidak ada data diubah."
            )

        if "tipe_sesi" in update_data and update_data["tipe_sesi"]:
            update_data["tipe_sesi"] = update_data["tipe_sesi"].upper()

        response = (
            supabase.table("schedules")
            .update(update_data)
            .eq("id", jadwal_id)
            .execute()
        )
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Jadwal tidak ditemukan."
            )
        return {"pesan": "Jadwal diperbarui.", "data": response.data[0]}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


def delete_schedule(jadwal_id: str):
    """Menghapus jadwal operasional."""
    try:
        response = supabase.table("schedules").delete().eq("id", jadwal_id).execute()
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Jadwal tidak ditemukan."
            )
        return {"pesan": f"Jadwal {jadwal_id} berhasil dihapus."}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


# ==============================================================================
# PROFIL PRIBADI ADMIN
# ==============================================================================
def update_admin_profile(email_admin: str, data: AdminProfileUpdate):
    """Memperbarui informasi identitas profil admin (nama lengkap)."""
    try:
        nama_baru = data.nama_lengkap.strip()
        if not nama_baru:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nama lengkap tidak boleh kosong.",
            )

        res = (
            supabase.table("users")
            .update({"nama": nama_baru})
            .eq("email", email_admin)
            .execute()
        )
        if not res.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Akun admin tidak ditemukan.",
            )

        user_info = res.data[0]
        user_info.pop("password", None)
        return {
            "pesan": "Profil admin berhasil diperbarui.",
            "data": user_info,
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


async def update_admin_avatar(email_admin: str, foto: UploadFile):
    """Mengunggah dan memperbarui foto profil admin."""
    try:
        ekstensi = foto.filename.split(".")[-1].lower() if "." in foto.filename else ""
        if ekstensi not in ["jpg", "jpeg", "png", "webp"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Format tidak didukung. Gunakan JPG, JPEG, PNG, atau WEBP.",
            )

        isi_gambar = await foto.read()
        nama_prefix = email_admin.split("@")[0]
        nama_file_baru = f"admin_avatar_{nama_prefix}_{int(time.time())}.{ekstensi}"

        supabase.storage.from_("foto_profil").upload(
            file=isi_gambar,
            path=nama_file_baru,
            file_options={"content-type": foto.content_type},
        )

        url_publik = supabase.storage.from_("foto_profil").get_public_url(
            nama_file_baru
        )

        supabase.table("users").update({"foto_profil": url_publik}).eq(
            "email", email_admin
        ).execute()

        return {
            "pesan": "Foto profil admin berhasil diupdate",
            "foto_profil": url_publik,
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


# ==============================================================================
# MANAJEMEN PENUGASAN KENDARAAN (HARIAN)
# ==============================================================================
def get_semua_penugasan():
    """Mengambil daftar penugasan harian beserta jadwal operasionalnya (auto-expire penugasan hari sebelumnya)."""
    try:
        user_map = _get_user_lookup_map()
        import datetime
        hari_ini = datetime.datetime.now().strftime("%Y-%m-%d")

        # Auto-clean data penugasan yang sudah lewat hari (agar tidak menumpuk)
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

        # Cek apakah sudah ada penugasan di tanggal yang sama untuk supir ini
        cek = (
            supabase.table("penugasan")
            .select("id")
            .eq("id_supir", data.id_supir)
            .eq("tanggal", str(data.tanggal))
            .execute()
        )

        if cek.data:
            # Update jika sudah ada
            res = (
                supabase.table("penugasan")
                .update(
                    {
                        "nopol_kendaraan": data.nopol_kendaraan,
                        "jenis_kendaraan": data.jenis_kendaraan,
                        "kapasitas_penumpang": data.kapasitas_penumpang,
                        "trayek": data.trayek,
                    }
                )
                .eq("id", cek.data[0]["id"])
                .execute()
            )
            pesan = "Penugasan diperbarui."
        else:
            # Insert baru
            res = (
                supabase.table("penugasan")
                .insert(
                    {
                        "id_supir": data.id_supir,
                        "tanggal": str(data.tanggal),
                        "nopol_kendaraan": data.nopol_kendaraan,
                        "jenis_kendaraan": data.jenis_kendaraan,
                        "kapasitas_penumpang": data.kapasitas_penumpang,
                        "trayek": data.trayek,
                    }
                )
                .execute()
            )
            pesan = "Penugasan dibuat."

        # Sinkronisasi Jadwal Operasional Sesi Pagi jika disertakan
        if data.jadwal_pagi and data.trayek:
            form_pagi = str(data.jadwal_pagi.get("jam_formulir_pengisian") or "").strip()[:5]
            keluar_pagi = str(data.jadwal_pagi.get("batas_keluar_dishub") or "").strip()[:5]
            kembali_pagi = str(data.jadwal_pagi.get("batas_kembali_dishub") or "").strip()[:5]
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
            form_siang = str(data.jadwal_siang.get("jam_formulir_pengisian") or "").strip()[:5]
            keluar_siang = str(data.jadwal_siang.get("batas_keluar_dishub") or "").strip()[:5]
            kembali_siang = str(data.jadwal_siang.get("batas_kembali_dishub") or "").strip()[:5]
            val_keluar_siang = f"{form_siang}|{keluar_siang}" if form_siang else keluar_siang

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
            update_payload["nopol_kendaraan"] = data.nopol_kendaraan
        if data.jenis_kendaraan is not None:
            update_payload["jenis_kendaraan"] = data.jenis_kendaraan
        if data.kapasitas_penumpang is not None:
            update_payload["kapasitas_penumpang"] = data.kapasitas_penumpang
        if data.trayek is not None:
            update_payload["trayek"] = data.trayek

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
            form_pagi = str(data.jadwal_pagi.get("jam_formulir_pengisian") or "").strip()[:5]
            keluar_pagi = str(data.jadwal_pagi.get("batas_keluar_dishub") or "").strip()[:5]
            kembali_pagi = str(data.jadwal_pagi.get("batas_kembali_dishub") or "").strip()[:5]
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
            form_siang = str(data.jadwal_siang.get("jam_formulir_pengisian") or "").strip()[:5]
            keluar_siang = str(data.jadwal_siang.get("batas_keluar_dishub") or "").strip()[:5]
            kembali_siang = str(data.jadwal_siang.get("batas_kembali_dishub") or "").strip()[:5]
            val_keluar_siang = f"{form_siang}|{keluar_siang}" if form_siang else keluar_siang

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

        # Cascade Cleanup: Cari daily_reports supir ini pada tanggal penugasan
        if id_supir and tanggal:
            try:
                reports_res = (
                    supabase.table("daily_reports")
                    .select("id")
                    .eq("id_supir", id_supir)
                    .eq("tanggal", str(tanggal))
                    .execute()
                )
                reports = reports_res.data or []
                for rep in reports:
                    rep_id = rep.get("id")
                    if rep_id:
                        # 1. Hapus trip_sessions
                        supabase.table("trip_sessions").delete().eq("laporan_id", rep_id).execute()
                        # 2. Hapus inspections
                        supabase.table("inspections").delete().eq("laporan_id", rep_id).execute()
                        # 3. Hapus daily_reports
                        supabase.table("daily_reports").delete().eq("id", rep_id).execute()
            except Exception as e_cascade:
                print("Warning cascade delete laporan:", e_cascade)

        # Terakhir, hapus record penugasan
        supabase.table("penugasan").delete().eq("id", id_penugasan).execute()
        return {"pesan": "Penugasan dan laporan terkait berhasil dibersihkan.", "id": id_penugasan}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
