# app/services/scheduler.py
from __future__ import annotations
import os
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.services.weekly_review import upsert_this_week

scheduler: BackgroundScheduler | None = None

def _job_weekly_review():
    db: Session = SessionLocal()
    try:
        upsert_this_week(db)
    finally:
        db.close()

def start_scheduler():
    """
    毎週日曜21:00(JST)に週次レビューを自動生成。
    Uvicornのリロード多重起動を避けるため、二重起動チェック付き。
    """
    global scheduler
    if scheduler and scheduler.running:
        return
    scheduler = BackgroundScheduler(timezone="Asia/Tokyo")
    trigger = CronTrigger(day_of_week="sun", hour=21, minute=0, second=0, timezone="Asia/Tokyo")
    scheduler.add_job(_job_weekly_review, trigger, id="weekly_review", replace_existing=True)
    scheduler.start()
