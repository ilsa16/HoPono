from datetime import date, datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models.booking import Booking
from app.models.payment import Payment

admin_payments_bp = Blueprint("admin_payments", __name__)


@admin_payments_bp.route("/")
@login_required
def list_payments():
    view_date = request.args.get("date", date.today().isoformat())

    # Bookings for that date that are completed but have no payment recorded
    unpaid = (
        Booking.query.filter_by(date=view_date, status="completed")
        .outerjoin(Payment)
        .filter(Payment.id.is_(None))
        .all()
    )

    # Already paid bookings for that date
    paid = (
        Booking.query.filter_by(date=view_date)
        .join(Payment)
        .all()
    )

    return render_template(
        "admin/payments.html",
        unpaid=unpaid,
        paid=paid,
        view_date=view_date,
    )


@admin_payments_bp.route("/record", methods=["POST"])
@login_required
def record_payment():
    booking_id = request.form.get("booking_id", type=int)
    amount = request.form.get("amount", type=float)
    method = request.form.get("method")
    notes = request.form.get("notes", "").strip()

    if not all([booking_id, amount, method]):
        flash("Booking, amount, and method are required.", "error")
        return redirect(url_for("admin_payments.list_payments"))

    booking = Booking.query.get_or_404(booking_id)

    existing = Payment.query.filter_by(booking_id=booking_id).first()
    if existing:
        flash("Payment already recorded for this booking.", "error")
        return redirect(url_for("admin_payments.list_payments"))

    payment = Payment(
        booking_id=booking_id,
        client_id=booking.client_id,
        amount_eur=amount,
        method=method,
        notes=notes,
        recorded_by=current_user.id,
    )
    db.session.add(payment)
    db.session.commit()
    flash("Payment recorded.", "success")
    return redirect(url_for("admin_payments.list_payments", date=booking.date.isoformat()))
