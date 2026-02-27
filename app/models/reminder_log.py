from datetime import datetime
from app.extensions import db


class ReminderLog(db.Model):
    __tablename__ = "reminder_log"

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id"), nullable=False)
    type = db.Column(db.String(10), nullable=False)  # 'sms' or 'email'
    status = db.Column(db.String(20), nullable=False)  # 'sent', 'failed', 'pending'
    sent_at = db.Column(db.DateTime)
    error_message = db.Column(db.Text)
