import os
from flask import Flask
from .config import config
from .extensions import db, migrate, login_manager, csrf


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "default")

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Register blueprints
    from .routes.public import public_bp
    from .routes.booking import booking_bp
    from .routes.admin.auth import admin_auth_bp
    from .routes.admin.dashboard import admin_dashboard_bp
    from .routes.admin.bookings import admin_bookings_bp
    from .routes.admin.clients import admin_clients_bp
    from .routes.admin.availability import admin_availability_bp
    from .routes.admin.payments import admin_payments_bp
    from .routes.admin.coupons import admin_coupons_bp
    from .routes.admin.settings import admin_settings_bp
    from .routes.admin.messaging import admin_messaging_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(booking_bp, url_prefix="/book")
    app.register_blueprint(admin_auth_bp, url_prefix="/admin")
    app.register_blueprint(admin_dashboard_bp, url_prefix="/admin")
    app.register_blueprint(admin_bookings_bp, url_prefix="/admin/bookings")
    app.register_blueprint(admin_clients_bp, url_prefix="/admin/clients")
    app.register_blueprint(admin_availability_bp, url_prefix="/admin/availability")
    app.register_blueprint(admin_payments_bp, url_prefix="/admin/payments")
    app.register_blueprint(admin_coupons_bp, url_prefix="/admin/coupons")
    app.register_blueprint(admin_settings_bp, url_prefix="/admin/settings")
    app.register_blueprint(admin_messaging_bp, url_prefix="/admin/messaging")

    # Import models so they're registered with SQLAlchemy
    from . import models  # noqa: F401

    return app
