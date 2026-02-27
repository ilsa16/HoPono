from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from app.extensions import db
from app.models.service import Service
from app.models.booking import Booking
from app.models.client import Client
from app.models.coupon import Coupon
from app.services.slot_engine import get_available_slots
from app.services.booking_service import create_booking
from app.services.coupon_service import validate_coupon

booking_bp = Blueprint("booking", __name__)


@booking_bp.route("/")
def select_service():
    services = Service.query.filter_by(is_active=True).order_by(Service.sort_order).all()
    return render_template("booking/select_service.html", services=services)


@booking_bp.route("/slots")
def slots():
    service_id = request.args.get("service_id", type=int)
    date = request.args.get("date")
    if not service_id or not date:
        return jsonify({"error": "Missing service_id or date"}), 400

    available = get_available_slots(date, service_id)
    return jsonify({"slots": available})


@booking_bp.route("/confirm", methods=["POST"])
def confirm():
    try:
        booking = create_booking(
            service_id=request.form.get("service_id", type=int),
            date=request.form.get("date"),
            start_time=request.form.get("start_time"),
            client_name=request.form.get("name"),
            client_email=request.form.get("email"),
            client_phone=request.form.get("phone"),
            reminder_preference=request.form.get("reminder_preference", "both"),
            coupon_code=request.form.get("coupon_code"),
        )
        return redirect(url_for("booking.success", booking_id=booking.id))
    except ValueError as e:
        flash(str(e), "error")
        return redirect(url_for("booking.select_service"))


@booking_bp.route("/success/<int:booking_id>")
def success(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    return render_template("booking/confirmation.html", booking=booking)


@booking_bp.route("/validate-coupon", methods=["POST"])
def validate_coupon_route():
    code = request.json.get("code", "")
    service_id = request.json.get("service_id")
    result = validate_coupon(code, service_id)
    return jsonify(result)
