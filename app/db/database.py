import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

API_URL = os.getenv("SUPABASE_URL")
API_KEY = os.getenv("SUPABASE_KEY")

# testing jaga jaga takut kunci lupa di taruh mana!
if not API_URL or not API_KEY:
    raise Exception("token belum di taruh ke .env!")

# koneksi api
supabase: Client = create_client(API_URL, API_KEY)
