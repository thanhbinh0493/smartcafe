"""UC04–UC06: tạo đơn, thanh toán giả lập, xem đơn (SD03).

- Giá và tổng tiền luôn tính lại ở server bằng cùng hàm của menu (NFR-S6).
- Mã đơn = {mã chi nhánh}-{số thứ tự trong ngày, 4 chữ số}; UNIQUE (order_code, order_date) (D28).
"""
import secrets
from collections import Counter
from datetime import date

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models import (
    Branch, DiningTable, LoyaltyTransaction, MenuItem, Order, OrderItem, OrderStatusHistory, Payment,
)
from app.modules.menu.service import get_branch_menu
from app.modules.order.schemas import (
    MAX_QTY_PER_ITEM, CreateOrderRequest, CreateOrderResponse, OrderLineOut, OrderView,
)
from app.modules.payment.gateway import ChargeResult, PaymentGateway

ACTIVE_QUEUE_STATUSES = ("PAID", "PREPARING")
_ORDER_CODE_LOCK = 8_201  # khóa advisory theo chi nhánh khi cấp số thứ tự đơn


def _lookup_table(db: Session, qr_token: str) -> tuple[DiningTable, Branch]:
    row = db.execute(
        select(DiningTable, Branch).join(Branch, Branch.id == DiningTable.branch_id)
        .where(DiningTable.qr_token == qr_token)
    ).first()
    if row is None or not row.DiningTable.is_active or not row.Branch.is_active:
        raise AppError(404, "TABLE_NOT_FOUND", "Mã QR không hợp lệ, vui lòng gọi nhân viên")
    return row.DiningTable, row.Branch


def _next_order_code(db: Session, branch: Branch) -> tuple[str, date]:
    # Khóa theo chi nhánh trong transaction để 2 đơn đặt cùng lúc không lấy trùng số
    db.execute(text("SELECT pg_advisory_xact_lock(:k, :b)"), {"k": _ORDER_CODE_LOCK, "b": branch.id})
    today = db.scalar(text("SELECT (now() AT TIME ZONE 'Asia/Ho_Chi_Minh')::date"))
    count = db.scalar(
        select(func.count()).select_from(Order).where(Order.branch_id == branch.id, Order.order_date == today)
    )
    return f"{branch.code}-{count + 1:04d}", today


def create_order(db: Session, req: CreateOrderRequest, customer_id: int | None = None) -> CreateOrderResponse:
    table, branch = _lookup_table(db, req.qr_token)

    qty_per_item = Counter()
    for line in req.items:
        qty_per_item[line.menu_item_id] += line.quantity
    over = [mid for mid, q in qty_per_item.items() if q > MAX_QTY_PER_ITEM]
    if over:
        raise AppError(422, "QUANTITY_LIMIT", f"Mỗi món tối đa {MAX_QTY_PER_ITEM} ly trong một đơn",
                       {"item_ids": over})

    menu = {it.id: it for it in get_branch_menu(db, branch.id)}
    unavailable = [mid for mid in qty_per_item if mid not in menu or not menu[mid].is_available]
    if unavailable:
        names = [menu[m].name for m in unavailable if m in menu]
        msg = f"Món {', '.join(names)} đã tạm hết" if names else "Có món không còn bán"
        raise AppError(409, "ITEM_UNAVAILABLE", msg + ", vui lòng bỏ khỏi giỏ hàng", {"item_ids": unavailable})

    subtotal = sum(menu[l.menu_item_id].regular_price * l.quantity for l in req.items)
    total = sum(menu[l.menu_item_id].sell_price * l.quantity for l in req.items)
    if req.expected_total is not None and req.expected_total != total:
        prices = [{"menu_item_id": mid, "regular_price": menu[mid].regular_price, "sell_price": menu[mid].sell_price,
                   "is_promo": menu[mid].is_promo} for mid in qty_per_item]
        raise AppError(409, "PRICE_CHANGED", "Giá một số món vừa thay đổi, vui lòng kiểm tra lại giỏ hàng",
                       {"total": total, "prices": prices})

    code, today = _next_order_code(db, branch)
    order = Order(
        order_code=code, order_date=today, access_token=secrets.token_urlsafe(16),
        branch_id=branch.id, table_id=table.id, customer_id=customer_id,
        status="PENDING_PAYMENT", total_amount=total, note=req.note,
        items=[
            OrderItem(
                menu_item_id=l.menu_item_id, quantity=l.quantity, note=l.note or None,
                original_price=menu[l.menu_item_id].regular_price, unit_price=menu[l.menu_item_id].sell_price,
                promotion_id=menu[l.menu_item_id].promotion_id, is_recommended=l.is_recommended,
            )
            for l in req.items
        ],
    )
    db.add(order)
    db.flush()
    db.add(OrderStatusHistory(order_id=order.id, from_status=None, to_status="PENDING_PAYMENT", source="CUSTOMER"))
    db.flush()

    return CreateOrderResponse(
        order_id=order.id, order_code=order.order_code, access_token=order.access_token, status=order.status,
        subtotal=subtotal, discount=subtotal - total, total=total,
        expected_points=total // 10_000 if customer_id else None,
        items=[_line(i, menu[i.menu_item_id].name) for i in order.items],
    )


