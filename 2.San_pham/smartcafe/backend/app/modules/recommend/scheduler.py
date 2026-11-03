"""Job nền (APScheduler, giờ Việt Nam):
- 00:05 – tổng hợp báo cáo ngày hôm trước cho mọi chi nhánh (F8, UC16, D21);
- 00:30 – học lại luật kết hợp "thường gọi kèm" (F7, II.2 Mục 2.4);
- ngay khi khởi động – bù báo cáo các ngày còn thiếu trong 60 ngày (laptop demo thường tắt lúc 00:05)."""
from datetime import timedelta
import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.core import cache
from app.core.config import get_settings
from app.core.db import SessionLocal
from app.modules.recommend.training import rebuild_rules
from app.modules.report.service import build_day, catch_up, today_vn

log = logging.getLogger("smartcafe.scheduler")
TZ = "Asia/Ho_Chi_Minh"


def rules_job() -> None:
    try:
        with SessionLocal() as db:
            rebuild_rules(db)
            db.commit()
        cache.invalidate("rules")          # sau commit: lần gợi ý sau đọc luật mới
    except Exception:  # job lỗi không được làm sập backend; lần sau chạy lại
        log.exception("Job học luật kết hợp lỗi")


def report_job() -> None:
    try:
        with SessionLocal() as db:
            build_day(db, today_vn() - timedelta(days=1))
            db.commit()
    except Exception:
        log.exception("Job báo cáo ngày lỗi")


def catch_up_job() -> None:
    try:
        with SessionLocal() as db:
            n = catch_up(db)
            db.commit()
        if n:
            log.info("Đã bù %d báo cáo ngày còn thiếu", n)
    except Exception:
        log.exception("Bù báo cáo ngày lỗi")


def start_scheduler() -> BackgroundScheduler | None:
    s = get_settings()
    if not s.scheduler_enabled:
        return None
    sched = BackgroundScheduler(timezone=TZ)
    sched.add_job(rules_job, "cron", hour=s.rules_job_hour, minute=s.rules_job_minute, id="rebuild_rules",
                  replace_existing=True, coalesce=True, misfire_grace_time=3600)
    sched.add_job(report_job, "cron", hour=s.report_job_hour, minute=s.report_job_minute, id="daily_report",
                  replace_existing=True, coalesce=True, misfire_grace_time=3600)
    sched.add_job(catch_up_job, id="report_catch_up", replace_existing=True)  # chạy 1 lần ngay khi khởi động
    sched.start()
    log.info("Scheduler đã chạy: báo cáo ngày %02d:%02d, học luật kết hợp %02d:%02d hằng ngày",
             s.report_job_hour, s.report_job_minute, s.rules_job_hour, s.rules_job_minute)
    return sched
