import logging
import os
from flask import Flask, abort, render_template, request
from werkzeug.middleware.proxy_fix import ProxyFix
from .config import config
from .extensions import db, migrate, login_manager, csrf, limiter

logger = logging.getLogger(__name__)

_BLOCKED_PREFIXES = (
    "/wp-admin", "/wp-login", "/wp-content", "/wp-includes",
    "/wp-json", "/wp-cron", "/wp-config",
    "/xmlrpc.php", "/eval-stdin.php", "/wp-signup.php",
    "/phpmyadmin", "/pma", "/myadmin",
    "/administrator", "/admin.php",
    "/.env", "/.git", "/.svn", "/.htaccess", "/.htpasswd",
    "/cgi-bin", "/shell", "/config.php",
    "/vendor/phpunit", "/solr", "/actuator",
)

_BLOCKED_EXTENSIONS = (".php", ".asp", ".aspx", ".jsp", ".cgi")


def _is_probe(path):
    lower = path.lower()
    if any(lower.startswith(p) for p in _BLOCKED_PREFIXES):
        return True
    if any(lower.endswith(ext) for ext in _BLOCKED_EXTENSIONS):
        if lower not in ("/favicon.ico",):
            return True
    return False


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "default")

    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    @app.before_request
    def block_probes():
        if _is_probe(request.path):
            logger.warning("Blocked probe: %s from %s", request.path, request.remote_addr)
            abort(403)

    @app.errorhandler(403)
    def forbidden_handler(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(429)
    def ratelimit_handler(e):
        return render_template("errors/429.html"), 429

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
    from .routes.admin.devtools import admin_devtools_bp

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
    app.register_blueprint(admin_devtools_bp, url_prefix="/admin/devtools")

    # Import models so they're registered with SQLAlchemy
    from . import models  # noqa: F401

    if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        from .tasks.scheduler import init_scheduler
        init_scheduler(app)

    return app
