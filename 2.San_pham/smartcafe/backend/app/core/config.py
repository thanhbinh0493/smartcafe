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
    # Quản trị (F6)
    public_base_url: str = "http://localhost:8080"  # địa chỉ khách mở khi quét QR (in vào ảnh QR – UC14)
    upload_dir: str = "uploads"                     # thư mục lưu ảnh món (phục vụ ở /api/uploads/...)
    max_image_bytes: int = 2 * 1024 * 1024          # ảnh món tối đa 2 MB
    # AI gợi ý món (F7 – II.2 Mục 2.3, 2.4; D35)
    weather_api_key: str = ""                       # OpenWeatherMap; để trống = nhiệt độ giả lập
    weather_mock_temp_c: float = 31.0               # nhiệt độ giả lập (đổi để demo trời nóng / lạnh)
    weather_cache_minutes: int = 30
    rec_popular_days: int = 7                       # "bán chạy" = số lượng bán 7 ngày tại chi nhánh
    rec_personal_half_life_days: int = 30           # đơn cũ 30 ngày nặng bằng nửa đơn hôm nay
    rules_window_days: int = 60                     # dữ liệu học luật kết hợp
    rules_min_support: float = 0.01
    rules_min_confidence: float = 0.2
    scheduler_enabled: bool = True                  # job học luật hằng đêm (tắt trong test)
    rules_job_hour: int = 0                         # 00:30 giờ VN (sau job báo cáo 00:05 của F8)
    rules_job_minute: int = 30
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:8080"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
