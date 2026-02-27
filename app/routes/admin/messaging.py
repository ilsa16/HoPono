from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required
from app.services.reminder_service import send_sms, send_email

admin_messaging_bp = Blueprint("admin_messaging", __name__)


@admin_messaging_bp.route("/")
@login_required
def messaging_page():
    return render_template("admin/messaging.html")


@admin_messaging_bp.route("/send-test-sms", methods=["POST"])
@login_required
def send_test_sms():
    phone = request.form.get("phone", "").strip()
    message = request.form.get("message", "").strip()

    if not phone or not message:
        flash("Phone number and message are required.", "error")
        return redirect(url_for("admin_messaging.messaging_page"))

    success = send_sms(phone, message)
    if success:
        flash(f"Test SMS sent successfully to {phone}.", "success")
    else:
        flash(f"Failed to send SMS to {phone}. Check server logs for details.", "error")

    return redirect(url_for("admin_messaging.messaging_page"))


@admin_messaging_bp.route("/send-test-email", methods=["POST"])
@login_required
def send_test_email():
    to_email = request.form.get("to_email", "").strip()
    subject = request.form.get("subject", "").strip()
    html_content = request.form.get("html_content", "").strip()

    if not to_email or not subject or not html_content:
        flash("Email address, subject, and message are all required.", "error")
        return redirect(url_for("admin_messaging.messaging_page"))

    success = send_email(to_email, subject, html_content)
    if success:
        flash(f"Test email sent successfully to {to_email}.", "success")
    else:
        flash(f"Failed to send email to {to_email}. Check server logs for details.", "error")

    return redirect(url_for("admin_messaging.messaging_page"))
