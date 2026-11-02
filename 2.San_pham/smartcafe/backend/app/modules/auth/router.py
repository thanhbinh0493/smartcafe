from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.core.errors import AppError
from app.core.security import create_staff_token, verify_password
from app.models import Staff
from app.modules.auth.deps import get_current_staff
from app.modules.auth.schemas import BranchBrief, LoginRequest, LoginResponse, StaffMe

router = APIRouter(prefix="/api/auth", tags=["auth"])


def to_me(staff: Staff) -> StaffMe:
    branch = None
    if staff.branch is not None:
        branch = BranchBrief(id=staff.branch.id, code=staff.branch.code, name=staff.branch.name)
    return StaffMe(id=staff.id, username=staff.username, full_name=staff.full_name, role=staff.role, branch=branch)


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    staff = db.scalar(select(Staff).where(Staff.username == body.username))
    # Cùng một thông báo cho sai tên đăng nhập / sai mật khẩu để không lộ tài khoản tồn tại
    if staff is None or not verify_password(body.password, staff.password_hash):
        raise AppError(401, "INVALID_CREDENTIALS", "Tên đăng nhập hoặc mật khẩu không đúng")
    if not staff.is_active:
        raise AppError(403, "ACCOUNT_LOCKED", "Tài khoản đã bị khóa, vui lòng liên hệ quản lý")
    token = create_staff_token(staff.id, staff.role, staff.branch_id)
    return LoginResponse(
        access_token=token,
        expires_in=get_settings().staff_token_hours * 3600,
        staff=to_me(staff),
    )


@router.get("/me", response_model=StaffMe)
def me(staff: Staff = Depends(get_current_staff)) -> StaffMe:
    return to_me(staff)
