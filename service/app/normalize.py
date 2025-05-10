import re
import unicodedata
from typing import List, Optional, Union
from datetime import datetime, date

from .models import RawListing, NormalizedListing

def parse_price(raw: Union[str, float, int]) -> int:
    if isinstance(raw, (int, float)):
        return int(round(raw))

    s = re.sub(r"[^\d\.,]", "", raw or "")
    # both comma & dot present?
    if "," in s and "." in s:
        # US style: comma before dot → thousands sep
        if s.find(",") < s.find("."):
            s = s.replace(",", "")
        # EU style: dot before comma → thousands & decimal
        else:
            s = s.replace(".", "").replace(",", ".")
    # only comma present → decimal sep
    elif "," in s:
        s = s.replace(",", ".")
    # else only dots or none → leave as is

    # collapse any extra dots into a single decimal point
    if s.count(".") > 1:
        parts = s.split(".")
        s = "".join(parts[:-1]) + "." + parts[-1]

    try:
        return int(round(float(s)))
    except ValueError:
        return 0


def parse_floor(raw: Optional[Union[str, int]]) -> int:
    if raw is None:
        return 0
    if isinstance(raw, int):
        return raw
    txt = raw.strip().lower()
    if txt.startswith(("ground", "g")):
        return 0
    m = re.search(r"(\d+)", txt)
    return int(m.group(1)) if m else 0

def parse_rooms(raw: Optional[Union[float, int, str]]) -> float:
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
    if not raw:
        return ""
    text = unicodedata.normalize("NFKD", raw)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def parse_published(raw: Optional[str]) -> Optional[date]:
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(raw.replace('Z', '+00:00'))
        return dt.date()
    except Exception:
        return None

def parse_build_year(raw: Optional[Union[str, int]]) -> Optional[int]:
    if raw is None:
        return None
    try:
        return int(raw)
    except Exception:
        return None

def normalize_listings(raw_list: List[RawListing]) -> List[NormalizedListing]:
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

        # engineered features
        price_per_sqm = round(price / living, 2) if living > 0 else 0.0
        title_length = len(title)
        title_word_count = len(title.split())
        desc = clean_text(item.description)
        description_length = len(desc)
        description_word_count = len(desc.split())
        additional_costs = parse_additional_costs(item.additional_costs)
        build_year = parse_build_year(item.build_year)
        age = (today.year - build_year) if build_year and today.year >= build_year else None
        pub_date = parse_published(item.published_datetime)
        days_since_published = (today - pub_date).days if pub_date else None

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
