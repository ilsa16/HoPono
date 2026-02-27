from datetime import datetime
from app.extensions import db


class AvailabilityWindow(db.Model):
    __tablename__ = "availability_windows"
    __table_args__ = (
        db.UniqueConstraint("date", "start_time", "end_time", name="uq_availability"),
    )

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
