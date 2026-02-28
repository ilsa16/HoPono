from datetime import date, datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, Response, jsonify
from flask_login import login_required
from app.extensions import db
from app.models.booking import Booking
from app.models.service import Service
from app.models.client import Client
from app.services.booking_service import create_booking
from app.services.slot_engine import get_available_slots

admin_bookings_bp = Blueprint("admin_bookings", __name__)


def _filtered_bookings_query():
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

    return query.order_by(Booking.date.desc(), Booking.start_time.desc())


@admin_bookings_bp.route("/")
@login_required
def list_bookings():
    bookings = _filtered_bookings_query().all()
    return render_template("admin/bookings.html", bookings=bookings)


@admin_bookings_bp.route("/export.ics")
@login_required
def export_ics():
    bookings = _filtered_bookings_query().all()

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//HoPono Massage//Booking Export//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-TIMEZONE:Europe/Nicosia",
        "BEGIN:VTIMEZONE",
        "TZID:Europe/Nicosia",
        "BEGIN:STANDARD",
        "DTSTART:19701025T040000",
        "RRULE:FREQ=YEARLY;BYDAY=-1SU;BYMONTH=10",
        "TZOFFSETFROM:+0300",
        "TZOFFSETTO:+0200",
        "TZNAME:EET",
        "END:STANDARD",
        "BEGIN:DAYLIGHT",
        "DTSTART:19700329T030000",
        "RRULE:FREQ=YEARLY;BYDAY=-1SU;BYMONTH=3",
        "TZOFFSETFROM:+0200",
        "TZOFFSETTO:+0300",
        "TZNAME:EEST",
        "END:DAYLIGHT",
        "END:VTIMEZONE",
    ]

    for b in bookings:
        client = b.client
        service = b.service
        dt_start = f"{b.date.strftime('%Y%m%d')}T{b.start_time.strftime('%H%M%S')}"
        dt_end = f"{b.date.strftime('%Y%m%d')}T{b.end_time.strftime('%H%M%S')}"
        summary = _ics_escape(f"HoPono: {service.name} - {client.name}")
        description = _ics_escape(
            f"Client: {client.name}\\n"
            f"Phone: {client.phone or 'N/A'}\\n"
            f"Email: {client.email or 'N/A'}\\n"
            f"Service: {service.name} ({service.duration_minutes}min)\\n"
            f"Price: €{service.price_eur:.2f}\\n"
            f"Status: {b.status.capitalize()}"
        )
        uid = f"hopono-booking-{b.id}@hopono.com"

        dtstamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

        lines.extend([
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{dtstamp}",
            f"DTSTART;TZID=Europe/Nicosia:{dt_start}",
            f"DTEND;TZID=Europe/Nicosia:{dt_end}",
            _ics_fold(f"SUMMARY:{summary}"),
            _ics_fold(f"DESCRIPTION:{description}"),
            _ics_fold(f"LOCATION:HoPono Massage Studio\\, Nicosia\\, Cyprus"),
            "STATUS:CONFIRMED",
            "END:VEVENT",
        ])

    lines.append("END:VCALENDAR")

    ics_content = "\r\n".join(lines) + "\r\n"

    return Response(
        ics_content,
        mimetype="text/calendar",
        headers={"Content-Disposition": "attachment; filename=hopono_bookings.ics"},
    )


def _ics_escape(text):
    text = text.replace("\\", "\\\\")
    text = text.replace(",", "\\,")
    text = text.replace(";", "\\;")
    return text


def _ics_fold(line):
    result = []
    while len(line.encode("utf-8")) > 75:
        cut = 75
        while len(line[:cut].encode("utf-8")) > 75:
            cut -= 1
        result.append(line[:cut])
        line = " " + line[cut:]
    result.append(line)
    return "\r\n".join(result)


@admin_bookings_bp.route("/calendar-data")
@login_required
def calendar_data():
    start_str = request.args.get("start")
    end_str = request.args.get("end")
    if not start_str or not end_str:
        return jsonify([])

    try:
        start_date = date.fromisoformat(start_str)
        end_date = date.fromisoformat(end_str)
    except ValueError:
        return jsonify([])

    bookings = (
        Booking.query.join(Client).join(Service)
        .filter(Booking.date >= start_date, Booking.date <= end_date)
        .order_by(Booking.date, Booking.start_time)
        .all()
    )

    status_colors = {
        "confirmed": "#3b82f6",
        "completed": "#22c55e",
        "cancelled": "#ef4444",
        "no_show": "#9ca3af",
    }

    events = []
    for b in bookings:
        events.append({
            "id": b.id,
            "title": b.client.name,
            "service": b.service.name,
            "date": b.date.isoformat(),
            "start": b.start_time.strftime("%H:%M"),
            "end": b.end_time.strftime("%H:%M"),
            "status": b.status,
            "color": status_colors.get(b.status, "#6b7280"),
        })

    return jsonify(events)


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
                client_phone=request.form.get("country_code", "+357") + request.form.get("phone", ""),
                reminder_preference=request.form.get("reminder_preference", "email"),
                source="manual",
                gdpr_consent=True,
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
