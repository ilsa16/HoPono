from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

scheduler = BackgroundScheduler()


def init_scheduler(app):
    """Initialize the background scheduler with the Flask app context."""
    from app.tasks.send_reminders import check_and_send_reminders

    scheduler.add_job(
        func=check_and_send_reminders,
        trigger=IntervalTrigger(minutes=15),
        id="reminder_check",
        replace_existing=True,
        kwargs={"app": app},
    )
    scheduler.start()
