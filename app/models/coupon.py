from datetime import datetime
from app.extensions import db


class Coupon(db.Model):
    __tablename__ = "coupons"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(30), unique=True, nullable=False)
    discount_type = db.Column(db.String(10), nullable=False)  # 'percent' or 'fixed'
    discount_value = db.Column(db.Numeric(6, 2), nullable=False)
    valid_from = db.Column(db.Date, nullable=True)
    valid_until = db.Column(db.Date, nullable=True)
    max_uses = db.Column(db.Integer, nullable=True)
    times_used = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
