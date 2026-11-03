"""UC11 – Quản lý chi nhánh (A03), UC13 – Menu chi nhánh (W06), UC14 – Bàn & mã QR (A06).

Quyền (ma trận RBAC – III.1):
- Chi nhánh: ADMIN thêm/sửa; MANAGER chỉ xem chi nhánh mình.
- Menu chi nhánh, bàn & QR: ADMIN mọi chi nhánh; MANAGER chi nhánh mình.
"""
import io
import secrets
import unicodedata

import qrcode
from fastapi import APIRouter, BackgroundTasks, Depends, Response, status
from PIL import Image, ImageDraw, ImageFont
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.core.errors import AppError
from app.models import Branch, BranchMenuItem, Category, DiningTable, MenuItem, Staff
from app.modules.admin.common import ADMIN, ADMIN_MANAGER, duplicate, flush_unique, get_or_404, publish_menu_updated
from app.modules.admin.schemas import (
    BranchCreate, BranchMenuOut, BranchMenuPatch, BranchOut, BranchUpdate, TableIn, TableOut,
)
from app.modules.auth.deps import ensure_branch_access, require_roles

router = APIRouter(prefix="/api/staff", tags=["admin – chi nhánh"])

DUP_CODE = "Mã chi nhánh đã tồn tại"
DUP_TABLE = "Số bàn đã tồn tại trong chi nhánh"


def _branch(db: Session, branch_id: int, *, lock: bool = False) -> Branch:
    return get_or_404(db, Branch, branch_id, "BRANCH_NOT_FOUND", "Chi nhánh không tồn tại", lock=lock)


def _branch_out(db: Session, b: Branch) -> BranchOut:
    tables = db.scalar(select(func.count()).where(DiningTable.branch_id == b.id)) or 0
    staff = db.scalar(select(func.count()).where(Staff.branch_id == b.id, Staff.is_active.is_(True))) or 0
    return BranchOut(
        id=b.id, code=b.code, name=b.name, address=b.address, phone=b.phone,
        latitude=float(b.latitude) if b.latitude is not None else None,
        longitude=float(b.longitude) if b.longitude is not None else None,
        is_active=b.is_active, table_count=tables, staff_count=staff,
    )


# ---------- Chi nhánh ----------
@router.get("/branches", response_model=list[BranchOut])
def list_branches(staff: Staff = Depends(require_roles(*ADMIN_MANAGER)), db: Session = Depends(get_db)):
    q = select(Branch).order_by(Branch.id)
    if staff.role != "ADMIN":
        q = q.where(Branch.id == staff.branch_id)
    return [_branch_out(db, b) for b in db.scalars(q)]


@router.post("/branches", response_model=BranchOut, status_code=status.HTTP_201_CREATED)
def create_branch(body: BranchCreate, _: Staff = Depends(require_roles(*ADMIN)), db: Session = Depends(get_db)):
    if db.scalar(select(Branch.id).where(Branch.code == body.code)) is not None:
        raise duplicate("code", DUP_CODE)
    b = Branch(**body.model_dump())
    db.add(b)
    flush_unique(db, "code", DUP_CODE)
    db.commit()
    return _branch_out(db, b)


@router.put("/branches/{branch_id}", response_model=BranchOut)
def update_branch(branch_id: int, body: BranchUpdate, background: BackgroundTasks,
                  _: Staff = Depends(require_roles(*ADMIN)), db: Session = Depends(get_db)):
    """Mã chi nhánh không đổi được (là tiền tố mã đơn). Ngừng hoạt động: mã QR các bàn báo không hợp lệ (UC01-2a)."""
    b = _branch(db, branch_id)
    for k, v in body.model_dump().items():
        setattr(b, k, v)
    db.commit()
    publish_menu_updated(background, b.id, "BRANCH")
    return _branch_out(db, b)


