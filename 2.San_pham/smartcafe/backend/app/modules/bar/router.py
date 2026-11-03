"""API màn hình Bar (UC17–UC19, SD04) + WebSocket /ws/bar/{branch_id}.

Sự kiện được đẩy sau khi commit (BackgroundTasks):
- kênh bar:{branch_id}: QUEUE_ITEM_ADDED (từ F2), ITEM_UPDATED, ORDER_READY, ORDER_COMPLETED;
- kênh order:{id} (khách): ITEM_PREPARING, ITEM_DONE, ORDER_READY, ORDER_COMPLETED kèm toàn bộ đơn (OrderView);
  QUEUE_POSITION {order_id, queue_position} cho các đơn khác khi hàng đợi dịch chuyển.
"""
from typing import Literal

import jwt
from fastapi import APIRouter, BackgroundTasks, Depends, Query, WebSocket, WebSocketDisconnect
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.errors import AppError
from app.core.security import decode_token
from app.models import Order, Staff
from app.modules.auth.deps import ensure_branch_access, require_roles
from app.modules.bar import service
from app.modules.bar.schemas import BarOrderOut, CompleteOut, ItemActionOut, QueueOut
from app.modules.order.service import build_order_view
from app.ws.hub import hub

router = APIRouter(tags=["bar"])

VIEW_ROLES = ("ADMIN", "MANAGER", "CASHIER", "BARISTA")  # thu ngân chỉ xem (UC17)
ACT_ROLES = ("MANAGER", "BARISTA")                        # Bắt đầu / Xong / Hoàn tác / Đã giao


@router.get("/api/staff/branches/{branch_id}/queue", response_model=QueueOut)
def get_queue(branch_id: int, staff: Staff = Depends(require_roles(*VIEW_ROLES)), db: Session = Depends(get_db)):
    ensure_branch_access(staff, branch_id)
    return service.get_queue(db, branch_id)


@router.get("/api/staff/branches/{branch_id}/orders", response_model=list[BarOrderOut])
def get_orders(
    branch_id: int,
    status: Literal["PAID", "PREPARING", "READY", "COMPLETED", "CANCELLED"] = Query("READY"),
    staff: Staff = Depends(require_roles(*VIEW_ROLES)),
    db: Session = Depends(get_db),
):
    ensure_branch_access(staff, branch_id)
    return service.get_orders(db, branch_id, status)


def _order_view(db: Session, order: Order, **extra) -> dict:
    return {**build_order_view(db, order).model_dump(mode="json"), **extra}


def _publish_queue_positions(background: BackgroundTasks, db: Session, branch_id: int) -> None:
    for oid, pos in service.queue_positions(db, branch_id):
        background.add_task(hub.publish, f"order:{oid}", "QUEUE_POSITION", {"order_id": oid, "queue_position": pos})


def _item_out(item, order) -> ItemActionOut:
    return ItemActionOut(item_id=item.id, item_status=item.status, order_id=order.id, order_status=order.status)


@router.post("/api/staff/order-items/{item_id}/start", response_model=ItemActionOut)
def start_item(item_id: int, background: BackgroundTasks, staff: Staff = Depends(require_roles(*ACT_ROLES)),
               db: Session = Depends(get_db)):
    item, order = service.start_item(db, item_id, staff)
    db.commit()
    out = _item_out(item, order)
    background.add_task(hub.publish, f"bar:{order.branch_id}", "ITEM_UPDATED", out.model_dump())
    background.add_task(hub.publish, f"order:{order.id}", "ITEM_PREPARING", _order_view(db, order, item_id=item.id))
    return out


@router.post("/api/staff/order-items/{item_id}/done", response_model=ItemActionOut)
def done_item(item_id: int, background: BackgroundTasks, staff: Staff = Depends(require_roles(*ACT_ROLES)),
              db: Session = Depends(get_db)):
    item, order, became_ready = service.done_item(db, item_id, staff)
    db.commit()
    out = _item_out(item, order)
    background.add_task(hub.publish, f"bar:{order.branch_id}", "ITEM_UPDATED", out.model_dump())
    if became_ready:
        background.add_task(hub.publish, f"bar:{order.branch_id}", "ORDER_READY",
                            service.bar_order(db, order).model_dump(mode="json"))
        background.add_task(hub.publish, f"order:{order.id}", "ORDER_READY", _order_view(db, order))
        _publish_queue_positions(background, db, order.branch_id)
    else:
        background.add_task(hub.publish, f"order:{order.id}", "ITEM_DONE", _order_view(db, order, item_id=item.id))
    return out


@router.post("/api/staff/order-items/{item_id}/undo", response_model=ItemActionOut)
def undo_item(item_id: int, background: BackgroundTasks, staff: Staff = Depends(require_roles(*ACT_ROLES)),
              db: Session = Depends(get_db)):
    item, order, back_to_queue = service.undo_item(db, item_id, staff)
    db.commit()
    out = _item_out(item, order)
    background.add_task(hub.publish, f"bar:{order.branch_id}", "ITEM_UPDATED", out.model_dump())
    background.add_task(hub.publish, f"order:{order.id}", "ITEM_PREPARING", _order_view(db, order, item_id=item.id))
    if back_to_queue:
        _publish_queue_positions(background, db, order.branch_id)
    return out


@router.post("/api/staff/orders/{order_id}/complete", response_model=CompleteOut)
def complete_order(order_id: int, background: BackgroundTasks, staff: Staff = Depends(require_roles(*ACT_ROLES)),
                   db: Session = Depends(get_db)):
    order, points = service.complete_order(db, order_id, staff)
    db.commit()
    background.add_task(hub.publish, f"bar:{order.branch_id}", "ORDER_COMPLETED", {"order_id": order.id})
    background.add_task(hub.publish, f"order:{order.id}", "ORDER_COMPLETED", _order_view(db, order))
    return CompleteOut(order_id=order.id, status=order.status, completed_at=order.completed_at, points_earned=points)


@router.websocket("/ws/bar/{branch_id}")
async def bar_socket(websocket: WebSocket, branch_id: int, token: str = "", db: Session = Depends(get_db)):
    """Kênh realtime của màn hình Bar. Token = JWT nhân viên (trình duyệt không gửi được header Authorization).
    Sai/hết hạn token: đóng mã 4401; không thuộc chi nhánh: 4403. Kết nối (lại) xong client tự tải lại hàng đợi."""
    def check() -> int:
        try:
            payload = decode_token(token)
        except jwt.InvalidTokenError:
            return 4401
        if payload.get("typ") != "staff":
            return 4401
        db.expire_all()
        staff = db.get(Staff, int(payload["sub"]))
        if staff is None or not staff.is_active:
            return 4401
        try:  # mọi vai trò đều được xem (VIEW_ROLES); chỉ cần đúng chi nhánh
            ensure_branch_access(staff, branch_id)
        except AppError:
            return 4403
        return 0

    code = await run_in_threadpool(check)
    if code:
        await websocket.close(code=code)
        return
    await websocket.accept()
    channel = f"bar:{branch_id}"
    hub.subscribe(channel, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        hub.unsubscribe(channel, websocket)
