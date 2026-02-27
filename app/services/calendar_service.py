from datetime import datetime, timedelta
from urllib.parse import quote


def generate_ics(booking):
    start_dt = datetime.combine(booking.date, booking.start_time)
    end_dt = datetime.combine(booking.date, booking.end_time)

    uid = f"hopono-booking-{booking.id}@hoponomassage.com"
    now = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    dtstart = start_dt.strftime("%Y%m%dT%H%M%S")
    dtend = end_dt.strftime("%Y%m%dT%H%M%S")

    summary = f"{booking.service.name} — HoPono Massage"
    description = (
        f"Service: {booking.service.name}\\n"
        f"Duration: {booking.service.duration_minutes} minutes\\n"
        f"Price: EUR {booking.service.price_eur}\\n"
        f"\\nQuestions? Call +357 96 537 959"
    )
    location = "HoPono Massage Studio, Nicosia, Cyprus"

    ics = (
        "BEGIN:VCALENDAR\r\n"
        "VERSION:2.0\r\n"
        "PRODID:-//HoPono Massage//Booking//EN\r\n"
        "CALSCALE:GREGORIAN\r\n"
        "METHOD:PUBLISH\r\n"
        "BEGIN:VEVENT\r\n"
        f"UID:{uid}\r\n"
        f"DTSTAMP:{now}\r\n"
        f"DTSTART:{dtstart}\r\n"
        f"DTEND:{dtend}\r\n"
        f"SUMMARY:{summary}\r\n"
        f"DESCRIPTION:{description}\r\n"
        f"LOCATION:{location}\r\n"
        "STATUS:CONFIRMED\r\n"
        "BEGIN:VALARM\r\n"
        "TRIGGER:-PT1H\r\n"
        "ACTION:DISPLAY\r\n"
        "DESCRIPTION:Reminder: Your HoPono Massage appointment is in 1 hour\r\n"
        "END:VALARM\r\n"
        "END:VEVENT\r\n"
        "END:VCALENDAR\r\n"
    )
    return ics


def google_calendar_url(booking):
    start_dt = datetime.combine(booking.date, booking.start_time)
    end_dt = datetime.combine(booking.date, booking.end_time)

    dates = f"{start_dt.strftime('%Y%m%dT%H%M%S')}/{end_dt.strftime('%Y%m%dT%H%M%S')}"
    title = f"{booking.service.name} — HoPono Massage"
    details = (
        f"Service: {booking.service.name}\n"
        f"Duration: {booking.service.duration_minutes} minutes\n"
        f"Price: EUR {booking.service.price_eur}\n"
        f"\nQuestions? Call +357 96 537 959"
    )
    location = "HoPono Massage Studio, Nicosia, Cyprus"

    url = (
        "https://calendar.google.com/calendar/render"
        f"?action=TEMPLATE"
        f"&text={quote(title)}"
        f"&dates={dates}"
        f"&details={quote(details)}"
        f"&location={quote(location)}"
    )
    return url


def outlook_calendar_url(booking):
    start_dt = datetime.combine(booking.date, booking.start_time)
    end_dt = datetime.combine(booking.date, booking.end_time)

    title = f"{booking.service.name} — HoPono Massage"
    body = (
        f"Service: {booking.service.name}\n"
        f"Duration: {booking.service.duration_minutes} minutes\n"
        f"Price: EUR {booking.service.price_eur}\n"
        f"\nQuestions? Call +357 96 537 959"
    )
    location = "HoPono Massage Studio, Nicosia, Cyprus"

    url = (
        "https://outlook.live.com/calendar/0/action/compose"
        f"?subject={quote(title)}"
        f"&startdt={start_dt.strftime('%Y-%m-%dT%H:%M:%S')}"
        f"&enddt={end_dt.strftime('%Y-%m-%dT%H:%M:%S')}"
        f"&body={quote(body)}"
        f"&location={quote(location)}"
    )
    return url