# ---------- Menu chi nhánh ----------
def _menu_rows(db: Session, branch_id: int, item_id: int | None = None) -> list[BranchMenuOut]:
    q = (
        select(MenuItem, Category.name, BranchMenuItem)
        .join(Category, Category.id == MenuItem.category_id)
        .outerjoin(BranchMenuItem, (BranchMenuItem.menu_item_id == MenuItem.id)
                   & (BranchMenuItem.branch_id == branch_id))
        .where(MenuItem.is_deleted.is_(False), MenuItem.is_active.is_(True))
        .order_by(Category.sort_order, Category.id, MenuItem.name.collate("vi-VN-x-icu"))
    )
    if item_id is not None:
        q = q.where(MenuItem.id == item_id)
    return [
        BranchMenuOut(
            menu_item_id=m.id, name=m.name, category_id=m.category_id, category_name=cat,
            base_price=m.base_price,
            price_override=bm.price_override if bm else None,
            is_available=bm.is_available if bm else True,
            updated_at=bm.updated_at if bm else None,
        )
        for m, cat, bm in db.execute(q)
    ]


@router.get("/branches/{branch_id}/menu", response_model=list[BranchMenuOut])
def branch_menu(branch_id: int, staff: Staff = Depends(require_roles(*ADMIN_MANAGER)), db: Session = Depends(get_db)):
    ensure_branch_access(staff, branch_id)
    _branch(db, branch_id)
    return _menu_rows(db, branch_id)


@router.patch("/branches/{branch_id}/menu/{item_id}", response_model=BranchMenuOut)
def patch_branch_menu(branch_id: int, item_id: int, body: BranchMenuPatch, background: BackgroundTasks,
                      staff: Staff = Depends(require_roles(*ADMIN_MANAGER)), db: Session = Depends(get_db)):
    """SD05: UPSERT branch_menu_items (an toàn khi 2 người sửa cùng lúc), rồi MENU_UPDATED cho chi nhánh."""
    ensure_branch_access(staff, branch_id)
    _branch(db, branch_id)
    m = db.get(MenuItem, item_id)
    if m is None or m.is_deleted or not m.is_active:
        raise AppError(404, "MENU_ITEM_NOT_FOUND", "Món không tồn tại hoặc đã ngừng bán toàn chuỗi")
    stmt = insert(BranchMenuItem).values(
        branch_id=branch_id, menu_item_id=item_id, price_override=body.price_override,
        is_available=body.is_available, updated_at=func.now(),
    )
    db.execute(stmt.on_conflict_do_update(
        index_elements=[BranchMenuItem.branch_id, BranchMenuItem.menu_item_id],
        set_={"price_override": stmt.excluded.price_override, "is_available": stmt.excluded.is_available,
              "updated_at": func.now()},
    ))
    db.commit()
    db.expire_all()
    publish_menu_updated(background, branch_id, "BRANCH_MENU")
    return _menu_rows(db, branch_id, item_id)[0]


# ---------- Bàn & mã QR ----------
def qr_url(token: str) -> str:
    return f"{get_settings().public_base_url.rstrip('/')}/t/{token}"


def _table_out(t: DiningTable) -> TableOut:
    return TableOut(id=t.id, branch_id=t.branch_id, table_number=t.table_number, qr_token=t.qr_token,
                    qr_url=qr_url(t.qr_token), is_active=t.is_active)


def _check_table_number(db: Session, branch_id: int, number: str, exclude_id: int | None = None) -> None:
    q = select(DiningTable.id).where(DiningTable.branch_id == branch_id, DiningTable.table_number == number)
    if exclude_id is not None:
        q = q.where(DiningTable.id != exclude_id)
    if db.scalar(q) is not None:
        raise duplicate("table_number", DUP_TABLE)


@router.get("/branches/{branch_id}/tables", response_model=list[TableOut])
def list_tables(branch_id: int, staff: Staff = Depends(require_roles(*ADMIN_MANAGER)), db: Session = Depends(get_db)):
    ensure_branch_access(staff, branch_id)
    _branch(db, branch_id)
    rows = db.scalars(
        select(DiningTable).where(DiningTable.branch_id == branch_id)
        .order_by(func.length(DiningTable.table_number), DiningTable.table_number)
    )
    return [_table_out(t) for t in rows]


