import os
import logging
import requests
from datetime import datetime

logger = logging.getLogger(__name__)


def send_sms(phone, message):
    """Send an SMS via Send.to (sms.to) REST API."""
    api_key = os.environ.get("SENDTO_API_KEY")

    if not api_key:
        logger.warning("Send.to not configured (SENDTO_API_KEY missing). Skipping SMS to %s", phone)
        return False

    try:
        resp = requests.post(
            "https://api.sms.to/sms/send",
            json={
                "message": message,
                "to": phone,
                "sender_id": "HoPono",
            },
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=15,
        )
        data = resp.json()
        if resp.ok and data.get("success"):
            logger.info("SMS sent to %s via Send.to (message_id: %s)", phone, data.get("message_id"))
            return True
        else:
            logger.error("Send.to SMS failed for %s: %s", phone, data)
            return False
    except Exception as e:
        logger.error("Failed to send SMS to %s via Send.to: %s", phone, e)
        return False


def send_email(to_email, subject, html_content):
    """Send an email via Brevo (formerly Sendinblue) transactional email API."""
    api_key = os.environ.get("BREVO_API_KEY")
    from_email = os.environ.get("BREVO_FROM_EMAIL", "bookings@hoponomassage.com")

    if not api_key:
        logger.warning("Brevo not configured (BREVO_API_KEY missing). Skipping email to %s", to_email)
        return False

    try:
        import sib_api_v3_sdk
        from sib_api_v3_sdk.rest import ApiException

        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key["api-key"] = api_key

        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
            sib_api_v3_sdk.ApiClient(configuration)
        )

        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": to_email}],
            sender={"name": "HoPono Massage", "email": from_email},
            subject=subject,
            html_content=html_content,
        )

        api_response = api_instance.send_transac_email(send_smtp_email)
        logger.info("Email sent to %s via Brevo (message_id: %s)", to_email, api_response.message_id)
        return True
    except ApiException as e:
        logger.error("Brevo API error sending email to %s: %s", to_email, e)
        return False
    except Exception as e:
        logger.error("Failed to send email to %s via Brevo: %s", to_email, e)
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
    <div style="font-family: 'Helvetica Neue', Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #0c1117; border-radius: 16px; overflow: hidden;">
        <div style="background-color: #161b22; padding: 32px; text-align: center; border-bottom: 1px solid rgba(255,255,255,0.05);">
            <h1 style="color: #dba11d; font-family: Georgia, serif; margin: 0; font-size: 28px; font-weight: 400; letter-spacing: 1px;">
                HoPono Massage
            </h1>
            <p style="color: rgba(255,255,255,0.3); font-size: 12px; margin: 8px 0 0 0; text-transform: uppercase; letter-spacing: 2px;">
                Nicosia, Cyprus
            </p>
        </div>
        <div style="padding: 36px 32px;">
            <h2 style="color: #dba11d; font-size: 20px; font-weight: 500; margin: 0 0 20px 0;">
                Appointment Reminder
            </h2>
            <p style="color: rgba(255,255,255,0.7); font-size: 15px; line-height: 1.6; margin: 0 0 12px 0;">
                Hi {client_name},
            </p>
            <p style="color: rgba(255,255,255,0.5); font-size: 15px; line-height: 1.6; margin: 0 0 24px 0;">
                This is a friendly reminder about your upcoming appointment:
            </p>
            <div style="background-color: #161b22; padding: 24px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05); margin: 0 0 24px 0;">
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 8px 0; color: rgba(255,255,255,0.4); font-size: 14px; width: 80px;">Service</td>
                        <td style="padding: 8px 0; color: white; font-size: 14px; font-weight: 600;">{service_name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; color: rgba(255,255,255,0.4); font-size: 14px;">Date</td>
                        <td style="padding: 8px 0; color: white; font-size: 14px; font-weight: 600;">{booking_date}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; color: rgba(255,255,255,0.4); font-size: 14px;">Time</td>
                        <td style="padding: 8px 0; color: #dba11d; font-size: 14px; font-weight: 600;">{booking_time}</td>
                    </tr>
                </table>
            </div>
            <p style="color: rgba(255,255,255,0.5); font-size: 14px; line-height: 1.6; margin: 0 0 8px 0;">
                If you need to reschedule or have any questions, please contact us at
                <a href="tel:+35796537959" style="color: #dba11d; text-decoration: none;">+357 96 537 959</a>.
            </p>
            <p style="color: rgba(255,255,255,0.5); font-size: 14px; line-height: 1.6; margin: 0;">
                We look forward to seeing you!
            </p>
        </div>
        <div style="background-color: #161b22; padding: 20px 32px; text-align: center; border-top: 1px solid rgba(255,255,255,0.05);">
            <p style="color: rgba(255,255,255,0.2); font-size: 12px; margin: 0;">
                &copy; HoPono Massage Studio &middot; Nicosia, Cyprus
            </p>
        </div>
    </div>
    """
