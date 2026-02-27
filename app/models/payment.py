from datetime import datetime
from app.extensions import db


class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id"), unique=True, nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False)
    amount_eur = db.Column(db.Numeric(6, 2), nullable=False)
    method = db.Column(db.String(20), nullable=False)  # revolut, cash, quickpay, other
    notes = db.Column(db.Text)
    paid_at = db.Column(db.DateTime, default=datetime.utcnow)
    recorded_by = db.Column(db.Integer, db.ForeignKey("admin_users.id"))
