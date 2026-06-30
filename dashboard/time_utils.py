"""Timezone helpers for dashboard-facing match schedules."""

from datetime import datetime
from zoneinfo import ZoneInfo


UTC = ZoneInfo("UTC")
BELGIUM = ZoneInfo("Europe/Brussels")
_MISSING = {"", "nan", "nat", "none", "<na>"}


def belgian_kickoff(date_value: object, time_value: object) -> tuple[str, str, str]:
    """Return ISO date, local time, and timezone label for a UTC kickoff."""
    date_text = str(date_value or "").strip()
    time_text = str(time_value or "").strip()
    if date_text.lower() in _MISSING:
        date_text = ""
    if time_text.lower() in _MISSING:
        time_text = ""
    if not date_text or not time_text:
        return date_text, time_text, ""

    try:
        clean_date = date_text[:10]
        clean_time = time_text.removesuffix("Z")
        kickoff = datetime.fromisoformat(f"{clean_date}T{clean_time}")
        if kickoff.tzinfo is None:
            kickoff = kickoff.replace(tzinfo=UTC)
        local = kickoff.astimezone(BELGIUM)
        return local.strftime("%Y-%m-%d"), local.strftime("%H:%M"), local.tzname() or "Belgium"
    except (TypeError, ValueError):
        return date_text, time_text, "UTC"
