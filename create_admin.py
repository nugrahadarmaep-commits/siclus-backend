"""
SICLUS CLI Management Tool: Admin Account Provisioning
"""

import sys
import getpass
import argparse
import re
from typing import Optional, Tuple
from email_validator import validate_email, EmailNotValidError

from app.core.security import get_password_hash
from app.db.database import supabase


def generate_next_admin_id() -> str:
    """
    Menghasilkan ID Admin secara otomatis dengan format ADMxxx (misal: ADM001 -> ADM002).
    Mencegah human error saat menentukan ID manual.
    """
    try:
        res = (
            supabase.table("users")
            .select("id")
            .ilike("id", "ADM%")
            .order("id", desc=True)
            .limit(20)
            .execute()
        )

        max_num = 0
        if res.data:
            for row in res.data:
                match = re.match(r"^ADM(\d+)$", str(row.get("id", "")).strip().upper())
                if match:
                    val = int(match.group(1))
                    if val > max_num:
                        max_num = val

        next_id = f"ADM{max_num + 1:03d}"
        return next_id
    except Exception:
        return "ADM001"


def validate_input(email: str, password: str) -> Tuple[bool, str]:
    """Validasi ketat input email dan kompleksitas password."""
    # 1. Validasi RFC Email
    try:
        valid = validate_email(email, check_deliverability=False)
        email_clean = valid.normalized
    except EmailNotValidError as e:
        return False, f"Format email tidak valid: {str(e)}"

    # 2. Validasi Kekuatan Password
    if len(password) < 8:
        return False, "Password minimal 8 karakter demi standar keamanan production."
    if not any(char.isdigit() for char in password):
        return False, "Password harus mengandung minimal 1 angka."
    if not any(char.isalpha() for char in password):
        return False, "Password harus mengandung minimal 1 huruf."

    return True, email_clean


def check_existing_user(admin_id: str, email: str) -> Tuple[bool, Optional[str]]:
    """Cek keunikan akun di database Supabase."""
    try:
        res = (
            supabase.table("users")
            .select("id, email")
            .or_(f"id.eq.{admin_id},email.eq.{email}")
            .execute()
        )
        if res.data:
            for user in res.data:
                if user.get("id") == admin_id:
                    return True, f"ID Admin '{admin_id}' sudah digunakan."
                if user.get("email") == email:
                    return True, f"Email '{email}' sudah terdaftar pada user lain."
        return False, None
    except Exception as e:
        return True, f"Gagal menghubungi server database: {str(e)}"


def prompt_user_data(args: argparse.Namespace) -> Tuple[str, str, str, str]:
    """Mengumpulkan dan memvalidasi data user baik dari argumen CLI atau interaktif."""
    # Handle ID
    default_id = generate_next_admin_id()
    if args.id:
        admin_id = args.id.strip().upper()
    else:
        id_input = input(f"ID Admin [{default_id}]: ").strip().upper()
        admin_id = id_input if id_input else default_id

    # Handle Nama
    nama = args.nama.strip() if args.nama else input("Nama Lengkap Admin: ").strip()
    while not nama:
        print("[!] Nama tidak boleh kosong.")
        nama = input("Nama Lengkap Admin: ").strip()

    # Handle Email
    email_raw = args.email.strip() if args.email else input("Alamat Email: ").strip()
    while True:
        is_valid, res = validate_input(email_raw, "dummyPassword123")
        if is_valid:
            email = res
            break
        print(f"[!] {res}")
        email_raw = input("Alamat Email: ").strip()

    # Handle Password (Masked)
    if args.password:
        password = args.password
        is_valid, msg = validate_input(email, password)
        if not is_valid:
            print(f"[X] {msg}")
            sys.exit(1)
    else:
        while True:
            password = getpass.getpass("Password Baru (min. 8 karakter, huruf & angka): ").strip()
            is_valid, msg = validate_input(email, password)
            if not is_valid:
                print(f"[!] {msg}")
                continue

            confirm = getpass.getpass("Konfirmasi Password: ").strip()
            if password != confirm:
                print("[!] Konfirmasi password tidak cocok. Silakan ulangi.")
                continue
            break

    return admin_id, nama, email, password


def create_admin():
    parser = argparse.ArgumentParser(
        description="SICLUS Backend CLI - Registrasi Akun Administrator",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--id", help="ID Akun Admin kustom (opsional, auto-generated jika kosong)")
    parser.add_argument("--nama", help="Nama Lengkap Admin")
    parser.add_argument("--email", help="Email Akun Admin")
    parser.add_argument("--password", help="Password Admin (opsional, gunakan mode interaktif jika ingin aman)")

    args = parser.parse_args()

    print("\n" + "=" * 55)
    print("      SICLUS OPERATIONAL SYSTEM - PROVISI ADMIN      ")
    print("=" * 55)

    try:
        admin_id, nama, email, password = prompt_user_data(args)

        print("\n[*] Memvalidasi status duplikasi di Supabase...")
        exists, err_msg = check_existing_user(admin_id, email)
        if exists:
            print(f"[X] Gagal: {err_msg}")
            sys.exit(1)

        print("[*] Melakukan enkripsi password (Bcrypt)...")
        hashed_password = get_password_hash(password)

        payload = {
            "id": admin_id,
            "nama": nama,
            "email": email,
            "password": hashed_password,
            "role": "admin",
            "trayek": None,
            "bus": None,
            "foto_profil": None,
        }

        print("[*] Menyimpan record admin ke tabel 'users'...")
        res = supabase.table("users").insert(payload).execute()

        if res.data:
            print("\n" + "-" * 55)
            print(" [V] SUKSES: Akun Administrator Berhasil Dibuat!")
            print("-" * 55)
            print(f" ID Akun    : {admin_id}")
            print(f" Nama       : {nama}")
            print(f" Email      : {email}")
            print(f" Role       : admin")
            print(" Status     : Aktif & Terotentikasi")
            print("-" * 55)
            print(" Akun ini sekarang dapat langsung login ke Dashboard Admin.\n")
        else:
            print("[X] Terjadi kesalahan: Data tidak berhasil disimpan.")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n[!] Proses dibatalkan oleh pengguna (Ctrl+C).")
        sys.exit(0)
    except Exception as e:
        print(f"\n[X] Fatal Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    create_admin()

