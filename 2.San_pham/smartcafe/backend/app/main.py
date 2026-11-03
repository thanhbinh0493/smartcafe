from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.errors import register_error_handlers
from app.modules.auth.router import router as auth_router
from app.modules.bar.router import router as bar_router
from app.modules.branch.router import router as branch_router
from app.modules.menu.router import router as menu_router
from app.modules.order.router import router as order_router


def create_app() -> FastAPI:
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
    app.include_router(menu_router)
    app.include_router(order_router)
    app.include_router(bar_router)

    @app.get("/api/health", tags=["system"])
    def health() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
