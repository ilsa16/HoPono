"""Seed the database with the admin user and massage services."""
import os
from dotenv import load_dotenv

load_dotenv()

from app import create_app
from app.extensions import db
from app.models.user import AdminUser
from app.models.service import Service
from app.models.settings import Setting
from werkzeug.security import generate_password_hash


def seed():
    app = create_app()
    with app.app_context():
        # Create admin user
        username = os.environ.get("ADMIN_USERNAME", "admin")
        password = os.environ.get("ADMIN_PASSWORD", "changeme")

        if not AdminUser.query.filter_by(username=username).first():
            admin = AdminUser(
                username=username,
                password_hash=generate_password_hash(password),
            )
            db.session.add(admin)
            print(f"Admin user '{username}' created.")
        else:
            print(f"Admin user '{username}' already exists.")

        # Create services
        services = [
            {
                "name": "Bali Blossom",
                "subtitle": "Relaxing Massage",
                "description": (
                    "A soft and gentle treatment that blends the wisdom of Indian "
                    "Ayurveda with the precision of Chinese acupressure techniques. "
                    "This massage soothes the body and calms the mind, releasing "
                    "tension through flowing, rhythmic strokes."
                ),
                "duration_minutes": 60,
                "price_eur": 50.00,
                "is_couples": False,
                "sort_order": 1,
            },
            {
                "name": "The Dive",
                "subtitle": "Deep Tissue Massage",
                "description": (
                    "Using greater pressure through thumbs and elbows, this massage "
                    "targets deep muscle knots and chronic tension. Ideal for those "
                    "who prefer a firm touch and need relief from persistent aches."
                ),
                "duration_minutes": 60,
                "price_eur": 50.00,
                "is_couples": False,
                "sort_order": 2,
            },
            {
                "name": "Buddha's Touch",
                "subtitle": "Thai Massage",
                "description": (
                    "Based on the ancient principles of Sen lines, this massage "
                    "incorporates yoga-like stretches and rhythmic compression. "
                    "Performed without oils, it improves flexibility, relieves "
                    "tension, and restores energy flow."
                ),
                "duration_minutes": 60,
                "price_eur": 50.00,
                "is_couples": False,
                "sort_order": 3,
            },
            {
                "name": "The Cure",
                "subtitle": "Signature Mix",
                "description": (
                    "Our signature treatment targeting calves, lower back and neck. "
                    "A carefully crafted blend of Thai and deep tissue techniques "
                    "that addresses the most common areas of tension and pain."
                ),
                "duration_minutes": 60,
                "price_eur": 50.00,
                "is_couples": False,
                "sort_order": 4,
            },
            {
                "name": "Old School",
                "subtitle": "Cupping Therapy",
                "description": (
                    "A traditional healing method that uses suction cups to increase "
                    "blood flow, reduce inflammation, and promote natural healing. "
                    "This ancient technique helps relieve muscle tension and improve "
                    "overall circulation."
                ),
                "duration_minutes": 30,
                "price_eur": 30.00,
                "is_couples": False,
                "sort_order": 5,
            },
            {
                "name": "Couples' Massage",
                "subtitle": "Shared Experience",
                "description": (
                    "Share the gift of relaxation with someone special. Choose any "
                    "of our massage styles and enjoy simultaneous or sequential "
                    "sessions together. A perfect way to unwind as a pair."
                ),
                "duration_minutes": 60,
                "price_eur": 50.00,
                "is_couples": True,
                "sort_order": 6,
            },
        ]

        for s in services:
            if not Service.query.filter_by(name=s["name"]).first():
                service = Service(**s)
                db.session.add(service)
                print(f"Service '{s['name']}' created.")
            else:
                print(f"Service '{s['name']}' already exists.")

        # Create default settings
        defaults = {
            "reminder_hours_before": "24",
            "buffer_minutes": "30",
            "sms_enabled": "true",
            "email_enabled": "true",
        }
        for key, value in defaults.items():
            if not db.session.get(Setting, key):
                db.session.add(Setting(key=key, value=value))
                print(f"Setting '{key}' = '{value}' created.")

        db.session.commit()
        print("\nSeeding complete!")


if __name__ == "__main__":
    seed()
