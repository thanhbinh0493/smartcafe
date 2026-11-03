"""API khách thành viên: OTP giả lập (UC02) và xem điểm (UC07)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import Customer
from app.modules.customer import service
from app.modules.customer.deps import get_current_customer
from app.modules.customer.schemas import CustomerMe, OtpRequestIn, OtpRequestOut, OtpVerifyIn, OtpVerifyOut
from app.modules.customer.sms import SmsSender, get_sms_sender

router = APIRouter(prefix="/api/public", tags=["public"])


@router.post("/otp/request", response_model=OtpRequestOut)
def request_otp(body: OtpRequestIn, db: Session = Depends(get_db),
                sms: SmsSender = Depends(get_sms_sender)) -> OtpRequestOut:
    res = service.request_otp(db, body.phone, sms)
    db.commit()
    return res


@router.post("/otp/verify", response_model=OtpVerifyOut)
def verify_otp(body: OtpVerifyIn, db: Session = Depends(get_db)) -> OtpVerifyOut:
    try:
        res = service.verify_otp(db, body.phone, body.code)
    except service.VerifyFailure as f:
        db.commit()  # lưu số lần nhập sai trước khi trả lỗi
        raise f.error
    db.commit()
    return res


@router.get("/me", response_model=CustomerMe)
def me(customer: Customer = Depends(get_current_customer), db: Session = Depends(get_db)) -> CustomerMe:
    return service.get_me(db, customer)
