from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://smartcafe:smartcafe@localhost:5432/smartcafe"
    jwt_secret: str = "change-me-please-0123456789abcdef"
    jwt_algorithm: str = "HS256"
    staff_token_hours: int = 8          # NFR-S2: 1 ca làm
    customer_token_minutes: int = 60    # D18: phiên thành viên 1 giờ
    new_item_days: int = 30             # D16: món mới = tạo trong 30 ngày
    seed_staff_password: str = "smartcafe123"
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:8080"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
