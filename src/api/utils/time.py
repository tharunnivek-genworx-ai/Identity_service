from datetime import datetime, timezone
 
 
def utc_now() -> datetime:
    """Return the current UTC time as a timezone-aware datetime. Used as
    the default and onupdate callable for all TIMESTAMP columns."""
    return datetime.now(timezone.utc)