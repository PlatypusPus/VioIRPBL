# StaySmart

StaySmart is a local review search system for accommodation reviews. It loads owner-supplied review data, filters hotel-type listings, ranks passages with BM25, TF-IDF, phrase, proximity and recency signals, and serves results through a CLI or FastAPI page.

## Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest
```

## Data

Place owner-supplied files in `data/raw/`.

Supported review files:
- `reviews.csv`
- `reviews.jsonl`
- `reviews.json`

Supported listing files:
- `listings.csv`
- `listings.jsonl`
- `listings.json`

Expected normalized review fields are `review_id`, `listing_id`, `listing_name`, `review_text` and `review_date`. Inside Airbnb-style fields are also mapped: review `id`, `date`, `comments`, and listing `id`, `name`, `room_type`.

If listings are provided, only rows with `room_type` equal to `Hotel room` are used.

## Commands

Print corpus stats and 20 deterministic sample passages:

```powershell
python -m staysmart.data data/raw
```

Build a persisted index:

```powershell
python -m staysmart.build_index data/raw data/processed/index.pkl
```

Search from raw data:

```powershell
python -m staysmart.search "quiet room at night" --data data/raw --limit 5
```

Search from a persisted index:

```powershell
python -m staysmart.search "quiet room at night" --index data/processed/index.pkl --limit 5
```

Run the API and page:

```powershell
python -m uvicorn staysmart.api:app --reload
```

Open `http://127.0.0.1:8000`.

Use a persisted index in the API:

```powershell
$env:STAYSMART_INDEX_PATH = "data/processed/index.pkl"
python -m uvicorn staysmart.api:app --reload
```

Run evaluation after filling `eval/judgments.csv`:

```powershell
python -m staysmart.evaluate data/raw eval/judgments.csv eval/results.md
```

## Judgment File

`eval/judgments.csv` must have:

```csv
query,review_id,relevance
quiet room,r123,2
quiet room,r456,0
```

Relevance is owner judged: `0` not relevant, `1` partly relevant, `2` relevant.

