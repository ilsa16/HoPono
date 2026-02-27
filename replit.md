# HoPono Massage Studio — Booking System

## Overview
A Flask-based booking and management system for HoPono Massage, a massage therapy business in Nicosia. Features a public-facing website with online booking and an admin panel for business management.

## Architecture
- **Framework**: Flask (Python)
- **Database**: PostgreSQL (Replit-managed, via `DATABASE_URL`)
- **ORM**: SQLAlchemy + Flask-Migrate (Alembic)
- **Auth**: Flask-Login (admin panel)
- **Templates**: Jinja2 + Tailwind CSS (CDN)

## Project Structure
```
run.py                  # App entrypoint (port 5000)
seed.py                 # Seeds admin user, services, and default settings
app/
  __init__.py           # create_app() factory
  config.py             # Config classes (dev/prod/test)
  extensions.py         # Flask extensions (db, migrate, login_manager, csrf)
  models/               # SQLAlchemy models
    user.py             # AdminUser
    service.py          # Massage services
    booking.py          # Bookings
    client.py           # Clients
    availability.py     # AvailabilityWindow
    payment.py          # Payment records
    coupon.py           # Discount coupons
    note.py             # Client notes
    reminder_log.py     # Reminder send log
    settings.py         # Key-value settings
  routes/
    public.py           # Public pages (home, about, services, contact)
    booking.py          # Booking flow (select service, pick slot, confirm)
    admin/              # Admin panel blueprints
      auth.py           # Login/logout
      dashboard.py      # Dashboard with stats
      bookings.py       # Booking management
      clients.py        # Client management
      availability.py   # Schedule/availability windows
      payments.py       # Payment tracking
      coupons.py        # Coupon management
      settings.py       # App settings
  services/
    booking_service.py  # Booking creation logic
    slot_engine.py      # Available slot calculation
    coupon_service.py   # Coupon validation
    reminder_service.py # SMS/Email reminder sending
  tasks/
    scheduler.py        # APScheduler setup
    send_reminders.py   # Reminder job
  templates/            # Jinja2 HTML templates
migrations/             # Alembic migration files
```

## Key URLs
- `/` — Public homepage
- `/services` — Service listing
- `/book` — Booking flow
- `/admin` — Admin login
- `/admin/dashboard` — Admin dashboard

## Environment Variables
- `DATABASE_URL` — PostgreSQL connection string (auto-set by Replit)
- `SECRET_KEY` — Flask session secret
- `FLASK_ENV` — development/production
- `ADMIN_USERNAME` / `ADMIN_PASSWORD` — Used by seed.py
- `TELNYX_API_KEY` / `TELNYX_PHONE_NUMBER` — Optional, for SMS reminders
- `SENDGRID_API_KEY` / `SENDGRID_FROM_EMAIL` — Optional, for email reminders

## Running
The app runs via `python run.py` on port 5000. Database migrations are managed with Flask-Migrate (`flask db migrate` / `flask db upgrade`).
