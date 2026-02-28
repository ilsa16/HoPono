import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def init_scheduler(app):
    if scheduler.running:
        logger.info("Scheduler already running, skipping init")
        return

    from app.tasks.send_reminders import check_and_send_reminders

    scheduler.add_job(
        func=check_and_send_reminders,
        trigger=IntervalTrigger(minutes=15),
        id="reminder_check",
        replace_existing=True,
        kwargs={"app": app},
    )
    scheduler.start()
    logger.info("Reminder scheduler started — checking every 15 minutes")
