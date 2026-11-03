"""Job nền (APScheduler): học lại luật kết hợp hằng đêm lúc 00:30 giờ Việt Nam (II.2 Mục 2.4).
Job báo cáo ngày 00:05 (F8) sẽ đăng ký vào cùng scheduler này."""
import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.modules.recommend.training import rebuild_rules

log = logging.getLogger("smartcafe.scheduler")
TZ = "Asia/Ho_Chi_Minh"


def rules_job() -> None:
    try:
        with SessionLocal() as db:
            rebuild_rules(db)
            db.commit()
    except Exception:  # job lỗi không được làm sập backend; lần sau chạy lại
        log.exception("Job học luật kết hợp lỗi")


def start_scheduler() -> BackgroundScheduler | None:
    s = get_settings()
    if not s.scheduler_enabled:
        return None
    sched = BackgroundScheduler(timezone=TZ)
    sched.add_job(rules_job, "cron", hour=s.rules_job_hour, minute=s.rules_job_minute, id="rebuild_rules",
                  replace_existing=True, coalesce=True, misfire_grace_time=3600)
    sched.start()
    log.info("Scheduler đã chạy: học luật kết hợp lúc %02d:%02d hằng ngày", s.rules_job_hour, s.rules_job_minute)
    return sched
