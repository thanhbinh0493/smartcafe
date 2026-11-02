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


def decode_token(token: str) -> dict:
    """Trả payload; ném jwt.InvalidTokenError nếu sai chữ ký hoặc hết hạn."""
    s = get_settings()
    return jwt.decode(token, s.jwt_secret, algorithms=[s.jwt_algorithm])
