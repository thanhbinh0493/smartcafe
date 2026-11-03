"""UC20 – Thu ngân hỗ trợ khách: tra cứu đơn, hủy đơn & hoàn tiền giả lập (SD06, D19).

- Chỉ hủy được đơn PAID / PREPARING (đơn chưa thanh toán do hệ thống tự hủy; đơn READY / COMPLETED không hủy).
- Khóa dòng `orders` như màn hình Bar, nên hủy đúng lúc pha chế bấm "Xong" không làm sai trạng thái.
- Hoàn tiền qua PaymentGateway; cổng báo lỗi thì không đổi gì (rollback) và báo 502 REFUND_FAILED.
- Đơn bị hủy không bao giờ phát sinh điểm (điểm chỉ cộng khi COMPLETED – D11).
"""
from sqlalchemy import func, or_, select, text
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models import DiningTable, MenuItem, Order, OrderItem, Payment, Staff
from app.modules.bar.service import _lock_order, _set_status
from app.modules.payment.gateway import PaymentGateway
from app.modules.support.schemas import SupportItemOut, SupportOrderOut, SupportPaymentOut

CANCELLABLE = ("PAID", "PREPARING")
OPEN_STATUSES = ("PAID", "PREPARING", "READY")
SEARCH_LIMIT = 50


def _today(db: Session):
    return db.scalar(text("SELECT (now() AT TIME ZONE 'Asia/Ho_Chi_Minh')::date"))


def search_orders(db: Session, branch_id: int, code: str | None, table: str | None) -> list[SupportOrderOut]:
    """Đơn của chi nhánh trong ngày hôm nay, cộng các đơn ngày trước vẫn còn dở (chờ / đang pha / có thể lấy)
    để thu ngân xử lý đơn tồn. Lọc theo mã đơn (khớp một phần, không phân biệt hoa thường) và / hoặc số bàn."""
    stmt = (
        select(Order).join(DiningTable, DiningTable.id == Order.table_id)
        .where(Order.branch_id == branch_id, Order.status != "PENDING_PAYMENT",
               or_(Order.order_date == _today(db), Order.status.in_(OPEN_STATUSES)))
    )
    if code:
        stmt = stmt.where(Order.order_code.ilike(f"%{code.strip()}%"))
    if table:
        stmt = stmt.where(DiningTable.table_number == table.strip())
    orders = db.scalars(stmt.order_by(Order.paid_at.desc().nulls_last(), Order.id.desc()).limit(SEARCH_LIMIT)).all()
    return [support_order(db, o) for o in orders]


def support_order(db: Session, order: Order) -> SupportOrderOut:
    table = db.get(DiningTable, order.table_id)
    names = dict(db.execute(
        select(MenuItem.id, MenuItem.name).where(MenuItem.id.in_([i.menu_item_id for i in order.items]))
    ).all())
    pay = db.scalar(select(Payment).where(Payment.order_id == order.id))
    by = db.get(Staff, order.cancelled_by) if order.cancelled_by else None
    return SupportOrderOut(
        id=order.id, order_code=order.order_code, order_date=order.order_date, table_number=table.table_number,
        status=order.status, total=order.total_amount, is_member=order.customer_id is not None, note=order.note,
        created_at=order.created_at, paid_at=order.paid_at, cancelled_at=order.cancelled_at,
        cancel_reason=order.cancel_reason, cancelled_by=by.full_name if by else None,
        can_cancel=order.status in CANCELLABLE,
        payment=SupportPaymentOut(method=pay.method, amount=pay.amount, status=pay.status,
                                  transaction_ref=pay.transaction_ref, refunded_at=pay.refunded_at) if pay else None,
        items=[SupportItemOut(id=i.id, name=names.get(i.menu_item_id, ""), quantity=i.quantity,
                              unit_price=i.unit_price, note=i.note, status=i.status)
               for i in sorted(order.items, key=lambda i: i.id)],
    )


_REFUSE = {
    "PENDING_PAYMENT": "Đơn chưa thanh toán, hệ thống sẽ tự hủy sau 15 phút",
    "READY": "Đồ uống đã pha xong (\"Có thể lấy\"), không thể hủy",
    "COMPLETED": "Khách đã nhận đồ, không thể hủy",
    "CANCELLED": "Đơn đã được hủy trước đó",
}


def cancel_order(db: Session, order_id: int, reason: str, staff: Staff, gateway: PaymentGateway) -> Order:
    order = _lock_order(db, order_id, staff)
    if order.status not in CANCELLABLE:
        raise AppError(409, "CANNOT_CANCEL", _REFUSE.get(order.status, "Không thể hủy đơn này"),
                       {"order_status": order.status})
    pay = db.scalar(select(Payment).where(Payment.order_id == order.id).with_for_update())
    result = gateway.refund(pay.transaction_ref, pay.amount)
    if not result.success:
        raise AppError(502, "REFUND_FAILED", "Cổng thanh toán từ chối hoàn tiền, vui lòng thử lại",
                       {"transaction_ref": pay.transaction_ref})
    pay.status, pay.refunded_at = "REFUNDED", func.now()

    _set_status(db, order, "CANCELLED", staff)
    order.cancel_reason, order.cancelled_by, order.cancelled_at = reason, staff.id, func.now()
    for item in db.scalars(select(OrderItem).where(OrderItem.order_id == order.id)
                           .execution_options(populate_existing=True)).all():
        item.status = "CANCELLED"
    db.flush()
    db.refresh(order)
    return order
