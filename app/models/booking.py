import uuid
from datetime import datetime
from app.extensions import db


class Booking(db.Model):
    __tablename__ = "bookings"
    __table_args__ = (db.Index("ix_bookings_date_status", "date", "status"),)

    id = db.Column(db.Integer, primary_key=True)
    confirmation_token = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey("services.id"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    buffer_before = db.Column(db.Time, nullable=False)
    buffer_after = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="confirmed")
    coupon_id = db.Column(db.Integer, db.ForeignKey("coupons.id"), nullable=True)
    discount_amount = db.Column(db.Numeric(6, 2), nullable=True)
    source = db.Column(db.String(20), default="online")
    admin_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    payment = db.relationship("Payment", backref="booking", uselist=False)
    notes = db.relationship("ClientNote", backref="booking", lazy="dynamic")
    reminder_logs = db.relationship("ReminderLog", backref="booking", lazy="dynamic")
    coupon = db.relationship("Coupon", backref="bookings")
