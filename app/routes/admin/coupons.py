from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.extensions import db
from app.models.coupon import Coupon

admin_coupons_bp = Blueprint("admin_coupons", __name__)


@admin_coupons_bp.route("/")
@login_required
def list_coupons():
    coupons = Coupon.query.order_by(Coupon.created_at.desc()).all()
    return render_template("admin/coupons.html", coupons=coupons)


@admin_coupons_bp.route("/new", methods=["POST"])
@login_required
def create_coupon():
    code = request.form.get("code", "").strip().upper()
    discount_type = request.form.get("discount_type")
    discount_value = request.form.get("discount_value", type=float)
    valid_from = request.form.get("valid_from") or None
    valid_until = request.form.get("valid_until") or None
    max_uses = request.form.get("max_uses", type=int) or None

    if not all([code, discount_type, discount_value]):
        flash("Code, discount type, and value are required.", "error")
        return redirect(url_for("admin_coupons.list_coupons"))

    existing = Coupon.query.filter_by(code=code).first()
    if existing:
        flash("A coupon with this code already exists.", "error")
        return redirect(url_for("admin_coupons.list_coupons"))

    coupon = Coupon(
        code=code,
        discount_type=discount_type,
        discount_value=discount_value,
        valid_from=datetime.strptime(valid_from, "%Y-%m-%d").date() if valid_from else None,
        valid_until=datetime.strptime(valid_until, "%Y-%m-%d").date() if valid_until else None,
        max_uses=max_uses,
    )
    db.session.add(coupon)
    db.session.commit()
    flash("Coupon created.", "success")
    return redirect(url_for("admin_coupons.list_coupons"))


@admin_coupons_bp.route("/<int:coupon_id>/toggle", methods=["POST"])
@login_required
def toggle_coupon(coupon_id):
    coupon = Coupon.query.get_or_404(coupon_id)
    coupon.is_active = not coupon.is_active
    db.session.commit()
    flash(f"Coupon {'activated' if coupon.is_active else 'deactivated'}.", "success")
    return redirect(url_for("admin_coupons.list_coupons"))
