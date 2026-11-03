"""UC02 – OTP giả lập, UC07 – xem điểm (SD01, D12, NFR-S4, NFR-S7).

- Mã 6 số sinh bằng `secrets`, chỉ lưu dạng băm, hết hạn 5 phút, tối đa 5 lần nhập sai / mã.
- Gửi lại sau 60 giây, tối đa 5 mã / giờ / SĐT.
- Response của bước gửi mã giống nhau cho SĐT mới và SĐT đã là thành viên (không lộ thông tin).
- Bản ghi `customers` chỉ được tạo sau khi OTP đúng.
"""
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.security import create_customer_token, hash_otp
from app.models import Customer, LoyaltyTransaction, Order, OtpRequest
from app.modules.customer.phone import mask_phone, normalize_phone
from app.modules.customer.schemas import CustomerMe, LoyaltyTxOut, OtpRequestOut, OtpVerifyOut
from app.modules.customer.sms import SmsSender

_OTP_LOCK = 8_202  # khóa advisory theo SĐT: 2 yêu cầu cùng lúc không vượt giới hạn gửi / thử


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _phone_or_error(raw: str) -> str:
    phone = normalize_phone(raw)
    if phone is None:
        raise AppError(422, "VALIDATION_ERROR", "Số điện thoại không hợp lệ (cần số di động Việt Nam 10 số)",
                       {"field": "phone"})
    return phone


def _lock_phone(db: Session, phone: str) -> None:
    db.execute(text("SELECT pg_advisory_xact_lock(:k, hashtext(:p))"), {"k": _OTP_LOCK, "p": phone})


def _seconds(delta: timedelta) -> int:
    return max(1, int(delta.total_seconds() + 0.999))


def request_otp(db: Session, raw_phone: str, sms: SmsSender) -> OtpRequestOut:
    s = get_settings()
    phone = _phone_or_error(raw_phone)
    _lock_phone(db, phone)
    now = _now()

    recent = db.scalars(
        select(OtpRequest.created_at).where(OtpRequest.phone == phone, OtpRequest.created_at > now - timedelta(hours=1))
        .order_by(OtpRequest.created_at)
    ).all()
    if recent:
        wait = recent[-1] + timedelta(seconds=s.otp_resend_seconds) - now
        if wait > timedelta(0):
            raise AppError(429, "OTP_RATE_LIMITED", f"Vui lòng đợi {_seconds(wait)} giây rồi gửi lại mã",
                           {"retry_after": _seconds(wait)})
    if len(recent) >= s.otp_max_per_hour:
        wait = recent[-s.otp_max_per_hour] + timedelta(hours=1) - now
        minutes = (_seconds(wait) + 59) // 60
        raise AppError(429, "OTP_RATE_LIMITED",
                       f"Bạn đã yêu cầu quá {s.otp_max_per_hour} mã trong 1 giờ, vui lòng thử lại sau {minutes} phút",
                       {"retry_after": _seconds(wait)})

    code = f"{secrets.randbelow(1_000_000):06d}"
    db.add(OtpRequest(phone=phone, code_hash=hash_otp(phone, code), created_at=now,
                      expires_at=now + timedelta(seconds=s.otp_ttl_seconds)))
    db.flush()
    sms.send_otp(phone, code)
    return OtpRequestOut(expires_in=s.otp_ttl_seconds, resend_after=s.otp_resend_seconds,
                         phone_masked=mask_phone(phone), demo_code=code if s.otp_demo_mode else None)


class VerifyFailure(Exception):
    """Sai mã: router phải commit (lưu số lần thử) rồi mới trả lỗi."""

    def __init__(self, error: AppError):
        super().__init__(error.message)
        self.error = error


def _invalid(reason: str, message: str, attempts_left: int = 0) -> AppError:
    return AppError(400, "OTP_INVALID", message, {"reason": reason, "attempts_left": attempts_left})


def verify_otp(db: Session, raw_phone: str, code: str) -> OtpVerifyOut:
    """Ném VerifyFailure khi sai mã (cần commit số lần thử), AppError cho các lỗi còn lại."""
    s = get_settings()
    phone = _phone_or_error(raw_phone)
    _lock_phone(db, phone)
    now = _now()

    otp = db.scalar(
        select(OtpRequest).where(OtpRequest.phone == phone)
        .order_by(OtpRequest.created_at.desc(), OtpRequest.id.desc()).limit(1).with_for_update()
    )
    if otp is None or otp.verified_at is not None:
        raise _invalid("NOT_FOUND", "Mã không đúng hoặc đã được dùng, vui lòng bấm \"Gửi lại mã\"")
    if otp.attempts >= s.otp_max_attempts:
        raise _invalid("LOCKED", f"Bạn đã nhập sai {s.otp_max_attempts} lần, mã đã bị hủy. Vui lòng yêu cầu mã mới")
    if now >= otp.expires_at:
        raise _invalid("EXPIRED", "Mã đã hết hạn, vui lòng bấm \"Gửi lại mã\"")
    if not hmac.compare_digest(otp.code_hash, hash_otp(phone, code)):
        otp.attempts += 1
        db.flush()
        left = s.otp_max_attempts - otp.attempts
        if left <= 0:
            err = _invalid("LOCKED", f"Bạn đã nhập sai {s.otp_max_attempts} lần, mã đã bị hủy. Vui lòng yêu cầu mã mới")
        else:
            err = _invalid("WRONG", f"Mã không đúng, bạn còn {left} lần thử", left)
        raise VerifyFailure(err)

    otp.verified_at = now
    db.execute(insert(Customer).values(phone=phone).on_conflict_do_nothing(index_elements=["phone"]))
    customer = db.scalar(select(Customer).where(Customer.phone == phone))
    customer.last_verified_at = now
    db.flush()
    token, exp = create_customer_token(customer.id)
    return OtpVerifyOut(customer_token=token, expires_at=exp, name=customer.name,
                        phone_masked=mask_phone(phone), loyalty_points=customer.loyalty_points)


def get_me(db: Session, customer: Customer) -> CustomerMe:
    s = get_settings()
    rows = db.execute(
        select(LoyaltyTransaction, Order.order_code).outerjoin(Order, Order.id == LoyaltyTransaction.order_id)
        .where(LoyaltyTransaction.customer_id == customer.id)
        .order_by(LoyaltyTransaction.created_at.desc(), LoyaltyTransaction.id.desc()).limit(5)
    ).all()
    return CustomerMe(
        name=customer.name, phone_masked=mask_phone(customer.phone), loyalty_points=customer.loyalty_points,
        point_value_vnd=s.point_value_vnd, points_value=customer.loyalty_points * s.point_value_vnd,
        recent_transactions=[
            LoyaltyTxOut(order_code=code, points=tx.points, type=tx.type, created_at=tx.created_at) for tx, code in rows
        ],
    )
