import logging
from datetime import datetime, timedelta
from app.extensions import db
from app.models.booking import Booking
from app.models.reminder_log import ReminderLog
from app.models.settings import Setting
from app.services.reminder_service import (
    send_sms,
    send_email,
    build_reminder_sms,
    build_reminder_email,
)

logger = logging.getLogger(__name__)


def check_and_send_reminders(app):
    """
    Check for upcoming bookings that need reminders sent.
    This runs every 15 minutes via APScheduler.
    """
    with app.app_context():
        # Get reminder timing from settings
        setting = db.session.get(Setting, "reminder_hours_before")
        hours_before = int(setting.value) if setting else 24

        sms_setting = db.session.get(Setting, "sms_enabled")
        sms_enabled = sms_setting.value.lower() == "true" if sms_setting else True

        email_setting = db.session.get(Setting, "email_enabled")
        email_enabled = email_setting.value.lower() == "true" if email_setting else True

        now = datetime.utcnow()
        target = now + timedelta(hours=hours_before)

        # Find bookings that need reminders
        bookings = (
            Booking.query.filter(
                Booking.status == "confirmed",
                Booking.date == target.date(),
            )
            .all()
        )

        for booking in bookings:
            booking_dt = datetime.combine(booking.date, booking.start_time)

            # Only send if within the reminder window
            if not (now < booking_dt <= target + timedelta(minutes=15)):
                continue

            # Check if reminder already sent
            existing = ReminderLog.query.filter(
                ReminderLog.booking_id == booking.id,
                ReminderLog.status == "sent",
            ).first()
            if existing:
                continue

            client = booking.client
            service = booking.service
            time_str = booking.start_time.strftime("%H:%M")
            date_str = booking.date.strftime("%B %d, %Y")

            # Send SMS
            if sms_enabled and client.reminder_preference == "phone":
                sms_text = build_reminder_sms(client.name, service.name, time_str)
                success = send_sms(client.phone, sms_text)
                log = ReminderLog(
                    booking_id=booking.id,
                    type="sms",
                    status="sent" if success else "failed",
                    sent_at=datetime.utcnow() if success else None,
                    error_message=None if success else "SMS send failed",
                )
                db.session.add(log)

            # Send email
            if email_enabled and client.reminder_preference == "email":
                html = build_reminder_email(client.name, service.name, date_str, time_str)
                success = send_email(
                    client.email,
                    f"Reminder: Your HoPono appointment on {date_str}",
                    html,
                )
                log = ReminderLog(
                    booking_id=booking.id,
                    type="email",
                    status="sent" if success else "failed",
                    sent_at=datetime.utcnow() if success else None,
                    error_message=None if success else "Email send failed",
                )
                db.session.add(log)

        db.session.commit()
        logger.info("Reminder check completed. Processed %d bookings.", len(bookings))
