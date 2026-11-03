"""Gắn đơn vào lần gợi ý (recommendation_logs.order_id – D34), phục vụ đánh giá online (II.2 Mục 2.5)."""
from datetime import timedelta

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models import Order, RecommendationLog

MAX_AGE = timedelta(hours=2)  # chỉ gắn lần gợi ý gần đây (1 lần ngồi quán)


def attach_order(db: Session, log_id: int, order: Order) -> bool:
    """Chỉ gắn khi log cùng chi nhánh, cùng khách (hoặc cùng ẩn danh), chưa gắn đơn nào và còn mới.
    Không hợp lệ thì bỏ qua lặng lẽ – không bao giờ làm hỏng việc đặt đơn (NFR-R1)."""
    res = db.execute(
        update(RecommendationLog)
        .where(
            RecommendationLog.id == log_id,
            RecommendationLog.branch_id == order.branch_id,
            RecommendationLog.order_id.is_(None),
            (RecommendationLog.customer_id == order.customer_id) if order.customer_id
            else RecommendationLog.customer_id.is_(None),
            RecommendationLog.created_at >= order.created_at - MAX_AGE,
        )
        .values(order_id=order.id)
    )
    return res.rowcount == 1
