import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

    SECRET_KEY: str = (
        os.getenv("SECRET_KEY")
        or os.getenv("JWT_SECRET_KEY")
        or "041c8201d962c84635bedd1131fa8c4452234f6039b40fac5ffc17c09941811c"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 12


settings = Settings()
