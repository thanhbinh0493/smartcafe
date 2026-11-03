"""Xác thực customer token (JWT role CUSTOMER, 1 giờ – D18, NFR-S2)."""
import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.errors import AppError
from app.core.security import decode_token
from app.models import Customer

bearer = HTTPBearer(auto_error=False)


def _customer_from(token: str, db: Session) -> Customer:
    try:
        payload = decode_token(token)
    except jwt.ExpiredSignatureError:
        raise AppError(401, "TOKEN_EXPIRED", "Phiên thành viên đã hết hạn, vui lòng nhập lại số điện thoại")
    except jwt.InvalidTokenError:
        raise AppError(401, "UNAUTHORIZED", "Phiên thành viên không hợp lệ")
    if payload.get("typ") != "customer":
        raise AppError(401, "UNAUTHORIZED", "Phiên thành viên không hợp lệ")
    customer = db.get(Customer, int(payload["sub"]))
    if customer is None:
        raise AppError(401, "UNAUTHORIZED", "Phiên thành viên không hợp lệ")
    return customer


def get_current_customer(
    cred: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db),
) -> Customer:
    if cred is None:
        raise AppError(401, "UNAUTHORIZED", "Vui lòng nhập số điện thoại để xem điểm")
    return _customer_from(cred.credentials, db)


def get_optional_customer(
    cred: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db),
) -> Customer | None:
    """Không có token: khách ẩn danh. Có token mà sai / hết hạn: 401 để client biết phiên đã hết
    (không âm thầm đặt đơn ẩn danh làm khách mất điểm)."""
    return None if cred is None else _customer_from(cred.credentials, db)
