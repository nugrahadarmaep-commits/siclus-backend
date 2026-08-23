import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# 2. Ambil alamat dan kunci rahasia dari dalem brankas
API_URL = os.getenv("SUPABASE_URL")
API_KEY = os.getenv("SUPABASE_KEY")

# 3. Validasi biar laptop lu ngasih tau kalo kuncinya lupa ditaruh
if not API_URL or not API_KEY:
    raise Exception("WEY KUNCINYA BELOM DIMASUKIN KE .ENV TUH!")

# 4. Bikin jembatan koneksinya!
supabase: Client = create_client(API_URL, API_KEY)
