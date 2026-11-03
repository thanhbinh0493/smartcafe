"""API khách: đặt món, thanh toán giả lập, theo dõi đơn (UC04–UC06, SD03) + WebSocket /ws/order/{id}."""
from fastapi import APIRouter, BackgroundTasks, Depends, Query, WebSocket, WebSocketDisconnect
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.errors import AppError
from app.models import Customer
from app.modules.customer.deps import get_optional_customer
from app.modules.order import service
from app.modules.order.schemas import CreateOrderRequest, CreateOrderResponse, OrderView, PayRequest, PayResponse
from app.modules.payment.gateway import PaymentGateway, get_payment_gateway
from app.ws.hub import hub, make_message, reject

router = APIRouter(tags=["public"])


@router.post("/api/public/orders", response_model=CreateOrderResponse, status_code=201)
def create_order(
    body: CreateOrderRequest,
    db: Session = Depends(get_db),
    customer: Customer | None = Depends(get_optional_customer),
) -> CreateOrderResponse:
    """Có customer token (khách thành viên, F4) thì gắn customer_id để cộng điểm khi đơn hoàn tất."""
    res = service.create_order(db, body, customer.id if customer else None)
    db.commit()
    return res


@router.post("/api/public/orders/{order_id}/pay", response_model=PayResponse)
def pay_order(
    order_id: int,
    body: PayRequest,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    gateway: PaymentGateway = Depends(get_payment_gateway),
) -> PayResponse:
    result = service.pay_order(db, order_id, body.access_token, body.method, gateway)
    db.commit()  # lưu cả bản ghi thanh toán FAILED để tra soát
    if not result.success:
        raise AppError(402, "PAYMENT_FAILED", "Thanh toán không thành công, vui lòng thử lại",
                       {"transaction_ref": result.transaction_ref})

    order = service.get_order_for_customer(db, order_id, body.access_token)
    view = service.build_order_view(db, order)
    # Đẩy sự kiện sau khi đã commit: món vào cuối hàng đợi Bar (F3), trang theo dõi đơn cập nhật
    background.add_task(hub.publish, f"bar:{order.branch_id}", "QUEUE_ITEM_ADDED", service.bar_payload(db, order))
    background.add_task(hub.publish, f"order:{order.id}", "ORDER_PAID", view.model_dump(mode="json"))
    return PayResponse(order_id=order.id, status=order.status, paid_at=order.paid_at,
                       transaction_ref=result.transaction_ref)


@router.get("/api/public/orders/{order_id}", response_model=OrderView)
def get_order(order_id: int, token: str = Query(min_length=1, max_length=64), db: Session = Depends(get_db)) -> OrderView:
    order = service.get_order_for_customer(db, order_id, token)
    return service.build_order_view(db, order)


@router.websocket("/ws/order/{order_id}")
async def order_socket(websocket: WebSocket, order_id: int, token: str = "", db: Session = Depends(get_db)):
    """Kênh realtime của trang theo dõi đơn. Khi kết nối (và kết nối lại) luôn gửi ảnh chụp đơn hiện tại (NFR-R3)."""
    def snapshot() -> dict | None:
        db.expire_all()  # luôn đọc trạng thái mới nhất từ CSDL
        try:
            order = service.get_order_for_customer(db, order_id, token)
        except AppError:
            return None
        return service.build_order_view(db, order).model_dump(mode="json")

    data = await run_in_threadpool(snapshot)
    if data is None:
        await reject(websocket, 4404)  # sai mã đơn hoặc access_token
        return
    await websocket.accept()
    channel = f"order:{order_id}"
    hub.subscribe(channel, websocket)
    try:
        await websocket.send_json(make_message("ORDER_SNAPSHOT", data))
        while True:
            await websocket.receive_text()  # client không cần gửi gì; giữ kết nối tới khi ngắt
    except WebSocketDisconnect:
        pass
    finally:
        hub.unsubscribe(channel, websocket)
