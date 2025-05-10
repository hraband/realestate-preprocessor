from typing import Optional, Union
from datetime import datetime
from pydantic import BaseModel, field_validator


class Coordinates(BaseModel):
    lat: Optional[float]
    lng: Optional[float]

    @field_validator('lat', 'lng', mode='before')
    def parse_float_nullable(cls, v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return None


class PropertyLocation(BaseModel):
    street: Optional[str]
    zip: Optional[str]
    city: Optional[str]
    canton: Optional[str]
    coordinates: Optional[Coordinates]


class RawListing(BaseModel):
    id: str
    platform: str
    price: Union[str, float, int]
    floor: Optional[Union[str, int]]
    rooms: Optional[Union[float, int, str]]
    living_space: Optional[Union[float, int, str]]
    plot_area: Optional[str]
    property_category: Optional[str]
    title: Optional[str]
    description: Optional[str]
    sale_type: str
    crawl_datetime: datetime
    published_datetime: Optional[datetime]
    seller_type: str
    build_year: Optional[Union[str, int]]
    payment_interval: Optional[str]
    additional_costs: Optional[str]
    parking: Optional[bool]
    property_location: PropertyLocation

    @field_validator('published_datetime', mode='before')
    def parse_published_datetime(cls, v):
        # Treat empty strings as None; let Pydantic parse valid dates
        if not v or (isinstance(v, str) and not v.strip()):
            return None
        return v


class NormalizedListing(BaseModel):
    price: int
    floor: int
    living_space: float
    propertyCategory: str
    title: str
    street: str
    price_per_sqm: float
    title_length: int
    title_word_count: int
    description_length: int
    description_word_count: int
    additional_costs: float
    build_year: Optional[int]
    age: Optional[int]
    days_since_published: Optional[int]
