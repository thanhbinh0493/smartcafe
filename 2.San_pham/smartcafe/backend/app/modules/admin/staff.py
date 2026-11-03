"""UC12 – Quản lý nhân viên & phân quyền (A04).

Quyền (ma trận RBAC – III.1):
- ADMIN: mọi nhân viên, mọi vai trò.
- MANAGER: chỉ nhân viên chi nhánh mình, chỉ tạo / sửa Thu ngân và Pha chế (không tạo ADMIN / MANAGER).
Không ai tự khóa, tự đổi vai trò hay chi nhánh của chính mình (tránh mất quyền quản trị).
Khóa tài khoản có hiệu lực ngay: mọi API kiểm tra staff.is_active ở mỗi request (deps.get_current_staff).
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.errors import AppError
from app.core.security import hash_password
from app.models import Branch, Staff
from app.modules.admin.common import ADMIN_MANAGER, duplicate, flush_unique, get_or_404
from app.modules.admin.schemas import StaffCreate, StaffOut, StaffUpdate
from app.modules.auth.deps import require_roles

router = APIRouter(prefix="/api/staff", tags=["admin – nhân viên"])

DUP_USERNAME = "Tên đăng nhập đã được sử dụng"
MANAGER_ROLES = ("CASHIER", "BARISTA")


def _out(s: Staff) -> StaffOut:
    return StaffOut(
        id=s.id, username=s.username, full_name=s.full_name, role=s.role, branch_id=s.branch_id,
        branch_name=s.branch.name if s.branch else None, phone=s.phone, is_active=s.is_active,
        created_at=s.created_at,
    )


def _forbid(message: str) -> AppError:
    return AppError(403, "FORBIDDEN", message)


def _resolve_branch(db: Session, actor: Staff, role: str, branch_id: int | None) -> int | None:
    """Kiểm tra vai trò + chi nhánh của tài khoản sẽ lưu; trả branch_id hợp lệ."""
    if actor.role == "MANAGER":
        if role not in MANAGER_ROLES:
            raise _forbid("Quản lý chi nhánh chỉ được tạo / sửa tài khoản Thu ngân và Pha chế")
        if branch_id is None:
            branch_id = actor.branch_id
        if branch_id != actor.branch_id:
            raise _forbid("Bạn chỉ được quản lý nhân viên chi nhánh của mình")
    if role == "ADMIN":
        if branch_id is not None:
            raise AppError(422, "VALIDATION_ERROR", "Quản trị viên thuộc trụ sở, không gắn với chi nhánh",
                           {"field": "branch_id"})
        return None
    if branch_id is None:
        raise AppError(422, "VALIDATION_ERROR", "Vui lòng chọn chi nhánh cho nhân viên", {"field": "branch_id"})
    get_or_404(db, Branch, branch_id, "BRANCH_NOT_FOUND", "Chi nhánh không tồn tại")
    return branch_id


@router.get("/staff", response_model=list[StaffOut])
def list_staff(
    branch_id: int | None = None,
    role: str | None = Query(None, pattern="^(ADMIN|MANAGER|CASHIER|BARISTA)$"),
    actor: Staff = Depends(require_roles(*ADMIN_MANAGER)),
    db: Session = Depends(get_db),
):
    q = select(Staff)
    if actor.role == "MANAGER":
        q = q.where(Staff.branch_id == actor.branch_id)
    elif branch_id is not None:
        q = q.where(Staff.branch_id == branch_id)
    if role:
        q = q.where(Staff.role == role)
    q = q.order_by(Staff.branch_id.nulls_first(), Staff.role, Staff.username)
    return [_out(s) for s in db.scalars(q)]


@router.post("/staff", response_model=StaffOut, status_code=status.HTTP_201_CREATED)
def create_staff(body: StaffCreate, actor: Staff = Depends(require_roles(*ADMIN_MANAGER)),
                 db: Session = Depends(get_db)):
    branch_id = _resolve_branch(db, actor, body.role, body.branch_id)
    if db.scalar(select(Staff.id).where(func.lower(Staff.username) == body.username)) is not None:
        raise duplicate("username", DUP_USERNAME)
    s = Staff(username=body.username, full_name=body.full_name, phone=body.phone, role=body.role,
              branch_id=branch_id, is_active=body.is_active, password_hash=hash_password(body.password))
    db.add(s)
    flush_unique(db, "username", DUP_USERNAME)
    db.commit()
    return _out(s)


@router.put("/staff/{staff_id}", response_model=StaffOut)
def update_staff(staff_id: int, body: StaffUpdate, actor: Staff = Depends(require_roles(*ADMIN_MANAGER)),
                 db: Session = Depends(get_db)):
    s = get_or_404(db, Staff, staff_id, "STAFF_NOT_FOUND", "Nhân viên không tồn tại", lock=True)
    if actor.role == "MANAGER" and (s.branch_id != actor.branch_id or s.role not in MANAGER_ROLES):
        if s.id != actor.id:
            raise _forbid("Bạn chỉ được sửa tài khoản Thu ngân / Pha chế của chi nhánh mình")
    if s.id == actor.id:
        if body.role != s.role or body.branch_id != s.branch_id or not body.is_active:
            raise AppError(409, "CANNOT_MODIFY_SELF",
                           "Không thể tự khóa, tự đổi vai trò hoặc chi nhánh của chính mình")
        branch_id = s.branch_id
    else:
        branch_id = _resolve_branch(db, actor, body.role, body.branch_id)
    s.full_name, s.phone, s.role, s.branch_id, s.is_active = (
        body.full_name, body.phone, body.role, branch_id, body.is_active,
    )
    if body.password:
        s.password_hash = hash_password(body.password)
    db.commit()
    db.refresh(s)
    return _out(s)
