from datetime import datetime, timedelta
from app.extensions import db
from app.models.booking import Booking
from app.models.client import Client
from app.models.service import Service
from app.models.settings import Setting
from app.services.slot_engine import get_available_slots
from app.services.coupon_service import validate_coupon, apply_coupon


def _get_buffer_minutes():
    setting = db.session.get(Setting, "buffer_minutes")
    return int(setting.value) if setting else 30


def create_booking(
    service_id,
    date,
    start_time,
    client_name,
    client_email,
    client_phone,
    reminder_preference="email",
    coupon_code=None,
    source="online",
):
    """
    Create a new booking, handling client creation/lookup, slot validation,
    and coupon application.

    Raises ValueError if the slot is unavailable or inputs are invalid.
    """
    service = db.session.get(Service, service_id)
    if not service:
        raise ValueError("Invalid service selected.")

    # Verify slot is still available (race condition guard)
    available = get_available_slots(date, service_id)
    if start_time not in available:
        raise ValueError("This time slot is no longer available. Please choose another.")

    # Find or create client
    client = Client.query.filter_by(email=client_email.lower().strip()).first()
    if client:
        # Update info for returning client
        client.name = client_name
        client.phone = client_phone
        client.reminder_preference = reminder_preference
        client.updated_at = datetime.utcnow()
    else:
        client = Client(
            name=client_name,
            email=client_email.lower().strip(),
            phone=client_phone,
            reminder_preference=reminder_preference,
            gdpr_consent=True,
            gdpr_consented_at=datetime.utcnow(),
        )
        db.session.add(client)
        db.session.flush()  # Get client.id

    # Calculate times
    buffer_mins = _get_buffer_minutes()
    start_dt = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
    end_dt = start_dt + timedelta(minutes=service.duration_minutes)
    buffer_before_dt = start_dt - timedelta(minutes=buffer_mins)
    buffer_after_dt = end_dt + timedelta(minutes=buffer_mins)

    # Handle coupon
    coupon_id = None
    discount_amount = None
    if coupon_code:
        result = validate_coupon(coupon_code, service_id)
        if result["valid"]:
            coupon_id = result["coupon_id"]
            discount_amount = result["discount_amount"]
            apply_coupon(coupon_code)

    booking = Booking(
        client_id=client.id,
        service_id=service_id,
        date=datetime.strptime(date, "%Y-%m-%d").date(),
        start_time=start_dt.time(),
        end_time=end_dt.time(),
        buffer_before=buffer_before_dt.time(),
        buffer_after=buffer_after_dt.time(),
        status="confirmed",
        coupon_id=coupon_id,
        discount_amount=discount_amount,
        source=source,
    )
    db.session.add(booking)
    db.session.commit()

    return booking
