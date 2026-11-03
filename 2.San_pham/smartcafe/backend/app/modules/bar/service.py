"""UC17–UC19: hàng đợi pha chế trên màn hình Bar, Bắt đầu / Xong / Hoàn tác / Đã giao (SD04, SD06).

- Mọi thao tác khóa dòng `orders` (SELECT ... FOR UPDATE) trước khi đổi trạng thái, nên 2 pha chế bấm cùng
  lúc không làm hỏng trạng thái: người thứ hai nhận 409 INVALID_STATE_TRANSITION.
- Cộng điểm khi đơn hoàn tất: floor(total / 10.000) (D15), mỗi đơn 1 lần (loyalty_transactions.order_id UNIQUE).
"""
from datetime import timedelta

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models import Customer, DiningTable, LoyaltyTransaction, MenuItem, Order, OrderItem, OrderStatusHistory, Staff
from app.modules.auth.deps import ensure_branch_access
from app.modules.bar.schemas import BarOrderItemOut, BarOrderOut, QueueItemOut, QueueOut
from app.modules.order.service import ACTIVE_QUEUE_STATUSES

UNDO_WINDOW_SECONDS = 10   # nút "Hoàn tác" hiện 10 giây trên màn hình Bar (UC18 – 3a)
UNDO_GRACE_SECONDS = 5     # server cho thêm vài giây để bù trễ mạng
POINT_UNIT = 10_000        # 1 điểm / 10.000đ (D15)


def get_queue(db: Session, branch_id: int) -> QueueOut:
    """Các món WAITING/PREPARING của đơn PAID/PREPARING, sắp theo giờ gọi; món cùng đơn đứng liền nhau."""
    rows = db.execute(
        select(OrderItem, Order, DiningTable.table_number, MenuItem.name)
        .join(Order, Order.id == OrderItem.order_id)
        .join(DiningTable, DiningTable.id == Order.table_id)
        .join(MenuItem, MenuItem.id == OrderItem.menu_item_id)
        .where(
            Order.branch_id == branch_id,
            Order.status.in_(ACTIVE_QUEUE_STATUSES),
            OrderItem.status.in_(("WAITING", "PREPARING")),
        )
        .order_by(Order.paid_at, Order.id, OrderItem.id)
    ).all()
    return QueueOut(
        branch_id=branch_id,
        server_time=db.scalar(select(func.now())),
        items=[
            QueueItemOut(
                id=i.id, order_id=o.id, order_code=o.order_code, table_number=table, paid_at=o.paid_at,
                name=name, quantity=i.quantity, note=i.note, order_note=o.note, status=i.status, started_at=i.started_at,
            )
            for i, o, table, name in rows
        ],
    )


def get_orders(db: Session, branch_id: int, status: str) -> list[BarOrderOut]:
    orders = db.scalars(
        select(Order).where(Order.branch_id == branch_id, Order.status == status)
        .order_by(Order.ready_at.asc().nulls_last(), Order.paid_at, Order.id)
        .limit(100)
    ).all()
    return [bar_order(db, o) for o in orders]


def bar_order(db: Session, order: Order) -> BarOrderOut:
    table = db.get(DiningTable, order.table_id)
    names = dict(db.execute(
        select(MenuItem.id, MenuItem.name).where(MenuItem.id.in_([i.menu_item_id for i in order.items]))
    ).all())
    return BarOrderOut(
        id=order.id, order_code=order.order_code, table_number=table.table_number, status=order.status,
        is_member=order.customer_id is not None, total=order.total_amount,
        paid_at=order.paid_at, ready_at=order.ready_at,
        items=[BarOrderItemOut(id=i.id, name=names.get(i.menu_item_id, ""), quantity=i.quantity, note=i.note,
                               status=i.status)
               for i in sorted(order.items, key=lambda i: i.id)],
    )


# ---------- thao tác của pha chế ----------

def _lock_order(db: Session, order_id: int, staff: Staff) -> Order:
    order = db.scalar(select(Order).where(Order.id == order_id).with_for_update())
    if order is None:
        raise AppError(404, "ORDER_NOT_FOUND", "Không tìm thấy đơn hàng")
    db.refresh(order)  # đọc lại sau khi đã giữ khóa
    ensure_branch_access(staff, order.branch_id)
    return order


def _lock_item(db: Session, item_id: int, staff: Staff) -> tuple[OrderItem, Order]:
    order_id = db.scalar(select(OrderItem.order_id).where(OrderItem.id == item_id))
    if order_id is None:
        raise AppError(404, "ITEM_NOT_FOUND", "Không tìm thấy món trong hàng đợi")
    order = _lock_order(db, order_id, staff)
    # Nạp lại các món của đơn sau khi khóa (có thể pha chế khác vừa đổi trạng thái)
    items = db.scalars(
        select(OrderItem).where(OrderItem.order_id == order.id).execution_options(populate_existing=True)
    ).all()
    return next(i for i in items if i.id == item_id), order


def _set_status(db: Session, order: Order, to: str, staff: Staff) -> None:
    db.add(OrderStatusHistory(order_id=order.id, from_status=order.status, to_status=to, source="STAFF",
                              staff_id=staff.id))
    order.status = to


