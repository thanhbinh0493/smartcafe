"""SQLAlchemy models, ánh xạ 1-1 với 18 bảng trong schema.sql (IV.1)."""
from app.models.analytics import AssociationRule, DailySalesReport, RecommendationLog
from app.models.branch import Branch, DiningTable, Staff
from app.models.customer import Customer, LoyaltyTransaction, OtpRequest
from app.models.menu import BranchMenuItem, Category, MenuItem, Promotion, PromotionItem
from app.models.order import Order, OrderItem, OrderStatusHistory, Payment

__all__ = [
    "AssociationRule", "DailySalesReport", "RecommendationLog",
    "Branch", "DiningTable", "Staff",
    "Customer", "LoyaltyTransaction", "OtpRequest",
    "BranchMenuItem", "Category", "MenuItem", "Promotion", "PromotionItem",
    "Order", "OrderItem", "OrderStatusHistory", "Payment",
]
