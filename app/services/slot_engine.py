from datetime import datetime, date, time, timedelta
from app.extensions import db
from app.models.availability import AvailabilityWindow
from app.models.booking import Booking
from app.models.service import Service
from app.models.settings import Setting


def _time_to_minutes(t):
    """Convert a time object to minutes since midnight."""
    return t.hour * 60 + t.minute


def _minutes_to_time(minutes):
    """Convert minutes since midnight to a time object."""
    return time(minutes // 60, minutes % 60)


def _get_buffer_minutes():
    """Get the buffer duration from settings, default 30."""
    setting = db.session.get(Setting, "buffer_minutes")
    return int(setting.value) if setting else 30


def ranges_overlap(start1, end1, start2, end2):
    """Check if two ranges (in minutes) overlap."""
    return start1 < end2 and start2 < end1


def get_available_slots(date_str, service_id):
    """
    Return a list of available start times for a given date and service.

    Each slot candidate is checked against existing bookings including their
    buffer zones. A 60-min session with 30-min buffers blocks 2 hours total.

    Args:
        date_str: Date string in YYYY-MM-DD format
        service_id: ID of the service being booked

    Returns:
        List of time strings like ["10:00", "10:30", "11:00"]
    """
    booking_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    service = db.session.get(Service, service_id)
    if not service:
        return []

    buffer_mins = _get_buffer_minutes()
    duration = service.duration_minutes

    # Fetch availability windows for this date
    windows = AvailabilityWindow.query.filter_by(date=booking_date).all()
    if not windows:
        return []

    # Fetch existing non-cancelled bookings for this date
    existing_bookings = Booking.query.filter(
        Booking.date == booking_date,
        Booking.status != "cancelled",
    ).all()

    # Build list of blocked ranges (in minutes since midnight)
    blocked_ranges = []
    for b in existing_bookings:
        block_start = _time_to_minutes(b.buffer_before)
        block_end = _time_to_minutes(b.buffer_after)
        blocked_ranges.append((block_start, block_end))

    # Generate candidate slots
    available = []
    slot_interval = 30  # 30-minute granularity

    for window in windows:
        window_start = _time_to_minutes(window.start_time)
        window_end = _time_to_minutes(window.end_time)

        candidate = window_start
        while candidate + duration <= window_end:
            # Full blocked range for this candidate
            candidate_block_start = candidate - buffer_mins
            candidate_block_end = candidate + duration + buffer_mins

            # Check for conflicts with existing bookings
            conflict = False
            for block_start, block_end in blocked_ranges:
                if ranges_overlap(candidate_block_start, candidate_block_end,
                                  block_start, block_end):
                    conflict = True
                    break

            if not conflict:
                available.append(_minutes_to_time(candidate).strftime("%H:%M"))

            candidate += slot_interval

    # Sort and deduplicate (in case multiple windows overlap)
    return sorted(set(available))
