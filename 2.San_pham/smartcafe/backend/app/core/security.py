import hashlib
import hmac
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import get_settings

BCRYPT_ROUNDS = 12  # NFR-S1: cost >= 10


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(BCRYPT_ROUNDS)).decode()


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except ValueError:
        return False


def create_staff_token(staff_id: int, role: str, branch_id: int | None) -> str:
    s = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(staff_id),
        "typ": "staff",
        "role": role,
        "branch_id": branch_id,
        "iat": now,
        "exp": now + timedelta(hours=s.staff_token_hours),
    }
    return jwt.encode(payload, s.jwt_secret, algorithm=s.jwt_algorithm)


def create_customer_token(customer_id: int) -> tuple[str, datetime]:
    """JWT khách thành viên (role CUSTOMER, 1 giờ – D18). Trả (token, thời điểm hết hạn)."""
    s = get_settings()
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=s.customer_token_minutes)
    payload = {"sub": str(customer_id), "typ": "customer", "role": "CUSTOMER", "iat": now, "exp": exp}
    return jwt.encode(payload, s.jwt_secret, algorithm=s.jwt_algorithm), exp


def hash_otp(phone: str, code: str) -> str:
    """Băm mã OTP (NFR-S4) bằng HMAC-SHA256, khóa = JWT_SECRET, gắn với SĐT."""
    key = get_settings().jwt_secret.encode()
    return hmac.new(key, f"{phone}:{code}".encode(), hashlib.sha256).hexdigest()


def decode_token(token: str) -> dict:
    """Trả payload; ném jwt.InvalidTokenError nếu sai chữ ký hoặc hết hạn."""
    s = get_settings()
    return jwt.decode(token, s.jwt_secret, algorithms=[s.jwt_algorithm])
