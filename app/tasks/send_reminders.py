import logging
import threading
from datetime import datetime, timedelta
import pytz
from sqlalchemy.exc import IntegrityError
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

CYPRUS_TZ = pytz.timezone("Europe/Nicosia")
_check_lock = threading.Lock()


def _log_reminder(booking_id, rtype, success, error_msg=None):
    log = ReminderLog(
        booking_id=booking_id,
        type=rtype,
        status="sent" if success else "failed",
        sent_at=datetime.now(CYPRUS_TZ).replace(tzinfo=None) if success else None,
        error_message=None if success else (error_msg or f"{rtype} send failed"),
    )
    db.session.add(log)
    return log


def _try_sms(booking, client, service, time_str):
    sms_text = build_reminder_sms(client.name, service.name, time_str)
    logger.info("Sending SMS to %s for booking #%d", client.phone, booking.id)
    success = send_sms(client.phone, sms_text)
    _log_reminder(booking.id, "sms", success)
    logger.info("SMS for booking #%d: %s", booking.id, "sent" if success else "FAILED")
    return success


def _try_email(booking, client, service, time_str, date_str):
    html = build_reminder_email(client.name, service.name, date_str, time_str)
    logger.info("Sending email to %s for booking #%d", client.email, booking.id)
    success = send_email(
        client.email,
        f"Reminder: Your HoPono appointment on {date_str}",
        html,
    )
    _log_reminder(booking.id, "email", success)
    logger.info("Email for booking #%d: %s", booking.id, "sent" if success else "FAILED")
    return success


def _attempt_reminder(booking, client, service, time_str, date_str,
                      sms_enabled, email_enabled):
    pref = client.reminder_preference
    can_sms = sms_enabled and bool(client.phone)
    can_email = email_enabled and bool(client.email)

    if pref == "phone":
        if can_sms:
            if _try_sms(booking, client, service, time_str):
                return True
            logger.info("SMS failed for booking #%d, trying email fallback", booking.id)
        else:
            logger.info("SMS unavailable for booking #%d (enabled=%s, phone=%s), trying email",
                        booking.id, sms_enabled, bool(client.phone))
        if can_email:
            return _try_email(booking, client, service, time_str, date_str)
    elif pref == "email":
        if can_email:
            if _try_email(booking, client, service, time_str, date_str):
                return True
            logger.info("Email failed for booking #%d, trying SMS fallback", booking.id)
        else:
            logger.info("Email unavailable for booking #%d (enabled=%s, email=%s), trying SMS",
                        booking.id, email_enabled, bool(client.email))
        if can_sms:
            return _try_sms(booking, client, service, time_str)
    else:
        if can_email:
            return _try_email(booking, client, service, time_str, date_str)
        if can_sms:
            return _try_sms(booking, client, service, time_str)

    logger.warning("No channel available to send reminder for booking #%d", booking.id)
    return False


def check_and_send_reminders(app):
    if not _check_lock.acquire(blocking=False):
        logger.info("Reminder check already in progress, skipping")
        return
    try:
        _do_check_and_send(app)
    finally:
        _check_lock.release()


def _do_check_and_send(app):
    with app.app_context():
        setting = db.session.get(Setting, "reminder_hours_before")
        hours_before = int(setting.value) if setting else 24

        sms_setting = db.session.get(Setting, "sms_enabled")
        sms_enabled = sms_setting.value.lower() == "true" if sms_setting else True

        email_setting = db.session.get(Setting, "email_enabled")
        email_enabled = email_setting.value.lower() == "true" if email_setting else True

        now_cyprus = datetime.now(CYPRUS_TZ).replace(tzinfo=None)
        target = now_cyprus + timedelta(hours=hours_before)

        logger.info(
            "Reminder check running. Cyprus time: %s, target window end: %s, sms_enabled=%s, email_enabled=%s",
            now_cyprus.strftime("%Y-%m-%d %H:%M:%S"),
            target.strftime("%Y-%m-%d %H:%M:%S"),
            sms_enabled,
            email_enabled,
        )

        window_end = target + timedelta(hours=12)
        date_cursor = now_cyprus.date()
        dates_to_check = set()
        while date_cursor <= window_end.date():
            dates_to_check.add(date_cursor)
            date_cursor += timedelta(days=1)

        bookings = (
            Booking.query.filter(
                Booking.status == "confirmed",
                Booking.date.in_(list(dates_to_check)),
            )
            .all()
        )

        logger.info(
            "Found %d confirmed bookings on %s",
            len(bookings),
            ", ".join(d.isoformat() for d in sorted(dates_to_check)),
        )

        sent_count = 0
        for booking in bookings:
            booking_dt = datetime.combine(booking.date, booking.start_time)

            if not (now_cyprus < booking_dt <= window_end):
                logger.debug(
                    "Booking #%d at %s outside reminder window (%s to %s), skipping",
                    booking.id,
                    booking_dt.strftime("%Y-%m-%d %H:%M"),
                    now_cyprus.strftime("%Y-%m-%d %H:%M"),
                    window_end.strftime("%Y-%m-%d %H:%M"),
                )
                continue

            existing = ReminderLog.query.filter(
                ReminderLog.booking_id == booking.id,
                ReminderLog.status == "sent",
            ).first()
            if existing:
                logger.debug("Booking #%d already has a sent reminder, skipping", booking.id)
                continue

            client = booking.client
            service = booking.service
            time_str = booking.start_time.strftime("%H:%M")
            date_str = booking.date.strftime("%B %d, %Y")

            logger.info(
                "Processing reminder for booking #%d: %s, %s at %s, preference=%s",
                booking.id,
                client.name,
                service.name,
                time_str,
                client.reminder_preference,
            )

            success = _attempt_reminder(
                booking, client, service, time_str, date_str,
                sms_enabled, email_enabled,
            )
            if success:
                try:
                    db.session.commit()
                    sent_count += 1
                except IntegrityError:
                    db.session.rollback()
                    logger.info("Booking #%d reminder already sent (concurrent), skipping", booking.id)
            else:
                db.session.commit()

        logger.info("Reminder check completed. Processed %d bookings, sent %d reminders.", len(bookings), sent_count)
