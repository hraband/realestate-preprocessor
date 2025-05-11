"""
normalize.py

Contains utility functions and the main transformation logic that converts a list of
RawListing objects into NormalizedListing instances.

Handles parsing of prices, floors, room counts, living space, text cleaning, and engineered
features like price per square meter, title stats, and days since published.

All normalization functions are robust to format variation, locale-specific formatting,
and missing or inconsistent input.
"""

import re
import unicodedata
from typing import List, Optional, Union
from datetime import datetime, date

from .models import RawListing, NormalizedListing


def parse_price(raw: Union[str, float, int]) -> int:
    """
    Parse price from a string like "CHF 1'200.000,00" or "1,234.56".
    Handles both US and EU decimal/thousand separators.

    Returns:
        int: Parsed price in integer form. Falls back to 0 if parsing fails.
    """
    if isinstance(raw, (int, float)):
        return int(round(raw))

    s = re.sub(r"[^\d\.,]", "", raw or "")

    if "." in s and "," in s:
        if s.find(",") < s.find("."):
            s = s.replace(",", "")
        else:
            s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        left, right = s.split(",", 1)
        if len(right) == 3 and right.isdigit():
            s = left + right
        else:
            s = left + "." + right

    if s.count(".") > 1:
        parts = s.split(".")
        s = "".join(parts[:-1]) + "." + parts[-1]

    try:
        return int(round(float(s)))
    except ValueError:
        return 0


def parse_floor(raw: Optional[Union[str, int]]) -> int:
    """
    Extracts the floor level from text like '1st floor' or 'EG'.
    If no digit found, returns 0 (ground level).
    """
    if raw is None:
        return 0
    if isinstance(raw, int):
        return raw

    txt = str(raw).strip().lower()
    m = re.search(r"(\d+)", txt)
    return int(m.group(1)) if m else 0


def parse_rooms(raw: Optional[Union[float, int, str]]) -> float:
    """
    Extracts room count from strings like '3.5 rooms'.
    Returns 0.0 on failure.
    """
    if raw is None:
        return 0.0
    if isinstance(raw, (int, float)):
        return float(raw)
    cleaned = re.sub(r"[^\d\.,]", "", raw)
    try:
        return float(cleaned.replace(',', '.'))
    except ValueError:
        return 0.0


def parse_living_space(raw: Optional[Union[float, int, str]]) -> float:
    """
    Parses living space (e.g., '120 m²') into a float.
    Returns 0.0 on failure.
    """
    if raw is None:
        return 0.0
    if isinstance(raw, (int, float)):
        return float(raw)
    cleaned = re.sub(r"[^\d\.,]", "", raw)
    try:
        return float(cleaned.replace(',', '.'))
    except ValueError:
        return 0.0


def parse_additional_costs(raw: Optional[Union[str, float, int]]) -> float:
    """
    Parses additional costs field, handling both numeric and string input.
    """
    if raw is None:
        return 0.0
    if isinstance(raw, (int, float)):
        return float(raw)
    cleaned = re.sub(r"[^\d\.,]", "", raw)
    try:
        return float(cleaned.replace(',', '.'))
    except ValueError:
        return 0.0


def map_category(raw: Optional[str]) -> str:
    """
    Standardizes property category field to one of: apartment, house, ground, commercial, other.
    """
    txt = (raw or "").strip().lower()
    if "apartment" in txt:
        return "apartment"
    if "house" in txt:
        return "house"
    if "ground" in txt:
        return "ground"
    if "commercial" in txt:
        return "commercial"
    return "other"


def clean_text(raw: Optional[str]) -> str:
    """
    Removes accents, punctuation, and excessive whitespace.
    Used for fields like title and description.
    """
    if not raw:
        return ""
    text = unicodedata.normalize("NFKD", raw)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def compute_price_per_sqm(price: int, living: float, payment_interval: Optional[str]) -> float:
    """
    Computes price per square meter.
    Handles both classic total-price cases and 'per_square_meter' rent specifications.
    """
    if living <= 0:
        return 0.0

    interval = (payment_interval or "").strip().lower()

    if "per_square_meter" in interval:
        rate = float(price)
        if interval.startswith("per_year"):
            return round(rate / 12, 2)
        return round(rate, 2)

    return round(price / living, 2)


def parse_iso_datetime(raw: Optional[Union[str, datetime, date]]) -> Optional[datetime]:
    """
    Attempts to parse a raw value into a proper datetime object.
    Supports ISO strings, date objects, and datetimes.
    """
    if raw is None:
        return None
    if isinstance(raw, datetime):
        return raw
    if isinstance(raw, date):
        return datetime(raw.year, raw.month, raw.day)
    try:
        return datetime.fromisoformat(str(raw))
    except ValueError:
        return None


def parse_build_year(raw: Optional[Union[str, int]]) -> Optional[int]:
    """
    Parses the build year from raw input. Returns None if parsing fails.
    """
    if raw is None:
        return None
    try:
        return int(raw)
    except Exception:
        return None


def normalize_listings(raw_list: List[RawListing]) -> List[NormalizedListing]:
    """
    Main transformation pipeline.

    Transforms a batch of RawListing instances into normalized format,
    including engineered features like price_per_sqm and days_since_published.
    """
    out: List[NormalizedListing] = []
    today = date.today()

    for item in raw_list:
        price = parse_price(item.price)
        living = parse_living_space(item.living_space)
        floor = parse_floor(item.floor)
        rooms = parse_rooms(item.rooms)
        category = map_category(item.property_category)
        title = clean_text(item.title)
        street = clean_text(item.property_location.street)

        price_per_sqm = compute_price_per_sqm(price, living, item.payment_interval)
        title_length = len(title)
        title_word_count = len(title.split())

        desc = clean_text(item.description)
        description_length = len(desc)
        description_word_count = len(desc.split())

        additional_costs = parse_additional_costs(item.additional_costs)
        build_year = parse_build_year(item.build_year)
        age = (today.year - build_year) if build_year and today.year >= build_year else None

        published_dt = parse_iso_datetime(item.published_datetime)
        crawl_dt = parse_iso_datetime(item.crawl_datetime)
        published_date = published_dt.date() if published_dt else None

        if published_date and crawl_dt:
            days_since_published = (crawl_dt.date() - published_date).days
        else:
            days_since_published = None

        out.append(NormalizedListing(
            price=price,
            floor=floor,
            living_space=living,
            rooms=rooms,
            propertyCategory=category,
            title=title,
            street=street,
            price_per_sqm=price_per_sqm,
            title_length=title_length,
            title_word_count=title_word_count,
            description_length=description_length,
            description_word_count=description_word_count,
            additional_costs=additional_costs,
            build_year=build_year,
            age=age,
            days_since_published=days_since_published
        ))

    return out
