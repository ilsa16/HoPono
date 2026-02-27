from app.extensions import db


class Service(db.Model):
    __tablename__ = "services"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    subtitle = db.Column(db.String(120))
    description = db.Column(db.Text)
    duration_minutes = db.Column(db.Integer, nullable=False)
    price_eur = db.Column(db.Numeric(6, 2), nullable=False)
    is_couples = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)

    bookings = db.relationship("Booking", backref="service", lazy="dynamic")
