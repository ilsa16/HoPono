import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def send_sms(phone, message):
    """Send an SMS via Telnyx."""
    api_key = os.environ.get("TELNYX_API_KEY")
    from_number = os.environ.get("TELNYX_PHONE_NUMBER")

    if not api_key or not from_number:
        logger.warning("Telnyx not configured. Skipping SMS to %s", phone)
        return False

    try:
        import telnyx
        telnyx.api_key = api_key
        telnyx.Message.create(
            from_=from_number,
            to=phone,
            text=message,
        )
        return True
    except Exception as e:
        logger.error("Failed to send SMS to %s: %s", phone, e)
        return False


def send_email(to_email, subject, html_content):
    """Send an email via SendGrid."""
    api_key = os.environ.get("SENDGRID_API_KEY")
    from_email = os.environ.get("SENDGRID_FROM_EMAIL", "bookings@hoponomassage.com")

    if not api_key:
        logger.warning("SendGrid not configured. Skipping email to %s", to_email)
        return False

    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail

        message = Mail(
            from_email=from_email,
            to_emails=to_email,
            subject=subject,
            html_content=html_content,
        )
        sg = SendGridAPIClient(api_key)
        sg.send(message)
        return True
    except Exception as e:
        logger.error("Failed to send email to %s: %s", to_email, e)
        return False


def build_reminder_sms(client_name, service_name, booking_time):
    """Build SMS reminder text (keep under 160 chars)."""
    return (
        f"Hi {client_name}! Reminder: your {service_name} at HoPono is "
        f"tomorrow at {booking_time}. Questions? Call +35796537959. See you soon!"
    )


def build_reminder_email(client_name, service_name, booking_date, booking_time):
    """Build HTML email for appointment reminder."""
    return f"""
    <div style="font-family: 'Open Sans', sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background-color: #1e73be; padding: 30px; text-align: center;">
            <h1 style="color: white; font-family: 'Raleway', sans-serif; margin: 0;">
                HoPono Massage
            </h1>
        </div>
        <div style="padding: 30px; background-color: #f9fafb;">
            <h2 style="color: #1e73be;">Appointment Reminder</h2>
            <p>Hi {client_name},</p>
            <p>This is a friendly reminder about your upcoming appointment:</p>
            <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <p><strong>Service:</strong> {service_name}</p>
                <p><strong>Date:</strong> {booking_date}</p>
                <p><strong>Time:</strong> {booking_time}</p>
            </div>
            <p>If you need to reschedule or have any questions, please contact us at
            <a href="tel:+35796537959">+357 96 537 959</a>.</p>
            <p>We look forward to seeing you!</p>
            <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
                &mdash; The HoPono Massage Team
            </p>
        </div>
    </div>
    """
