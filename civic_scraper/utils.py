from datetime import datetime
from os.path import expanduser, join
import hashlib
import pytz  # Add pytz for timezone handling


def today_local_str():
    return datetime.now().strftime("%Y-%m-%d")


def parse_date(date_str, format="%Y-%m-%d"):
    return datetime.strptime(date_str, format)


def dtz_to_dt(dtz):
    return datetime.fromordinal(dtz.toordinal())


def default_user_home():
    return join(expanduser("~"), ".civic-scraper")


def mb_to_bytes(size_mb):
    if size_mb is None:
        return None
    return float(size_mb) * 1048576


def asset_generated_id(input_string):
    """Generates a unique ID based on the hash of an input string."""
    # Use SHA-256 for a robust hash, take the first 16 chars for brevity
    return hashlib.sha256(input_string.encode("utf-8")).hexdigest()[:16]


def parse_datetime_formats(datetime_str, formats, timezone_str):
    """Attempts to parse a datetime string using a list of format strings."""
    dt = None
    for fmt in formats:
        try:
            dt = datetime.strptime(datetime_str, fmt)
            break  # Success
        except ValueError:
            continue  # Try next format
    if dt and timezone_str:
        try:
            tz = pytz.timezone(timezone_str)
            # Make the datetime timezone-aware
            # If the original datetime had no time component, localize might fail
            # Check if time is midnight (often default when only date is parsed)
            if dt.time() == datetime.min.time():
                # Assume it represents the start of the day in the target timezone
                dt = tz.localize(dt, is_dst=None)
            else:
                # Assume the parsed time is already in the target timezone
                dt = tz.localize(
                    dt, is_dst=None
                )  # Or consider dt.replace(tzinfo=tz) if appropriate
        except pytz.UnknownTimeZoneError:
            # Log warning or handle error if timezone string is invalid
            pass  # Keep dt naive if timezone is invalid
        except Exception:
            # Handle potential localization issues (e.g., ambiguous times during DST change)
            # For simplicity, we might just keep it naive or apply a fixed offset
            pass
    if dt is None:
        raise ValueError(
            f"Could not parse datetime string '{datetime_str}' with any provided format."
        )
    return dt


def standardize_committee_name(name):
    """Standardizes a committee name (e.g., strip whitespace, title case)."""
    if not name:
        return "Unknown Committee"
    # Simple standardization: strip whitespace and title case
    return name.strip().title()
