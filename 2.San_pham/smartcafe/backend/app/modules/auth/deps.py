"""Phụ thuộc FastAPI cho xác thực JWT nhân viên và kiểm tra RBAC (NFR-S2, ma trận RBAC ở III.1)."""
from collections.abc import Callable

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.errors import AppError
from app.core.security import decode_token
from app.models import Staff

bearer = HTTPBearer(auto_error=False)


def get_current_staff(
    cred: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> Staff:
    if cred is None:
        raise AppError(401, "UNAUTHORIZED", "Vui lòng đăng nhập")
    try:
        payload = decode_token(cred.credentials)
    except jwt.ExpiredSignatureError:
        raise AppError(401, "TOKEN_EXPIRED", "Phiên đăng nhập đã hết hạn")
    except jwt.InvalidTokenError:
        raise AppError(401, "UNAUTHORIZED", "Token không hợp lệ")
    if payload.get("typ") != "staff":
        # Token khách thành viên không được gọi API nhân viên
        raise AppError(403, "FORBIDDEN", "Không có quyền truy cập")
    staff = db.get(Staff, int(payload["sub"]))
    if staff is None or not staff.is_active:
        raise AppError(401, "UNAUTHORIZED", "Tài khoản không tồn tại hoặc đã bị khóa")
    return staff


def require_roles(*roles: str) -> Callable[..., Staff]:
    def checker(staff: Staff = Depends(get_current_staff)) -> Staff:
        if staff.role not in roles:
            raise AppError(403, "FORBIDDEN", "Vai trò của bạn không được phép thực hiện thao tác này")
        return staff

    return checker


def ensure_branch_access(staff: Staff, branch_id: int) -> None:
    """ADMIN truy cập mọi chi nhánh; các vai trò khác chỉ chi nhánh của mình."""
    if staff.role != "ADMIN" and staff.branch_id != branch_id:
        raise AppError(403, "FORBIDDEN", "Bạn chỉ được thao tác trên chi nhánh của mình")
