"""UC01 – Quét QR: xác định chi nhánh và bàn từ qr_token."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.errors import AppError
from app.models import Branch, DiningTable

router = APIRouter(prefix="/api/public", tags=["public"])


class BranchPublic(BaseModel):
    id: int
    code: str
    name: str
    address: str


class TablePublic(BaseModel):
    id: int
    table_number: str


class TableLookupResponse(BaseModel):
    branch: BranchPublic
    table: TablePublic


@router.get("/tables/{qr_token}", response_model=TableLookupResponse)
def lookup_table(qr_token: str, db: Session = Depends(get_db)) -> TableLookupResponse:
    row = db.execute(
        select(DiningTable, Branch)
        .join(Branch, Branch.id == DiningTable.branch_id)
        .where(DiningTable.qr_token == qr_token)
    ).first()
    # Ngoại lệ 2a (UC01): mã sai, bàn bị khóa hoặc chi nhánh ngừng hoạt động đều trả cùng một lỗi
    if row is None or not row.DiningTable.is_active or not row.Branch.is_active:
        raise AppError(404, "TABLE_NOT_FOUND", "Mã QR không hợp lệ, vui lòng gọi nhân viên")
    table, branch = row.DiningTable, row.Branch
    return TableLookupResponse(
        branch=BranchPublic(id=branch.id, code=branch.code, name=branch.name, address=branch.address),
        table=TablePublic(id=table.id, table_number=table.table_number),
    )
