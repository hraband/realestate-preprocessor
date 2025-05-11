"""
main.py

Entrypoint for the normalization API using FastAPI.

Exposes a single POST endpoint `/normalize` which accepts a list of raw real estate
listings and returns their normalized form based on internal processing logic.
"""

from fastapi import FastAPI
from typing import List

from .normalize import normalize_listings
from .models import RawListing, NormalizedListing

# Define metadata for Swagger UI grouping
tags_metadata = [
    {
        "name": "Normalization",
        "description": "Operations related to preprocessing and normalizing real estate listings."
    }
]

# Initialize FastAPI with metadata
app = FastAPI(
    title="Real Estate Normalization API",
    description="API for transforming raw property listing data into a standardized format.",
    version="1.0.0",
    openapi_tags=tags_metadata
)


@app.post(
    "/normalize",
    response_model=List[NormalizedListing],
    summary="Normalize a batch of raw listings",
    tags=["Normalization"],
    response_description="List of normalized real estate listings"
)
def normalize_endpoint(raw_list: List[RawListing]):
    """
    Normalize a batch of raw real estate listings.

    Args:
        raw_list (List[RawListing]): A list of raw listings with possibly inconsistent or free-text fields.

    Returns:
        List[NormalizedListing]: Listings with cleaned, standardized, and structured fields.
    """
    return normalize_listings(raw_list)
