from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta

from database import SessionLocal
from models import SchedulerSettings
from services import ESP32Config

get_esp32_client = ESP32Config()

class SchedulerManager:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.scheduler.start()

    async def run_job(self, schedule_id: int):
        db = SessionLocal()
        try:
            schedule = db.query(SchedulerSettings).get(schedule_id)
            if not schedule or not schedule.is_enabled:
                return

            now = datetime.utcnow()

            if schedule.last_run:
                if now - schedule.last_run < timedelta(hours=1):
                    return

            result = get_esp32_client.start_feeding()
            if 'error' not in result:
                schedule.last_run = now
                db.commit()

        finally:
            db.close()

    def create_trigger(self, schedule):
        if schedule.scheduler_type == "daily":
            return CronTrigger(hour=schedule.hour, minute=26)

        elif schedule.scheduler_type == "weekly":
            return CronTrigger(day_of_week='mon', hour=schedule.hour, minute=0)

        elif schedule.scheduler_type == "monthly":
            return CronTrigger(day=1, hour=schedule.hour, minute=0)

        elif schedule.scheduler_type == "custom":
            return IntervalTrigger(hours=schedule.hour)

    def sync_job(self, schedule):
        job_id = str(schedule.id)   
        job = self.scheduler.get_job(job_id)

        if schedule.is_enabled:
            if job:
                return

            trigger = self.create_trigger(schedule)

            self.scheduler.add_job(
                self.run_job,
                trigger=trigger,
                args=[job_id],
                id=job_id,
                replace_existing=True,
                misfire_grace_time=3600,
                coalesce=True
            )
            
            # if True:
            #     import asyncio
            #     asyncio.create_task(self.run_job(schedule.id))
        else:
            if job:
                self.scheduler.remove_job(job_id)

    def load_all(self):
        db = SessionLocal()

        try:
            schedules = db.query(SchedulerSettings).all()

            active_job_ids = set()

            for schedule in schedules:
                job_id = schedule.id

                if schedule.is_enabled:
                    self.sync_job(schedule)
                    active_job_ids.add(job_id)
                else:
                    if self.scheduler.get_job(job_id):
                        self.scheduler.remove_job(job_id)

            for job in self.scheduler.get_jobs():
                if job.id not in active_job_ids:
                    self.scheduler.remove_job(job.id)

        except Exception as e:
            print("Error loading schedules:", e)

        finally:
            db.close()
   


# scheduler_service = SchedulerService()
# SchedulerManager()