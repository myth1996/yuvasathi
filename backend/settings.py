from pydantic_settings import BaseSettings
import json
import os


class Settings(BaseSettings):
    free_limit: int = 2

    # CORS: set CORS_ORIGINS env var to your Vercel URL in production
    # e.g. "https://yuvasathi.vercel.app"
    # Accepts plain URL, comma-separated, or JSON array string
    cors_origins: str = "*"

    @property
    def cors_origins_list(self) -> list[str]:
        v = self.cors_origins.strip()
        if not v:
            return ["*"]
        if v.startswith("["):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return ["*"]
        return [u.strip() for u in v.split(",") if u.strip()]

    # JWT signing key — MUST be set via JWT_SECRET_KEY env var in production
    jwt_secret_key: str = os.environ.get(
        "JWT_SECRET_KEY",
        "a3a2d72161f366a5c1343b81a814234567890123456789012345678901234567",
    )
    jwt_algorithm: str = "HS256"

    # Redis — set REDIS_HOST env var to your Railway/Upstash Redis URL
    redis_host: str = os.environ.get("REDIS_HOST", "localhost")
    redis_port: int = int(os.environ.get("REDIS_PORT", "6379"))

    # Cashfree — MUST be set via env vars in production
    cashfree_app_id: str = os.environ.get("CASHFREE_APP_ID", "")
    cashfree_secret: str = os.environ.get("CASHFREE_SECRET", "")
    cashfree_url: str = os.environ.get(
        "CASHFREE_URL", "https://api.cashfree.com/pg"
    )

    class Config:
        env_file = ".env"


settings = Settings()
