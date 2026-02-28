# HoPono Massage Studio — Booking System

## Overview
A Flask-based booking and management system for HoPono Massage, a massage therapy business in Nicosia. Features a public-facing website with inline booking flow on the homepage, and an admin panel for business management.

## Architecture
- **Framework**: Flask (Python)
- **Database**: PostgreSQL (Replit-managed, via `DATABASE_URL`)
- **ORM**: SQLAlchemy + Flask-Migrate (Alembic)
- **Auth**: Flask-Login (admin panel)
- **Frontend**: Jinja2 + Tailwind CSS (CDN) + Alpine.js
- **Theme**: Dark luxury aesthetic (charcoal #0c1117 backgrounds, #161b22 surface cards, gold #dba11d accents, white text)
- **Animations**: Scroll-triggered fade-up/fade-in via Intersection Observer (classes in base.html)
- **Imagery**: Stock photography backgrounds on hero sections (hero_bg.jpg, about_massage.jpg, services_header.jpg, experience_atmosphere.jpg, contact_bg.jpg in app/static/images/); AI-generated per-service portrait images in app/static/images/services/
- **Treatment Selector**: Two-state product configurator on homepage and /book page:
  - State A (Grid Browse): 2x3 card grid; clicking a card enters State B
  - State B (Focus Mode): 3-column layout — portrait image (left), service details/description/metadata/CTA (center), compact service rail (right). Service rail allows switching the focused service with crossfade. "All treatments" back-link returns to State A. On mobile, columns stack vertically.
  - Mobile: Swipeable horizontal card carousel (CSS scroll-snap, no external library); dots + arrows + counter navigation; cards show image, details, price, Continue CTA
  - Alpine.js state: `focusMode`, `focusedServiceId`, `currentCardIndex`, `allServices[]` array populated from Jinja `{{ services }}`, computed `focusedService` getter, `enterFocusMode()`, `switchFocusedService()`, `confirmFocusSelection()`, `handleCarouselScroll()`, `scrollToCard()`, `scrollCarousel()` methods
  - Service model fields: `image_filename`, `best_for`, `pressure_level` (added via migration)
- **CSRF**: Flask-WTF CSRFProtect (form tokens + X-CSRFToken header for AJAX)
- **Rate Limiting**: Flask-Limiter (in-memory, 60/min global; 5/min login; 5/min+30/hr booking; 10/min coupon validation)
- **Brute Force Protection**: IP-based lockout after 5 failed admin login attempts within 15 minutes
- **Bot Protection**: Honeypot field + timing-based detection (< 3s or > 2hr = bot) on booking forms
- **Developer Tools**: Separate password gate behind admin auth (double authentication layer); password from `DEVTOOLS_PASSWORD` env var
- **Session Security**: HttpOnly cookies, SameSite=Lax, 1-hour session lifetime, Secure flag in production
- **Secret Key**: Required from `SECRET_KEY` env var (no hardcoded fallback); app refuses to start without it
- **Input Validation**: Server-side phone (+country code, 7-15 digits), email format, name length (2-100) validation in booking_service
- **Probe Blocker**: WordPress/CMS/PHP paths blocked at `before_request` level; custom 403 page
- **HTML Sanitization**: Devtools messaging strips script/iframe/event handler tags before sending emails
- **Proxy Support**: ProxyFix middleware for real client IP behind reverse proxies
- **Reminder Scheduler**: APScheduler (BackgroundScheduler) runs every 15 minutes, uses Cyprus timezone (Europe/Nicosia) for all time calculations, initialized in `create_app()` with double-init guard
- **GDPR Compliance**: Marketing consent checkbox (optional, separate from required data processing consent), privacy policy page at `/privacy`, consent status visible in admin client detail
- **Privacy Policy**: 12-section policy covering data controller, data collected, purpose, legal basis (Art. 6), marketing consent, retention (24mo), client rights, third parties (Brevo/Send.to), cookies, security, changes, complaints (Cyprus DPA)

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
      availability.py   # Schedule/availability windows + JSON API
      payments.py       # Payment tracking
      coupons.py        # Coupon management
      settings.py       # App settings
      devtools.py       # Password-gated developer tools section
      messaging.py      # Test SMS/Email sending (behind devtools gate)
  services/
    booking_service.py  # Booking creation logic
    slot_engine.py      # Available slot calculation
    coupon_service.py   # Coupon validation
    reminder_service.py # SMS/Email reminder sending
    calendar_service.py # ICS file generation + Google/Outlook calendar URLs
  tasks/
    scheduler.py        # APScheduler setup
    send_reminders.py   # Reminder job
  templates/            # Jinja2 HTML templates
migrations/             # Alembic migration files
```

## Key URLs
### Public
- `/` — Homepage with inline 3-step booking flow
- `/services` — Service listing
- `/book` — Standalone booking flow (fallback)
- `/book/slots?service_id=X&date=YYYY-MM-DD` — Available slots API
- `/book/calendar/<booking_id>.ics` — Download ICS calendar file for a booking
- `/book/success/<booking_id>` — Booking confirmation with Add to Calendar buttons

### Admin
- `/admin/login` — Admin login
- `/admin/dashboard` — Dashboard with stats
- `/admin/availability/` — Mobile-first weekly availability manager
- `/admin/availability/api/week?start=YYYY-MM-DD` — Week availability JSON
- `/admin/availability/api/add` — Add availability window (POST JSON)
- `/admin/availability/api/delete` — Delete window (POST JSON)
- `/admin/availability/api/clear-day` — Clear all windows for a day (POST JSON)
- `/admin/availability/api/copy-week` — Copy week's availability (POST JSON)
- `/admin/availability/api/month?year=YYYY&month=M` — Month availability JSON (count + windows per day)
- `/admin/availability/api/copy-month` — Copy entire month's availability (POST JSON)
- `/admin/devtools/` — Developer Tools hub (password-gated)
- `/admin/messaging` — Test SMS and email sending (requires devtools access)

## Environment Variables
- `DATABASE_URL` — PostgreSQL connection string (auto-set by Replit)
- `SECRET_KEY` — Flask session secret
- `FLASK_ENV` — development/production
- `ADMIN_USERNAME` / `ADMIN_PASSWORD` — Used by seed.py
- `SENDTO_API_KEY` — Send.to (sms.to) API key for SMS reminders (sender_id: "HoPono")
- `BREVO_API_KEY` — Brevo API key for transactional email reminders
- `BREVO_FROM_EMAIL` — Optional sender email (default: bookings@hoponomassage.com)

## Running
The app runs via `flask db upgrade && python run.py` on port 5000. Database migrations auto-run on startup.