@router.post("/branches/{branch_id}/tables", response_model=TableOut, status_code=status.HTTP_201_CREATED)
def create_table(branch_id: int, body: TableIn, staff: Staff = Depends(require_roles(*ADMIN_MANAGER)),
                 db: Session = Depends(get_db)):
    ensure_branch_access(staff, branch_id)
    _branch(db, branch_id)
    _check_table_number(db, branch_id, body.table_number)
    # NFR-S3: qr_token ngẫu nhiên 128 bit, không dùng ID bàn trên URL công khai
    t = DiningTable(branch_id=branch_id, table_number=body.table_number, is_active=body.is_active,
                    qr_token=secrets.token_urlsafe(16))
    db.add(t)
    flush_unique(db, "table_number", DUP_TABLE)
    db.commit()
    return _table_out(t)


def _table(db: Session, staff: Staff, table_id: int, branch_id: int | None = None) -> DiningTable:
    t = db.get(DiningTable, table_id)
    if t is None or (branch_id is not None and t.branch_id != branch_id):
        raise AppError(404, "TABLE_NOT_FOUND", "Bàn không tồn tại")
    ensure_branch_access(staff, t.branch_id)
    return t


@router.put("/branches/{branch_id}/tables/{table_id}", response_model=TableOut)
def update_table(branch_id: int, table_id: int, body: TableIn, staff: Staff = Depends(require_roles(*ADMIN_MANAGER)),
                 db: Session = Depends(get_db)):
    """Đổi số bàn giữ nguyên mã QR (không phải in lại). Khóa bàn: quét QR báo không hợp lệ (UC01-2a)."""
    ensure_branch_access(staff, branch_id)
    t = _table(db, staff, table_id, branch_id)
    _check_table_number(db, branch_id, body.table_number, exclude_id=t.id)
    t.table_number, t.is_active = body.table_number, body.is_active
    flush_unique(db, "table_number", DUP_TABLE)
    db.commit()
    return _table_out(t)


# Phông có dấu tiếng Việt cho dòng chữ dưới mã QR. Phông mặc định của Pillow không có chữ "à, ư, ơ, đ…"
# nên "Bàn" hiện thành "B□n" (BUG-F6-01). Image Docker cài fonts-dejavu-core (Dockerfile).
LABEL_FONTS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",   # Docker (Debian)
    "C:/Windows/Fonts/arialbd.ttf",                           # máy dev Windows
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",      # macOS
]


def label_font(size: int = 40):
    """Phông TrueType đầu tiên có trên máy; None nếu không có phông nào."""
    for path in LABEL_FONTS:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return None


def ascii_fold(s: str) -> str:
    """Bỏ dấu tiếng Việt ("Bàn" → "Ban"): dùng khi máy không có phông tiếng Việt, vẫn đọc được thay vì ô vuông."""
    s = s.replace("đ", "d").replace("Đ", "D").replace("·", "-")
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def render_qr_png(url: str, label: str) -> bytes:
    """Ảnh QR để in: mã QR + dòng chữ "CG · Bàn 05" bên dưới (tránh dán nhầm bàn)."""
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    code = qr.make_image(fill_color="black", back_color="white").get_image().convert("RGB")
    w, h = code.size
    canvas = Image.new("RGB", (w, h + 70), "white")
    canvas.paste(code, (0, 0))
    draw = ImageDraw.Draw(canvas)
    font = label_font()
    if font is None:
        font, label = ImageFont.load_default(size=40), ascii_fold(label)
    tw = draw.textlength(label, font=font)
    draw.text(((w - tw) / 2, h - 10), label, fill="black", font=font)
    buf = io.BytesIO()
    canvas.save(buf, format="PNG")
    return buf.getvalue()


@router.get("/tables/{table_id}/qr.png", response_class=Response)
def table_qr(table_id: int, staff: Staff = Depends(require_roles(*ADMIN_MANAGER)), db: Session = Depends(get_db)):
    t = _table(db, staff, table_id)
    b = db.get(Branch, t.branch_id)
    png = render_qr_png(qr_url(t.qr_token), f"{b.code} · Bàn {t.table_number}")
    filename = f"QR_{b.code}_Ban_{t.table_number}.png"
    return Response(png, media_type="image/png", headers={"Content-Disposition": f'attachment; filename="{filename}"'})
