import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.core.errors import register_error_handlers
from app.modules.admin import branches, catalog, promotions, staff
from app.modules.auth.router import router as auth_router
from app.modules.bar.router import router as bar_router
from app.modules.branch.router import router as branch_router
from app.modules.customer.router import router as customer_router
from app.modules.menu.router import router as menu_router
from app.modules.menu.router import ws_router as menu_ws_router
from app.modules.order.router import router as order_router
from app.modules.support.router import router as support_router


def _setup_logging() -> None:
    """Log nghiệp vụ (VD: Mock SMS) ra stdout để xem bằng `docker compose logs backend`."""
    logger = logging.getLogger("smartcafe")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        h = logging.StreamHandler()
        h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        logger.addHandler(h)


def create_app() -> FastAPI:
    _setup_logging()
    app = FastAPI(title="SmartCafe API", version="0.1.0", description="API hệ thống SmartCafe – Nhóm 8")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_settings().cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_error_handlers(app)
    app.include_router(auth_router)
    app.include_router(branch_router)
    app.include_router(customer_router)
    app.include_router(menu_router)
    app.include_router(order_router)
    app.include_router(bar_router)
    app.include_router(support_router)
    app.include_router(menu_ws_router)
    for module in (catalog, branches, staff, promotions):  # F6 – quản trị
        app.include_router(module.router)

    # Ảnh món đã upload (W05). Đặt dưới /api/ để Nginx chuyển tiếp như các API khác.
    uploads = Path(get_settings().upload_dir)
    uploads.mkdir(parents=True, exist_ok=True)
    app.mount("/api/uploads", StaticFiles(directory=uploads), name="uploads")

    @app.get("/api/health", tags=["system"])
    def health() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
