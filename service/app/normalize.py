import re
import unicodedata
from typing import List

from .models import RawListing, NormalizedListing

# 1. Price parsing: strip currency, thousands‐sep, convert to int
def parse_price(raw: str) -> int:
    # remove all non-digit and non-dot characters
    cleaned = re.sub(r"[^\d\.]", "", raw)
    # if there are multiple dots (e.g. “1.200.00”), assume last is decimal
    if cleaned.count('.') > 1:
        parts = cleaned.split('.')
        # join all but last as integer part, keep last as decimal
        cleaned = "".join(parts[:-1]) + "." + parts[-1]
    try:
        value = float(cleaned)
    except ValueError:
        value = 0.0
    return int(round(value))

# 2. Floor parsing: extract first integer, ground→0
def parse_floor(raw: str) -> int:
    raw = raw.strip().lower()
    if raw.startswith(("ground", "g")):
        return 0
    m = re.search(r"(\d+)", raw)
    return int(m.group(1)) if m else 0

# 3. Living space: if numeric, use as-is; if str, strip units
def parse_living_space(raw) -> float:
    if isinstance(raw, (int, float)):
        return float(raw)
    cleaned = re.sub(r"[^\d\.]", "", raw)
    try:
        return float(cleaned)
    except ValueError:
        return 0.0

# 4. Category mapping
def map_category(raw: str) -> str:
    txt = raw.strip().lower()
    if "apartment" in txt:
        return "apartment"
    if "house" in txt:
        return "house"
    if "ground" in txt:
        return "ground"
    if "commercial" in txt:
        return "commercial"
    return "other"

# 5. Text cleaning: remove accents, lowercase, collapse whitespace
def clean_text(raw: str) -> str:
    # normalize unicode (e.g. ü → u)
    text = unicodedata.normalize("NFKD", raw)
    # remove combining marks
    text = "".join(c for c in text if not unicodedata.combining(c))
    # lowercase
    text = text.lower()
    # remove punctuation
    text = re.sub(r"[^\w\s]", " ", text)
    # collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text

# 6. Main normalization function
def normalize_listings(raw_list: List[RawListing]) -> List[NormalizedListing]:
    out: List[NormalizedListing] = []
    for item in raw_list:
        price = parse_price(item.price)
        living = parse_living_space(item.living_space)
        floor = parse_floor(item.floor)
        category = map_category(item.property_category)
        title = clean_text(item.title)
        street = clean_text(item.property_location.street)

        # engineered features
        price_per_sqm = round(price / living, 2) if living > 0 else 0.0
        title_length = len(title)

        out.append(NormalizedListing(
            price=price,
            floor=floor,
            living_space=living,
            propertyCategory=category,
            title=title,
            street=street,
            price_per_sqm=price_per_sqm,
            title_length=title_length
        ))
    return out
