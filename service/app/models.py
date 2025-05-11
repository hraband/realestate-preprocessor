"""
models.py

Defines the data models for the normalization API using Pydantic.

- RawListing: Represents an unprocessed real estate listing as received from the data source.
- NormalizedListing: Represents a cleaned and standardized listing used downstream.
- Coordinates and PropertyLocation: Substructures embedded within listings.
"""

from typing import Optional, Union
from datetime import datetime
from pydantic import BaseModel, field_validator


class Coordinates(BaseModel):
    """
    Latitude and longitude representation.
    Accepts float or values that can be parsed to float.
    """
    lat: Optional[float]
    lng: Optional[float]

    @field_validator('lat', 'lng', mode='before')
    def parse_float_nullable(cls, v):
        """
        Convert values to float if possible; otherwise return None.
        Handles strings or malformed input gracefully.
        """
        try:
            return float(v)
        except (TypeError, ValueError):
            return None


class PropertyLocation(BaseModel):
    """
    Address and geographical metadata of the property.
    """
    street: Optional[str]
    zip: Optional[str]
    city: Optional[str]
    canton: Optional[str]
    coordinates: Optional[Coordinates]


class RawListing(BaseModel):
    """
    A raw real estate listing, as scraped from a property platform.

    Many fields are loosely typed to accommodate free-text, numeric, or inconsistent formats.
    This model will be transformed into a NormalizedListing via the normalization pipeline.
    """
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
        """
        Normalize published date input:
        - Converts empty strings or nulls to None
        - Allows datetime parsing by Pydantic for valid values
        """
        if not v or (isinstance(v, str) and not v.strip()):
            return None
        return v


class NormalizedListing(BaseModel):
    """
    A normalized, clean real estate listing used for downstream analytics or machine learning.

    Fields are strictly typed and reflect values computed or inferred from the RawListing.
    """
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
