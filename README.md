# Real Estate Preprocessor

A simple two-part pipeline to normalize real‑estate listings from various platforms for downstream matching and ML tasks.

---

## 📦 Project Structure

* **service/** – FastAPI app exposing a `/normalize` endpoint.
* **processor/** – CLI tool that reads raw JSONL, calls the service, and writes normalized output.
* **tests/** – Unit tests for normalization logic.

---

## 🚀 Quick Start

### Prerequisites

* Python 3.9+
* `pip` to install dependencies
* Docker (optional, see section below)

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run the service

```bash
uvicorn service.app.main:app --reload --host 0.0.0.0 --port 8000
```

### Normalize via CLI

```bash
python -m processor.processor \
  --input data/raw_listings.jsonl \
  --output data/normalized_listings.jsonl \
  --url http://localhost:8000/normalize \
  --batch-size 50
```

---

## 🧮 Data Analysis & Handling

- **Field completeness**  
  Observed substantial missingness in several key fields (out of ~60 000 records):  
  - `plot_area`: ~33 800 missing  
  - `parking`: ~31 700 missing  
  - `additional_costs`: ~27 000 missing  
  - `published_datetime`: ~22 200 missing  
  - `build_year`: ~21 900 missing  
  - `floor` & `rooms`: ~18 500 and ~9 600 missing respectively  

- **Imputation & filtering strategies**  
  - **Numeric fields** with missing values are set to `None` in the Pydantic model (so downstream ML can decide), or to `0` when a zero‑value is semantically meaningful (e.g., `additional_costs`).  
  - **Categorical fields** (`propertyCategory`) map any missing or unrecognized text to `"other"`.  
  - **Text fields** (`title`, `description`, `street`) default to an empty string when missing.  
  - **Date fields** (`published_datetime`) become `None`, and derived `days_since_published` is set to `None`.  
  - We **exclude** any record missing both `price` and `living_space` since key ratios (like price/m²) cannot be computed.

- **Outlier handling & scaling**  
  - **Price** and **living_space** are highly right‑skewed; in a matching pipeline we recommend either **log‑transforming** or **clamping** them at the 1st–99th percentile to reduce the impact of extreme values.  
  - The derived **`price_per_sqm`** also inherits this skew; apply the same capping or transformation before feeding into a model.  
  - Continuous features will be **standardized** or **robust‑scaled** in your ML preprocessing to mitigate different ranges and outliers.

- **Feature distributions**  
  - **Median sale price** is around **CHF 1 000 000**, with a long tail of luxury listings.
  - **Median rent price** is around **CHF 1 420** per month.  
  - Typical living_space centers near 75 m² but extends from studio flats to multi‑hundred‑sqm villas.  
  - Title lengths average ~30 characters, with some titles exceeding 200 characters.

This strategy ensures that our normalized dataset is complete, robust to extreme values, and ready for downstream ML matching or backfill tasks.  


---

## 🔄 Normalization & Assumptions

* **`price`**: parsed from strings or numbers into integer CHF values, stripping currency symbols, thousand‐separators, and decimals.
* **`floor`**: mapped textual floors (`"ground"`, `"G"`) to `0`, numeric strings to ints.
* **`living_space`**: extracted numeric m² from strings into floats.
* **`propertyCategory`**: one of `apartment`, `house`, `ground`, `commercial`, `other`; relies on keyword matching.
* **Text fields** (`title`, `street`): Unicode‐normalized, lowercased, non‐word chars removed, whitespace cleaned.

*Unspecified or unparsable inputs default to safe values (0, empty string, or `other`).*

---

## 🌟 Feature Engineering

Implemented both numerical and textual signals to enrich the matching model:

- **`price_per_sqm`**  
  \(CHF/m²\)  
  > `price / living_space`  
  A core metric for comparing value across listings.

- **`title_length`**  
  > Character count of the cleaned `title`  
  Serves as a proxy for marketing emphasis and descriptive richness.

- **`description_length`**  
  > Character count of the cleaned `description`  
  Gauges listing detail depth.

- **`has_parking`**  
  > Boolean (“true” if any parking information present)  
  Captures a key amenity often used in buyer preferences.

- **`year_built`**  
  > Normalized integer from `build_year` (0 if missing)  
  Offers an age-based feature for condition and style.

These engineered features help the downstream ML matcher weigh cost efficiency, verbosity, amenity presence, and property vintage when aligning similar listings. ```


---

## 🤖 ML Matching Strategy

## 🤖 ML Matching Strategy

### 1. Extra Helpful Fields
To improve matching precision and recall, the following additional fields are highly valuable:
- **Bedrooms**: number of sleeping rooms.
- **Location bucket**: group nearby latitude/longitude cells to compare within the same neighborhood.
- **Amenities count**: count keywords like “garage,” “pool,” “garden” in the description.
- **Listing age**: days since the listing went live.
- **Seller type**: company vs. private.
- **Price per m²**: price divided by living space.
- **Text embeddings**: numeric vectors summarizing title and description using a lightweight encoder.

### 2. Fast Candidate Filtering (“Blocking”)
Efficiently reduce the number of comparisons by:
- Restricting to listings in the same or adjacent **location bucket**.
- Filtering to those within **±10% price per m²** and **±1 bedroom**.
- Optionally applying a **simple text hash** on cleaned titles to catch obvious duplicates.

### 3. Proposed ML Approaches
Two complementary approaches are proposed:

- **Siamese Network**
  - Two identical neural “towers” process text embeddings and numeric features.
  - Cosine similarity between their 128-dimensional outputs yields a match score (0–1).
  - Especially powerful when labeled pairs are available.

- **Gradient-Boosted Trees (e.g. XGBoost)**
  - Handcrafted feature differences (e.g., price difference, bedroom difference, embedding distance).
  - One-hot encoded categorical fields.
  - Predicts match probability from structured feature inputs.

- **RAG-Style Simple Embedding Matching**
  - Precompute embeddings using a pre-trained Sentence Transformer (e.g., `all-MiniLM-L6-v2`).
  - Index embeddings with a fast nearest-neighbor engine (e.g., Faiss).
  - Retrieve top‑K similar listings; optionally apply numeric filters.
  - Requires no labeled training data and deploys rapidly.
### 🔍 Comparison of Approaches

| Approach                     | Strengths                                        | Weaknesses                                      | Best Use Case                           |
|------------------------------|-------------------------------------------------|------------------------------------------------|----------------------------------------|
| **Siamese Network**          | Learns rich similarity patterns, handles complex signals | Needs labeled data, requires training, slower to develop | When labeled match/no-match data is available and you need high precision |
| **Gradient-Boosted Trees**   | Strong tabular performance, interpretable, fast to train | Needs labeled match/non-match pairs, manual feature engineering, limited on raw text | When you can design good numeric + categorical features and have labeled pairs |
| **RAG-Style Embedding Matching** | No training needed, fast to implement, scalable with Faiss | Relies on pre-trained embeddings, may miss domain-specific patterns | When you need a pragmatic, production-ready solution with minimal labeled data |


### 4. Scaling to 40,000+ Listings
- Precompute all text and numeric features once.
- Build a **vector index** (e.g., Faiss) on the 128‑dimensional embeddings.
- For each listing:
  1. Retrieve the top K nearest neighbors (e.g., K=50) from the index.
  2. Run the full scoring model (Siamese or XGBoost) only on this reduced candidate set.
- This hybrid approach balances **speed** and **accuracy** at scale.

### 5. Example Workflow
1. **Listing A**: 2 beds, CHF 8,000/m², lake‑view, title “Bright 2‑bed apartment.”
2. **Listing B**: 2 beds, CHF 7,900/m², same block, title “2‑room flat close to lake.”
3. Both pass **location and price filters**.
4. A **cosine similarity of 0.95** from the Siamese network indicates a likely duplicate match.

### Summary
This ML strategy blends pragmatic, production-ready solutions (RAG-style retrieval) with more sophisticated machine learning models (Siamese, XGBoost), allowing rapid iteration and future improvements.
 

---

## 🐳 Docker & Deployment

A `Dockerfile` and `docker-compose.yml` spin up both service and CLI runner.

```bash
docker-compose up --build
```
---

*Prepared by \Andrea Hrabovski, 2025*

