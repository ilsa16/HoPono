from datetime import datetime
from app.extensions import db


class Client(db.Model):
    __tablename__ = "clients"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    reminder_preference = db.Column(db.String(10), nullable=False, default="email")
    gdpr_consent = db.Column(db.Boolean, nullable=False, default=False)
    gdpr_consented_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    bookings = db.relationship("Booking", backref="client", lazy="dynamic")
    notes = db.relationship("ClientNote", backref="client", lazy="dynamic")
    payments = db.relationship("Payment", backref="client", lazy="dynamic")
