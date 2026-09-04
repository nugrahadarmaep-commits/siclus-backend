import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

    SECRET_KEY: str = os.getenv(
        "SECRET_KEY", "kunci-rahasia-siclus-dishub-mojokerto-2026"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 12


settings = Settings()
