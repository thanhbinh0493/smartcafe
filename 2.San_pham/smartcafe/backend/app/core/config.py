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
    # OTP giả lập (D12, NFR-S4)
    otp_demo_mode: bool = True          # trả mã OTP trong response để hiện khung [DEMO] (W00a)
    otp_ttl_seconds: int = 300          # mã hết hạn sau 5 phút
    otp_resend_seconds: int = 60        # gửi lại sau 60 giây
    otp_max_per_hour: int = 5           # tối đa 5 mã / giờ / SĐT
    otp_max_attempts: int = 5           # tối đa 5 lần nhập sai / mã
    point_value_vnd: int = 100          # D15: 1 điểm = 100đ
    seed_staff_password: str = "smartcafe123"
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:8080"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
