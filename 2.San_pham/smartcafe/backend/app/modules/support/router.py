"""API thu ngân hỗ trợ khách (UC20, SD06): tra cứu đơn, hủy đơn & hoàn tiền giả lập.

Sau khi hủy (đã commit) đẩy sự kiện:
- kênh bar:{branch_id}: ORDER_CANCELLED {order_id, order_code} → các màn hình Bar tải lại hàng đợi;
- kênh order:{id}: ORDER_CANCELLED kèm toàn bộ đơn (khách thấy "Đơn đã hủy – đã hoàn tiền" và lý do);
- QUEUE_POSITION cho các đơn phía sau (hàng đợi dịch lên).
"""
from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import Staff
from app.modules.auth.deps import require_roles
from app.modules.bar.router import _order_view, _publish_queue_positions
from app.modules.payment.gateway import PaymentGateway, get_payment_gateway
from app.modules.support import service
from app.modules.support.schemas import CancelIn, SupportOrderOut
from app.ws.hub import hub

router = APIRouter(tags=["support"])

SUPPORT_ROLES = ("CASHIER", "MANAGER")  # ma trận RBAC (III.1): hủy đơn & hoàn tiền


@router.get("/api/staff/orders/search", response_model=list[SupportOrderOut])
def search_orders(
    code: str | None = Query(None, max_length=20),
    table: str | None = Query(None, max_length=10),
    staff: Staff = Depends(require_roles(*SUPPORT_ROLES)),
    db: Session = Depends(get_db),
):
    """Tra cứu trong chi nhánh của nhân viên: theo mã đơn và / hoặc số bàn; không lọc thì trả các đơn gần nhất."""
    return service.search_orders(db, staff.branch_id, code, table)


@router.post("/api/staff/orders/{order_id}/cancel", response_model=SupportOrderOut)
def cancel_order(
    order_id: int,
    body: CancelIn,
    background: BackgroundTasks,
    staff: Staff = Depends(require_roles(*SUPPORT_ROLES)),
    db: Session = Depends(get_db),
    gateway: PaymentGateway = Depends(get_payment_gateway),
):
    order = service.cancel_order(db, order_id, body.reason, staff, gateway)
    db.commit()
    background.add_task(hub.publish, f"bar:{order.branch_id}", "ORDER_CANCELLED",
                        {"order_id": order.id, "order_code": order.order_code})
    background.add_task(hub.publish, f"order:{order.id}", "ORDER_CANCELLED", _order_view(db, order))
    _publish_queue_positions(background, db, order.branch_id)
    return service.support_order(db, order)
