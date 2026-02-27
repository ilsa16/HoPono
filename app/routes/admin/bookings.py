from datetime import date, datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.extensions import db
from app.models.booking import Booking
from app.models.service import Service
from app.models.client import Client
from app.services.booking_service import create_booking
from app.services.slot_engine import get_available_slots

admin_bookings_bp = Blueprint("admin_bookings", __name__)


@admin_bookings_bp.route("/")
@login_required
def list_bookings():
    status_filter = request.args.get("status")
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    search = request.args.get("search", "").strip()

    query = Booking.query.join(Client).join(Service)

    if status_filter:
        query = query.filter(Booking.status == status_filter)
    if date_from:
        query = query.filter(Booking.date >= date_from)
    if date_to:
        query = query.filter(Booking.date <= date_to)
    if search:
        query = query.filter(
            db.or_(
                Client.name.ilike(f"%{search}%"),
                Client.email.ilike(f"%{search}%"),
                Client.phone.ilike(f"%{search}%"),
            )
        )

    bookings = query.order_by(Booking.date.desc(), Booking.start_time.desc()).all()
    return render_template("admin/bookings.html", bookings=bookings)


@admin_bookings_bp.route("/<int:booking_id>")
@login_required
def booking_detail(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    return render_template("admin/booking_detail.html", booking=booking)


@admin_bookings_bp.route("/new", methods=["GET", "POST"])
@login_required
def new_booking():
    if request.method == "POST":
        try:
            booking = create_booking(
                service_id=request.form.get("service_id", type=int),
                date=request.form.get("date"),
                start_time=request.form.get("start_time"),
                client_name=request.form.get("name"),
                client_email=request.form.get("email"),
                client_phone=request.form.get("phone"),
                reminder_preference=request.form.get("reminder_preference", "email"),
                source="manual",
            )
            flash("Booking created successfully.", "success")
            return redirect(url_for("admin_bookings.booking_detail", booking_id=booking.id))
        except ValueError as e:
            flash(str(e), "error")

    services = Service.query.filter_by(is_active=True).order_by(Service.sort_order).all()
    return render_template("admin/booking_new.html", services=services)


@admin_bookings_bp.route("/<int:booking_id>/status", methods=["POST"])
@login_required
def update_status(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    new_status = request.form.get("status")
    if new_status in ("confirmed", "cancelled", "completed", "no_show"):
        booking.status = new_status
        booking.updated_at = datetime.utcnow()
        db.session.commit()
        flash(f"Booking marked as {new_status}.", "success")
    return redirect(url_for("admin_bookings.booking_detail", booking_id=booking.id))