def _conflict(message: str, item: OrderItem | None = None, order: Order | None = None) -> AppError:
    details = {}
    if item is not None:
        details["item_status"] = item.status
    if order is not None:
        details["order_status"] = order.status
    return AppError(409, "INVALID_STATE_TRANSITION", message, details)


def start_item(db: Session, item_id: int, staff: Staff) -> tuple[OrderItem, Order]:
    """UC18 – "Bắt đầu": WAITING → PREPARING; đơn PAID → PREPARING."""
    item, order = _lock_item(db, item_id, staff)
    if order.status not in ACTIVE_QUEUE_STATUSES:
        raise _conflict("Đơn không còn trong hàng đợi (đã xong hoặc đã hủy)", item, order)
    if item.status != "WAITING":
        raise _conflict("Món này đã được bắt đầu pha", item, order)
    item.status, item.started_at = "PREPARING", func.now()
    if order.status == "PAID":
        _set_status(db, order, "PREPARING", staff)
    db.flush()
    db.refresh(item)
    return item, order


def done_item(db: Session, item_id: int, staff: Staff) -> tuple[OrderItem, Order, bool]:
    """UC18 – "Xong": PREPARING → DONE. Món cuối cùng xong thì đơn → READY. Trả (món, đơn, đơn vừa READY?)."""
    item, order = _lock_item(db, item_id, staff)
    # Kiểm tra đơn còn trong hàng đợi (PAID/PREPARING) trước, rồi mới tới trạng thái món (BUG-F3-01)
    if order.status not in ACTIVE_QUEUE_STATUSES:
        raise _conflict("Đơn không còn trong hàng đợi (đã xong hoặc đã hủy)", item, order)
    if item.status != "PREPARING":
        msg = "Món đã xong rồi" if item.status == "DONE" else "Cần bấm \"Bắt đầu\" trước khi bấm \"Xong\""
        raise _conflict(msg, item, order)
    item.status, item.done_at = "DONE", func.now()
    became_ready = all(i.status in ("DONE", "CANCELLED") for i in order.items)
    if became_ready:
        _set_status(db, order, "READY", staff)
        order.ready_at = func.now()
    db.flush()
    db.refresh(item)
    db.refresh(order)
    return item, order, became_ready


def undo_item(db: Session, item_id: int, staff: Staff) -> tuple[OrderItem, Order, bool]:
    """UC18 – 3a "Hoàn tác" trong 10 giây: DONE → PREPARING. Nếu đơn đã READY vì món này thì đơn → PREPARING
    (P15). Trả (món, đơn, đơn vừa quay lại hàng đợi?)."""
    item, order = _lock_item(db, item_id, staff)
    if item.status != "DONE" or order.status not in ("PREPARING", "READY"):
        raise _conflict("Không thể hoàn tác: món chưa xong hoặc đơn đã giao / đã hủy", item, order)
    elapsed = db.scalar(select(func.now())) - item.done_at
    if elapsed > timedelta(seconds=UNDO_WINDOW_SECONDS + UNDO_GRACE_SECONDS):
        raise AppError(409, "UNDO_EXPIRED", f"Đã quá {UNDO_WINDOW_SECONDS} giây, không thể hoàn tác",
                       {"item_status": item.status})
    item.status, item.done_at = "PREPARING", None
    back_to_queue = order.status == "READY"
    if back_to_queue:
        _set_status(db, order, "PREPARING", staff)
        order.ready_at = None
    db.flush()
    db.refresh(item)
    db.refresh(order)
    return item, order, back_to_queue


def complete_order(db: Session, order_id: int, staff: Staff) -> tuple[Order, int | None]:
    """UC19 – "Đã giao": READY → COMPLETED; cộng điểm cho khách thành viên. Trả (đơn, số điểm cộng | None)."""
    order = _lock_order(db, order_id, staff)
    if order.status != "READY":
        raise _conflict("Chỉ đơn ở trạng thái \"Có thể lấy\" mới bấm \"Đã giao\" được", order=order)
    _set_status(db, order, "COMPLETED", staff)
    order.completed_at, order.completed_by = func.now(), staff.id

    points = None
    if order.customer_id is not None:
        points = order.total_amount // POINT_UNIT
        if points > 0:
            db.add(LoyaltyTransaction(customer_id=order.customer_id, order_id=order.id, points=points, type="EARN"))
            db.execute(update(Customer).where(Customer.id == order.customer_id)
                       .values(loyalty_points=Customer.loyalty_points + points))
    db.flush()
    db.refresh(order)
    return order, points


def queue_positions(db: Session, branch_id: int) -> list[tuple[int, int]]:
    """(order_id, vị trí) của mọi đơn đang chờ/đang pha – gửi QUEUE_POSITION khi hàng đợi dịch chuyển."""
    ids = db.scalars(
        select(Order.id).where(Order.branch_id == branch_id, Order.status.in_(ACTIVE_QUEUE_STATUSES))
        .order_by(Order.paid_at, Order.id)
    ).all()
    return [(oid, pos) for pos, oid in enumerate(ids, start=1)]