def get_order_for_customer(db: Session, order_id: int, access_token: str, *, lock: bool = False) -> Order:
    """Khách chỉ xem/thao tác được đơn khi có đúng access_token (UC06 – bảo mật)."""
    stmt = select(Order).where(Order.id == order_id)
    if lock:
        stmt = stmt.with_for_update()
    order = db.scalar(stmt)
    if order is None or not secrets.compare_digest(order.access_token, access_token):
        raise AppError(404, "ORDER_NOT_FOUND", "Không tìm thấy đơn hàng")
    return order


def pay_order(db: Session, order_id: int, access_token: str, method: str, gateway: PaymentGateway) -> ChargeResult:
    """Trả kết quả thanh toán. Khi thất bại, đơn giữ PENDING_PAYMENT và router vẫn commit bản ghi FAILED."""
    order = get_order_for_customer(db, order_id, access_token, lock=True)
    if order.status != "PENDING_PAYMENT":
        msg = "Đơn đã được thanh toán" if order.paid_at else "Đơn không còn ở trạng thái chờ thanh toán"
        raise AppError(409, "INVALID_STATE_TRANSITION", msg, {"status": order.status})

    result = gateway.charge(order.total_amount, method, order.order_code)
    payment = db.scalar(select(Payment).where(Payment.order_id == order.id))
    if payment is None:
        payment = Payment(order_id=order.id)
        db.add(payment)
    # payments.order_id là UNIQUE: lưu lần thử gần nhất (FAILED rồi SUCCESS khi khách thử lại)
    payment.method, payment.amount, payment.transaction_ref = method, order.total_amount, result.transaction_ref
    payment.status = "SUCCESS" if result.success else "FAILED"
    payment.paid_at = func.now()
    if result.success:
        order.status = "PAID"
        order.paid_at = func.now()
        db.add(OrderStatusHistory(order_id=order.id, from_status="PENDING_PAYMENT", to_status="PAID", source="CUSTOMER"))
    db.flush()
    db.refresh(order)
    return result


def queue_position(db: Session, order: Order) -> int | None:
    """Số đơn đang chờ/đang pha của chi nhánh được gọi trước đơn này + 1."""
    if order.status not in ACTIVE_QUEUE_STATUSES or order.paid_at is None:
        return None
    ahead = db.scalar(
        select(func.count()).select_from(Order).where(
            Order.branch_id == order.branch_id,
            Order.status.in_(ACTIVE_QUEUE_STATUSES),
            (Order.paid_at < order.paid_at) | ((Order.paid_at == order.paid_at) & (Order.id < order.id)),
        )
    )
    return ahead + 1


def build_order_view(db: Session, order: Order) -> OrderView:
    branch = db.get(Branch, order.branch_id)
    table = db.get(DiningTable, order.table_id)
    names = dict(db.execute(
        select(MenuItem.id, MenuItem.name).where(MenuItem.id.in_([i.menu_item_id for i in order.items]))
    ).all())
    items = sorted(order.items, key=lambda i: i.id)
    subtotal = sum(i.original_price * i.quantity for i in items)
    return OrderView(
        id=order.id, order_code=order.order_code, order_date=order.order_date, status=order.status,
        branch_name=branch.name, table_number=table.table_number,
        subtotal=subtotal, discount=subtotal - order.total_amount, total=order.total_amount,
        queue_position=queue_position(db, order),
        created_at=order.created_at, paid_at=order.paid_at, ready_at=order.ready_at,
        completed_at=order.completed_at, cancelled_at=order.cancelled_at, cancel_reason=order.cancel_reason,
        points_earned=(db.scalar(select(LoyaltyTransaction.points).where(LoyaltyTransaction.order_id == order.id)) or 0)
        if order.customer_id and order.status == "COMPLETED" else None,
        expected_points=order.total_amount // 10_000 if order.customer_id else None,
        items=[_line(i, names.get(i.menu_item_id, "")) for i in items],
    )


def _line(i: OrderItem, name: str) -> OrderLineOut:
    return OrderLineOut(
        id=i.id, menu_item_id=i.menu_item_id, name=name, quantity=i.quantity,
        original_price=i.original_price, unit_price=i.unit_price, is_promo=i.promotion_id is not None,
        note=i.note, status=i.status,
    )


def bar_payload(db: Session, order: Order) -> dict:
    """Dữ liệu đẩy lên màn hình Bar khi có đơn mới được thanh toán (QUEUE_ITEM_ADDED)."""
    view = build_order_view(db, order)
    return {
        "order_id": view.id, "order_code": view.order_code, "table_number": view.table_number,
        "paid_at": view.paid_at.isoformat() if view.paid_at else None,
        "items": [{"id": i.id, "name": i.name, "quantity": i.quantity, "note": i.note, "status": i.status}
                  for i in view.items],
    }
