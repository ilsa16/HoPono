# HoPono Massage Studio — Booking System

## Overview
A Flask/PostgreSQL booking and management system for HoPono Massage Studio (Nicosia, Cyprus). Features a public-facing dark-luxury-themed website with an inline booking flow and a comprehensive admin panel for business management.

## Quick Start
```bash
# Required environment variables
export SECRET_KEY="<random-hex-string>"
export ADMIN_USERNAME="hopono"
export ADMIN_PASSWORD="<your-admin-password>"
export DATABASE_URL="postgresql://..."

# Optional (for SMS/email reminders)
export SENDTO_API_KEY="<send.to-api-key>"
export BREVO_SMTP_LOGIN="<brevo-smtp-login>"
export BREVO_API_KEY="<brevo-api-key>"
export BREVO_FROM_EMAIL="noreply@hoponomassage.com"

# Run
flask db upgrade && python run.py
```

## Architecture
- **Backend**: Flask + SQLAlchemy + Flask-Migrate (Alembic)
- **Database**: PostgreSQL
- **Frontend**: Jinja2 templates + Tailwind CSS (CDN) + Alpine.js
- **SMS**: Send.to (sms.to) REST API
- **Email**: Brevo SMTP relay
- **Scheduler**: APScheduler (BackgroundScheduler) for automated reminders

## Project Structure
```
run.py                  # Entrypoint (port 5000)
seed.py                 # Seeds admin user, services, default settings
app/
  __init__.py           # create_app() factory, probe blocker, admin reminder trigger
  config.py             # Config classes (dev/prod/test)
  extensions.py         # Flask extensions
  models/               # SQLAlchemy models (booking, client, service, etc.)
  routes/
    public.py           # Public pages
    booking.py          # Booking flow
    admin/              # Admin panel (auth, dashboard, bookings, clients, etc.)
  services/             # Business logic (booking, slots, coupons, reminders, calendar)
  tasks/
    scheduler.py        # APScheduler setup
    send_reminders.py   # Reminder job with fallback logic
  templates/            # Jinja2 HTML templates
migrations/             # Alembic migrations
```

## Key Patterns

### Reminder System
- Runs every 15 minutes via APScheduler + immediate check on app startup
- Also triggers on any admin page visit (throttled to once per 5 minutes, runs in background thread)
- Wide ±12h window: sends reminders for bookings between now and now+36 hours
- Fallback: if preferred channel (SMS/email) fails or is disabled, tries the other
- Duplicate protection: threading lock prevents concurrent checks; DB unique constraint on `(booking_id, status)` prevents duplicate sends
- Designed for Autoscale deployments where the app may sleep

### Security
- CSRF on all forms (Flask-WTF)
- Rate limiting (Flask-Limiter): login, booking, coupon validation
- Brute force lockout: IP-based after 5 failed logins within 15 minutes
- Bot protection: honeypot field + timing check on booking forms
- WordPress/CMS probe blocking at before_request level
- HTML sanitization on admin messaging
- HttpOnly/SameSite/Secure cookies; 1-hour session lifetime

### Booking Flow
- 3-step inline flow on homepage: select service → pick date/time → enter details
- Treatment selector: grid browse mode and focus mode with service rail
- Mobile: swipeable card carousel with CSS scroll-snap
- Slot engine calculates available times from admin-defined availability windows
- Phone validation: `^\+\d{7,15}$`

### Admin Panel
- Dashboard with stats and pending bookings
- Bookings: list view + calendar view (Day/Week/Month)
- Availability: mobile-first weekly manager with month overview
- Client management with notes and GDPR consent tracking
- Payment tracking, coupon management
- Settings for reminder timing and channel toggles
- Developer tools section (double password gate)

## Environment Variables
| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | Flask session secret |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `ADMIN_USERNAME` | For seed | Admin username (default: hopono) |
| `ADMIN_PASSWORD` | For seed | Admin password (no default) |
| `SENDTO_API_KEY` | No | Send.to API key for SMS |
| `BREVO_SMTP_LOGIN` | No | Brevo SMTP login for email |
| `BREVO_API_KEY` | No | Brevo API key (used as SMTP password) |
| `BREVO_FROM_EMAIL` | No | Sender email (default: noreply@hoponomassage.com) |
| `DEVTOOLS_PASSWORD` | No | Password for admin developer tools section |

## Commands
- `flask db upgrade && python run.py` — Start the app (auto-runs migrations)
- `python seed.py` — Seed admin user, services, and default settings
- `flask db migrate -m "description"` — Generate a new migration
