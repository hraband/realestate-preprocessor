from fastapi import FastAPI
from typing  import List

from .normalize import normalize_listings
from .models    import RawListing, NormalizedListing

app = FastAPI()

@app.post(
    "/normalize",
    response_model=List[NormalizedListing],
    summary="Normalize a batch of raw listings"
)
def normalize_endpoint(raw_list: List[RawListing]):
    return normalize_listings(raw_list)
