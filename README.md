# 🏠 Real Estate Preprocessor

A simple two-part pipeline to normalize real-estate listings from various platforms for downstream matching and ML tasks.

---

## 📖 Project Overview

This solution implements a modular, Python-based data normalization pipeline designed to:

1. **Ingest** raw JSONL listings from multiple property platforms via a lightweight CLI tool.  
2. **Normalize** varied field formats (prices, areas, categories, text) through a RESTful service.  
3. **Produce** a unified dataset enriched with engineered features (e.g., price per square meter, text length) ready for ML-powered matching.

**Why this approach?**  
- **Separation of concerns:** A dedicated processor handles I/O and batching, while the service focuses on data transformation logic.  
- **FastAPI:** Chosen for its high performance, built-in async support, and automatic OpenAPI/Swagger documentation—critical for scaling and maintainability.  
- **Requests library:** Simple, reliable HTTP client for inter-process communication in the processor.  
- **Pydantic:** Ensures strict validation and parsing of incoming and outgoing data models, minimizing runtime errors.

---

## 📂 Project Structure

* **service/** – FastAPI app exposing a `/normalize` endpoint.  
* **processor/** – CLI tool (Click) that reads raw JSONL, calls the service, and writes normalized output.  
* **tests/** – Pytest-based unit tests covering both normalization rules and feature engineering logic.  
* **Dockerfile** – Defines container image for the service with all dependencies.  
* **docker-compose.yml** – Orchestrates both service and processor for local end-to-end testing.


---

## 🚀 Quick Start

### Prerequisites

* Python 3.9+  
* `pip` to install dependencies  
* Docker & Docker Compose (optional)

### Install dependencies

```bash
pip install -r requirements.txt
```
### ⚠️ Prepare Input Data (Required)

Before running the CLI tool or Docker pipeline, make sure your input file (e.g. `raw_listings.jsonl`) is placed in the `data/` directory at the root of the project:
realestate-preprocessor/data/raw_listings.jsonl

### Run the service (Pure-Python)
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
> 🚀 **Scaling tip:**  
> For large datasets (e.g. millions of listings), consider increasing `--batch-size` (e.g. 500 or 1000) to reduce the number of HTTP requests and improve throughput.  
> The current implementation processes batches sequentially — parallel or async processing may be added in the future for high-throughput environments.


## 🐳 Docker & Deployment

A `Dockerfile` and `docker-compose.yml` are provided to run both the API service and the processor.

### Start the API

To build the images and launch the API in the background:

```bash
docker-compose up -d --build
```

The API is available at http://localhost:8000/normalize.

Run the processor on demand
To execute the processor and normalize the data:

```bash
docker-compose run --rm processor
```
This command uses the predefined arguments from the docker-compose.yml, processing raw_listings.jsonl and writing the output to normalized_listings.jsonl in the shared /data volume.

One-liner: Build, run API, and normalize

For convenience, both steps can be combined into a single command:

```bash
docker-compose up -d --build && docker-compose run --rm processor
```
This builds the services, starts the API in the background, and immediately runs the processor once. The API will remain running for any further normalization tasks.
### Future metrics & tuning

In production, both the service and processor can be instrumented with Prometheus metrics (e.g., request durations, batch processing time) and visualized in Grafana dashboards. This instrumentation supports data-driven batch-size optimization based on CPU, memory, and network metrics.

---

## 📚 Documentation

### 🧪 API Reference (Swagger & ReDoc)

The FastAPI service exposes auto-generated interactive documentation:

- **Swagger UI** — for interactive testing  
  [http://localhost:8000/docs](http://localhost:8000/docs)

- **ReDoc** — for clean OpenAPI spec browsing  
  [http://localhost:8000/redoc](http://localhost:8000/redoc)

These pages include:
- The `/normalize` endpoint with full request/response models
- Auto-generated field types and descriptions from Pydantic schemas

### 🛠 Internal Code Documentation (pdoc)

Developer-facing documentation for internal modules (e.g. `normalize.py`, `models.py`) is generated using [`pdoc`](https://pdoc.dev/).

To generate the documentation locally:

```bash
PYTHONPATH=. pdoc service.app.models service.app.normalize --output-dir docs
```
---

## 🧪 Testing

Unit tests for the normalization logic are located in the `tests/` folder.

You can run them locally using:

```bash
pytest
```
In the future, this test suite can be integrated into a CI/CD pipeline (e.g., GitHub Actions) to ensure every change to the normalization logic is automatically tested before deployment.

## 🧮 Data Analysis & Handling
The exploratory data analysis and strategy decisions described here were conducted using a Jupyter Notebook located at:
📄 notebooks/analysis.ipynb

- **This notebook includes code cells for:** 
  - Checking field completeness across ~60,000 listings
  - Visualizing distributions (e.g., price, living space)
  - Identifying outliers and skewed fields
  - Supporting decisions around imputation, filtering, and feature engineering
A static html version of this analysis is also included in the `docs/` folder as `analysis.html` for review without running the notebook.

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

This section outlines how each field is parsed, cleaned, and standardized, along with handling of edge cases and future considerations.

---

### `price`

- Parsed as an integer (CHF), stripping all non-digit characters including currency symbols, thousand separators (`.`, `'`), and decimals.
- Non-numeric entries like `"Prix sur demande"` are cleaned to an empty string, resulting in `price = 0` as a fallback.
- Downstream logic can interpret `0` as "missing" and choose to drop or impute such records.

**Outlier strategy**:
- Extremely high values (e.g. CHF > 5,000,000) may be log-transformed or capped in downstream ML workflows.

---

### `floor`

- Textual labels like `"ground"`, `"EG"`, `"Erdgeschoss"` are mapped to `0`.
- Numeric strings are parsed as integers.
- Non-numeric, unknown, or special cases (e.g. `"Penthouse"`, `"Dachgeschoss"`, `None`) default to `0`.

**Known limitation**:
- Both ground floor and top floor currently normalize to `0`, so the model can't differentiate them.

**Future improvements**:
- Map `"penthouse"` or `"top"` to `-1` or `max_floor + 1`.
- Add boolean flags such as `is_ground_floor`, `is_top_floor`.
- Use `null` when floor information is completely absent.

---

### `living_space`

- Cleans inputs like `"85 m²"` or `"100,5"` by removing non-digit characters, replacing `,` with `.` and parsing as `float`.
- Fallback to `0.0` if unparseable.
- Outliers (≫ 500 m²) are retained but can be flagged or capped downstream.

---

### `propertyCategory`

- Normalized to one of: `apartment`, `house`, `ground`, `commercial`, `other` via keyword-based matching.

**Future enhancements**:
- Expand keyword dictionary with multilingual support (e.g., `"wohnung"`, `"maison"`).
- Handle fuzzy matches and synonyms (e.g., `"hotel-gastronomie"`, `"single-house"`).
- Add subcategories like `office`, `parking`, `industrial`.
- Consider using a lightweight classifier trained on labeled examples.

---

### Text fields (`title`, `street`, `description`)

- Unicode-normalized (NFKD) to handle accents
- HTML and punctuation removed
- Lowercased and extra spaces collapsed
- Missing values default to an empty string

---

### Text-based features

These features aim to quantify listing descriptiveness for matching or quality scoring:

- `title_length`: number of characters
- `title_word_count`: number of words
- `description_length` and `description_word_count`: same as above for the description

---

### Fallback defaults

Any unspecified or unparseable values are normalized as follows:

- Numbers → `0` or `0.0`
- Text → empty string (`""`)
- Categorical → `"other"`


## 🔗 Platform Context

 **Future consideration**:  
 Each listing originates from a distinct portal (e.g., Homegate, Immoscout24, Comparis, etc.). Carrying the `platform` field through the pipeline enables several benefits:

- **Preserve platform metadata**  
  Retain the source portal for each record to enable downstream models to learn portal-specific patterns and biases.

- **Platform-specific normalization**  
  Handle quirks like locale-based number formats, currency symbols, or multilingual labels (e.g. `"wohnung"` vs. `"appartement"`) on a per-platform basis.

- **Traceability**  
  Store the original URL or source ID for each record to allow backtracking and human verification in the matching pipeline.

- **Bias correction**  
  Some platforms may systematically over- or under-price listings. Including `platform` as a model feature—or calibrating metrics like `price_per_sqm` by platform—can help reduce false positives.


---

## 🌟 Feature Engineering

The following derived features were engineered to support ML-based property matching by capturing pricing efficiency, listing richness, recency, and key amenities.

---

### `price_per_sqm`  *(CHF per m²)*

- For **sale** listings: `price` ÷ `living_space`
- For **rent** listings: monthly `price` ÷ `living_space` (adjusted if provided in daily or annual terms)
- Outlier values are either capped between the 5th and 95th percentiles or log-transformed prior to modeling

This feature enables comparison across properties by adjusting cost to size — useful for aligning listings of different types or pricing schemes.

---

### `title_length`

- Character count of the cleaned `title`
- Serves as a proxy for marketing emphasis and descriptive richness

---

### `description_length`

- Character count of the cleaned `description`
- Reflects the amount of descriptive content, often correlated with listing quality or agent professionalism

---

### `has_parking`

- Boolean: `true` if parking is mentioned anywhere in the raw data
- Captures a key amenity often used in buyer filters
- Helps prevent false-positive matches between similar properties with/without parking

---

### `year_built`

- Integer normalized from the `build_year` field
- Defaults to `0` if missing
- Can be used to infer property condition, design era, or renovation likelihood

---

### `days_since_published`

- Integer: difference in days between `crawl_datetime` and `published_datetime`
- Highlights listing freshness, reducing the risk of matching with stale or unavailable properties

---

These engineered signals enable the matching model to weigh cost-efficiency, listing verbosity, amenity presence, and recency — all of which are critical in distinguishing near-duplicate or equivalent listings across platforms.

---


## 🤖 ML Matching Strategy

This section outlines additional data fields, candidate filtering strategies, model architectures, and scalable workflows designed to support accurate and efficient real-estate listing matching across platforms.

---

### 1. Valuable Additional Fields

To improve matching precision and recall, the following fields are especially useful:

- **Bedrooms** – number of sleeping rooms  
- **Location bucket** – group listings by nearby coordinates (e.g., grid cell or H3 index)  
- **Amenities count** – count of terms like "garage", "pool", "garden"  
- **Listing age** – days since the listing was first published  
- **Seller type** – distinguish company vs. private  
- **Price per m²** – normalized cost signal  
- **Text embeddings** – vector representations of title and description (e.g., via MiniLM)

---

### 2. Candidate Filtering ("Blocking")

To reduce computational cost at scale, apply lightweight filters before ML inference:

- Only compare listings in the same or adjacent **location bucket**
- Filter candidates within **±10% price per m²** and **±1 bedroom**
- Optionally use a **hash or fingerprint** on cleaned titles for obvious duplicates

---

### 3. Proposed ML Approaches

Three viable model strategies:

- **Siamese Neural Network**  
  - Two identical subnetworks process input pairs (e.g., title, description, price, etc.)  
  - Cosine similarity between the outputs yields a match score (0–1)  
  - Effective with labeled training data and complex similarity patterns

- **Gradient-Boosted Trees (e.g., XGBoost)**  
  - Trained on handcrafted feature differences (e.g., price delta, embedding distance)  
  - Fast to train, interpretable, and robust on structured data  

- **RAG-Style Embedding Matching**  
  - Generate embeddings via pre-trained model (e.g., `all-MiniLM-L6-v2`)  
  - Index with Faiss for fast retrieval  
  - Requires no labels and deploys quickly

---

### 🔍 Comparison of Approaches

| Approach                     | Strengths                                              | Limitations                                           | Best Use Case                                          |
|------------------------------|---------------------------------------------------------|--------------------------------------------------------|--------------------------------------------------------|
| **Siamese Network**          | Learns complex similarity patterns, works well with text | Needs labeled data, slower dev cycle                   | High-precision use cases with labeled match data       |
| **Gradient-Boosted Trees**   | Fast, interpretable, good tabular performance           | Needs labels, manual feature engineering               | Structured data with labeled examples                  |
| **RAG-style Embedding Matching** | No training needed, fast to deploy, scalable             | May miss domain-specific context                       | Cold-start or low-label scenarios with fast turnaround |

---

### 4. Scaling to 40,000+ Listings

Efficient hybrid matching strategy for large-scale datasets:

1. **Precompute** all embeddings and numerical features  
2. **Index** listings using a vector database (e.g., Faiss)  
3. For each new listing:  
   - Retrieve top K candidates from the index  
   - Score only these candidates using the full ML model (e.g., Siamese or XGBoost)  
   
This architecture balances **speed** and **accuracy**.

---

### 5. Example: Matching in Practice

- **Listing A**: 2 beds, CHF 8,000/m², lake-view, title: “Bright 2-bed apartment”  
- **Listing B**: 2 beds, CHF 7,900/m², same location, title: “2-room flat close to lake”  
- They pass location and price filters  
- A **cosine similarity of 0.95** from the Siamese network indicates a likely match

---

### Summary

This strategy blends pragmatic, deployable solutions (RAG-style retrieval) with more advanced modeling (Siamese, GBT), enabling iterative improvements over time — from rule-based filtering to full ML matching pipelines.

 



*Prepared by \ Andrea Hrabovski, 2025*

