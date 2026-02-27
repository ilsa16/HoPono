import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///hopono.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_size": 5,
        "max_overflow": 10,
    }

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = 3600

    TELNYX_API_KEY = os.environ.get("TELNYX_API_KEY")
    TELNYX_PHONE_NUMBER = os.environ.get("TELNYX_PHONE_NUMBER")

    SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")
    SENDGRID_FROM_EMAIL = os.environ.get(
        "SENDGRID_FROM_EMAIL", "bookings@hoponomassage.com"
    )

    @staticmethod
    def init_app(app):
        if not app.config.get("SECRET_KEY"):
            raise RuntimeError(
                "SECRET_KEY environment variable is not set. "
                "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )


class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True


class TestConfig(Config):
    TESTING = True
    SECRET_KEY = "test-secret-key-not-for-production"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestConfig,
    "default": DevelopmentConfig,
}
