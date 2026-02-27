from datetime import date, timedelta
from flask import Blueprint, render_template
from flask_login import login_required
from app.extensions import db
from app.models.booking import Booking
from app.models.client import Client

admin_dashboard_bp = Blueprint("admin_dashboard", __name__)


@admin_dashboard_bp.route("/")
@login_required
def dashboard():
    today = date.today()
    todays_bookings = (
        Booking.query.filter_by(date=today)
        .filter(Booking.status.in_(["confirmed", "completed"]))
        .order_by(Booking.start_time)
        .all()
    )

    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    weekly_count = (
        Booking.query.filter(
            Booking.date.between(week_start, week_end),
            Booking.status.in_(["confirmed", "completed"]),
        ).count()
    )

    total_clients = Client.query.count()

    upcoming_count = (
        Booking.query.filter(
            Booking.date >= today, Booking.status == "confirmed"
        ).count()
    )

    pending_bookings = (
        Booking.query.filter(
            Booking.date > today,
            Booking.status == "confirmed",
        )
        .order_by(Booking.date, Booking.start_time)
        .limit(10)
        .all()
    )

    return render_template(
        "admin/dashboard.html",
        todays_bookings=todays_bookings,
        weekly_count=weekly_count,
        total_clients=total_clients,
        upcoming_count=upcoming_count,
        pending_bookings=pending_bookings,
    )
