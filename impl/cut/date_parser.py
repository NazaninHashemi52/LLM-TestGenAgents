"""Date parsing module — a CUT with many boundary cases (leap years, month ends).

Implemented without the datetime module so that every boundary check is
explicit in the source and visible to coverage and mutation testing.
"""


class DateError(ValueError):
    """Raised for malformed or out-of-range dates."""


_DAYS_IN_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

_MONTH_NAMES = [
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
]

MIN_YEAR = 1
MAX_YEAR = 9999


def is_leap_year(year):
    """Return True if year is a Gregorian leap year."""
    if not isinstance(year, int) or isinstance(year, bool):
        raise TypeError("year must be an int")
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def days_in_month(year, month):
    """Return the number of days in the given month (1-12) of year."""
    if not 1 <= month <= 12:
        raise DateError(f"month out of range: {month}")
    if month == 2 and is_leap_year(year):
        return 29
    return _DAYS_IN_MONTH[month - 1]


def validate_date(year, month, day):
    """Raise DateError if (year, month, day) is not a valid calendar date."""
    for name, value in (("year", year), ("month", month), ("day", day)):
        if not isinstance(value, int) or isinstance(value, bool):
            raise TypeError(f"{name} must be an int")
    if not MIN_YEAR <= year <= MAX_YEAR:
        raise DateError(f"year out of range: {year}")
    if not 1 <= month <= 12:
        raise DateError(f"month out of range: {month}")
    if not 1 <= day <= days_in_month(year, month):
        raise DateError(f"day out of range for {year}-{month:02d}: {day}")


def _to_int(text, field):
    if not text.isdigit():
        raise DateError(f"{field} is not a number: {text!r}")
    return int(text)


def parse_date(text):
    """Parse a date string and return a (year, month, day) tuple.

    Supported formats:
        - ISO:       "2024-02-29"
        - European:  "29/02/2024" or "29.02.2024"
        - Long form: "29 February 2024" or "Feb 29, 2024" (month names may be
                     abbreviated to 3+ letters, case-insensitive)

    Surrounding whitespace is ignored.

    Raises:
        TypeError: if text is not a str.
        DateError: if the format is unrecognised or the date is invalid.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a str")
    text = text.strip()
    if not text:
        raise DateError("empty date string")

    if "-" in text:
        parts = text.split("-")
        if len(parts) != 3 or len(parts[0]) != 4:
            raise DateError(f"invalid ISO date: {text!r}")
        year, month, day = (_to_int(p, f) for p, f in zip(parts, ("year", "month", "day")))
    elif "/" in text or "." in text:
        sep = "/" if "/" in text else "."
        parts = text.split(sep)
        if len(parts) != 3:
            raise DateError(f"invalid numeric date: {text!r}")
        day, month, year = (_to_int(p, f) for p, f in zip(parts, ("day", "month", "year")))
    else:
        tokens = text.replace(",", " ").split()
        if len(tokens) != 3:
            raise DateError(f"unrecognised date format: {text!r}")
        if tokens[0].isdigit():
            day_tok, month_tok, year_tok = tokens
        else:
            month_tok, day_tok, year_tok = tokens
        month = month_from_name(month_tok)
        day = _to_int(day_tok, "day")
        year = _to_int(year_tok, "year")

    validate_date(year, month, day)
    return (year, month, day)


def month_from_name(name):
    """Return the month number (1-12) for a full or abbreviated (3+ letter) name."""
    if not isinstance(name, str):
        raise TypeError("name must be a str")
    key = name.strip().lower().rstrip(".")
    if len(key) < 3:
        raise DateError(f"month name too short: {name!r}")
    for i, full in enumerate(_MONTH_NAMES, start=1):
        if full.startswith(key):
            return i
    raise DateError(f"unknown month name: {name!r}")


def format_date(year, month, day, style="iso"):
    """Format a valid date. style is 'iso' (YYYY-MM-DD), 'eu' (DD/MM/YYYY) or 'long'."""
    validate_date(year, month, day)
    if style == "iso":
        return f"{year:04d}-{month:02d}-{day:02d}"
    if style == "eu":
        return f"{day:02d}/{month:02d}/{year:04d}"
    if style == "long":
        return f"{day} {_MONTH_NAMES[month - 1].capitalize()} {year}"
    raise ValueError(f"unknown style: {style!r}")


def day_of_year(year, month, day):
    """Return the 1-based ordinal day within the year (1..365 or 366)."""
    validate_date(year, month, day)
    return sum(days_in_month(year, m) for m in range(1, month)) + day


def add_days(year, month, day, n):
    """Return the date n days after (or before, if negative) the given date."""
    validate_date(year, month, day)
    if not isinstance(n, int) or isinstance(n, bool):
        raise TypeError("n must be an int")
    while n > 0:
        remaining = days_in_month(year, month) - day
        if n <= remaining:
            day += n
            n = 0
        else:
            n -= remaining + 1
            day = 1
            month += 1
            if month > 12:
                month = 1
                year += 1
    while n < 0:
        if -n < day:
            day += n
            n = 0
        else:
            n += day
            month -= 1
            if month < 1:
                month = 12
                year -= 1
            day = days_in_month(year, month)
    validate_date(year, month, day)
    return (year, month, day)


def days_between(date_a, date_b):
    """Return the signed number of days from date_a to date_b (each a (y, m, d) tuple)."""
    return _ordinal(*date_b) - _ordinal(*date_a)


def _ordinal(year, month, day):
    """Days since 0001-01-01 (which has ordinal 1)."""
    y = year - 1
    return y * 365 + y // 4 - y // 100 + y // 400 + day_of_year(year, month, day)


def weekday(year, month, day):
    """Return the weekday name of the given date (0001-01-01 was a Monday)."""
    names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    return names[(_ordinal(year, month, day) - 1) % 7]
