from datetime import date
from app.extensions import db
from app.models.coupon import Coupon
from app.models.service import Service


def validate_coupon(code, service_id=None):
    """
    Validate a coupon code and return discount details.

    Returns dict with keys: valid, message, discount_amount, coupon_id
    """
    if not code:
        return {"valid": False, "message": "No coupon code provided."}

    coupon = Coupon.query.filter_by(code=code.upper().strip()).first()
    if not coupon:
        return {"valid": False, "message": "Invalid coupon code."}

    if not coupon.is_active:
        return {"valid": False, "message": "This coupon is no longer active."}

    today = date.today()
    if coupon.valid_from and today < coupon.valid_from:
        return {"valid": False, "message": "This coupon is not yet valid."}

    if coupon.valid_until and today > coupon.valid_until:
        return {"valid": False, "message": "This coupon has expired."}

    if coupon.max_uses and coupon.times_used >= coupon.max_uses:
        return {"valid": False, "message": "This coupon has reached its usage limit."}

    # Calculate discount amount
    discount_amount = 0
    if service_id:
        service = db.session.get(Service, service_id)
        if service:
            if coupon.discount_type == "percent":
                discount_amount = float(service.price_eur) * float(coupon.discount_value) / 100
            else:  # fixed
                discount_amount = min(float(coupon.discount_value), float(service.price_eur))

    return {
        "valid": True,
        "message": f"Coupon applied! You save \u20ac{discount_amount:.2f}.",
        "discount_amount": discount_amount,
        "coupon_id": coupon.id,
        "discount_type": coupon.discount_type,
        "discount_value": float(coupon.discount_value),
    }


def apply_coupon(code):
    """Increment the usage counter for a coupon."""
    coupon = Coupon.query.filter_by(code=code.upper().strip()).first()
    if coupon:
        coupon.times_used += 1
        db.session.flush()
