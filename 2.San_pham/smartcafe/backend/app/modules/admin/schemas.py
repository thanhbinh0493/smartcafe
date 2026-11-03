"""Schema vào/ra của các API quản trị (F6). Chuỗi được bỏ khoảng trắng thừa trước khi kiểm tra độ dài."""
from datetime import datetime
from typing import Annotated, Literal

from pydantic import AfterValidator, AwareDatetime, BaseModel, BeforeValidator, Field, field_validator

from app.modules.admin.common import MAX_PRICE, clean


def _clean(v):
    return clean(v) if isinstance(v, str) else v


def _clean_opt(v):
    """Chuỗi tùy chọn: rỗng sau khi bỏ khoảng trắng = None."""
    if isinstance(v, str):
        v = clean(v)
        return v or None
    return v


Name50 = Annotated[str, BeforeValidator(_clean), Field(min_length=1, max_length=50)]
Name100 = Annotated[str, BeforeValidator(_clean), Field(min_length=1, max_length=100)]
OptText = Annotated[Annotated[str, Field(max_length=1000)] | None, BeforeValidator(_clean_opt)]
Opt255 = Annotated[Annotated[str, Field(max_length=255)] | None, BeforeValidator(_clean_opt)]
Phone = Annotated[Annotated[str, Field(pattern=r"^\+?[0-9 .()-]{8,15}$")] | None, BeforeValidator(_clean_opt)]
Price = Annotated[int, Field(ge=0, le=MAX_PRICE)]
TempType = Literal["HOT", "COLD", "BOTH", "NONE"]
Role = Literal["ADMIN", "MANAGER", "CASHIER", "BARISTA"]


# ---------- Danh mục (UC09 – A05) ----------
class CategoryIn(BaseModel):
    name: Name50
    sort_order: int = Field(0, ge=0, le=999)
    is_active: bool = True


class CategoryOut(BaseModel):
    id: int
    name: str
    sort_order: int
    is_active: bool
    item_count: int


# ---------- Món – menu chung (UC10 – W05) ----------
def _tags(v: list[str]) -> list[str]:
    out: list[str] = []
    for t in v:
        t = clean(t).lower()
        if not t:
            continue
        if len(t) > 30:
            raise ValueError("Mỗi thẻ tối đa 30 ký tự")
        if t not in out:
            out.append(t)
    if len(out) > 10:
        raise ValueError("Tối đa 10 thẻ")
    return out


class MenuItemIn(BaseModel):
    category_id: int
    name: Name100
    description: OptText = None
    base_price: Price
    temperature_type: TempType = "BOTH"
    tags: Annotated[list[str], AfterValidator(_tags)] = []
    is_active: bool = True


class MenuItemOut(BaseModel):
    id: int
    category_id: int
    category_name: str
    name: str
    description: str | None
    base_price: int
    image_url: str | None
    temperature_type: str
    tags: list[str]
    is_active: bool
    created_at: datetime


# ---------- Chi nhánh (UC11 – A03) ----------
def _upper(v):
    return clean(v).upper() if isinstance(v, str) else v


class BranchUpdate(BaseModel):
    name: Name100
    address: Annotated[str, BeforeValidator(_clean), Field(min_length=1, max_length=255)]
    phone: Phone = None
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)
    is_active: bool = True


class BranchCreate(BranchUpdate):
    # Tiền tố mã đơn (CG-0142), không đổi được sau khi tạo để mã đơn cũ vẫn khớp chi nhánh
    code: Annotated[str, BeforeValidator(_upper), Field(pattern=r"^[A-Z0-9]{2,10}$")]


class BranchOut(BaseModel):
    id: int
    code: str
    name: str
    address: str
    phone: str | None
    latitude: float | None
    longitude: float | None
    is_active: bool
    table_count: int
    staff_count: int


# ---------- Nhân viên (UC12 – A04) ----------
def _lower(v):
    return v.strip().lower() if isinstance(v, str) else v


Password = Annotated[str, Field(min_length=8, max_length=128)]


class StaffUpdate(BaseModel):
    full_name: Name100
    phone: Phone = None
    role: Role
    branch_id: int | None = None
    is_active: bool = True
    password: Password | None = None  # để trống = giữ mật khẩu cũ


class StaffCreate(StaffUpdate):
    username: Annotated[str, BeforeValidator(_lower), Field(pattern=r"^[a-z0-9_.]{3,50}$")]
    password: Password


class StaffOut(BaseModel):
    id: int
    username: str
    full_name: str
    role: str
    branch_id: int | None
    branch_name: str | None
    phone: str | None
    is_active: bool
    created_at: datetime


# ---------- Menu chi nhánh (UC13 – W06) ----------
class BranchMenuPatch(BaseModel):
    price_override: Price | None = None  # None = dùng giá chung
    is_available: bool = True


class BranchMenuOut(BaseModel):
    menu_item_id: int
    name: str
    category_id: int
    category_name: str
    base_price: int
    price_override: int | None
    is_available: bool
    updated_at: datetime | None


# ---------- Bàn & QR (UC14 – A06) ----------
class TableIn(BaseModel):
    table_number: Annotated[str, BeforeValidator(_upper), Field(pattern=r"^[A-Z0-9-]{1,10}$")]
    is_active: bool = True


class TableOut(BaseModel):
    id: int
    branch_id: int
    table_number: str
    qr_token: str
    qr_url: str
    is_active: bool


# ---------- Khuyến mãi (UC15 – W07) ----------
class PromotionItemIn(BaseModel):
    menu_item_id: int
    promo_price: Price


class PromotionIn(BaseModel):
    name: Name100
    description: Opt255 = None
    branch_id: int | None = None  # None = toàn chuỗi
    start_at: AwareDatetime
    end_at: AwareDatetime
    is_active: bool = True
    items: list[PromotionItemIn] = Field(min_length=1, max_length=50)

    @field_validator("items")
    @classmethod
    def _unique_items(cls, v: list[PromotionItemIn]) -> list[PromotionItemIn]:
        ids = [i.menu_item_id for i in v]
        if len(ids) != len(set(ids)):
            raise ValueError("Mỗi món chỉ được thêm 1 lần vào chương trình")
        return v


PromoStatus = Literal["running", "upcoming", "ended"]


class PromotionItemOut(BaseModel):
    menu_item_id: int
    name: str
    current_price: int
    promo_price: int
    discount_percent: int


class PromotionOut(BaseModel):
    id: int
    name: str
    description: str | None
    branch_id: int | None
    branch_name: str | None
    start_at: datetime
    end_at: datetime
    is_active: bool
    status: PromoStatus
    created_by: str
    items: list[PromotionItemOut]
