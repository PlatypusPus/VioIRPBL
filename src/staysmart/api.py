import os
from datetime import date
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse

from .search import SearchEngine


def create_app(engine: SearchEngine | None = None) -> FastAPI:
    app = FastAPI(title="StaySmart")
    cache = {"engine": engine}

    def get_engine() -> SearchEngine:
        if cache["engine"] is None:
            raw_dir = Path(os.getenv("STAYSMART_DATA_DIR", "data/raw"))
            reference = os.getenv("STAYSMART_REFERENCE_DATE")
            reference_date = date.fromisoformat(reference) if reference else None
            try:
                cache["engine"] = SearchEngine.from_raw_dir(raw_dir, reference_date=reference_date)
            except FileNotFoundError as exc:
                raise HTTPException(status_code=503, detail=str(exc)) from exc
        return cache["engine"]

    @app.get("/", response_class=HTMLResponse)
    def home() -> str:
        return INDEX_HTML

    @app.get("/search")
    def search(q: str = Query(..., min_length=1), limit: int = Query(10, ge=1, le=50)) -> dict[str, object]:
        results = [result.as_dict() for result in get_engine().search(q, limit=limit)]
        return {"query": q, "count": len(results), "results": results}

    return app


INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>StaySmart</title>
  <style>
    body { margin: 0; font-family: Arial, sans-serif; color: #202124; background: #f6f7f9; }
    main { max-width: 860px; margin: 0 auto; padding: 32px 20px; }
    form { display: flex; gap: 8px; margin: 20px 0; }
    input { flex: 1; padding: 12px; border: 1px solid #c7ccd1; border-radius: 6px; font-size: 16px; }
    button { padding: 12px 16px; border: 0; border-radius: 6px; background: #155eef; color: white; font-size: 16px; }
    article { background: white; border: 1px solid #dde1e6; border-radius: 8px; padding: 16px; margin: 12px 0; }
    h1 { margin: 0; font-size: 32px; }
    h2 { margin: 0 0 8px; font-size: 18px; }
    mark { background: #fff1a8; }
    .meta { color: #5f6368; font-size: 14px; }
  </style>
</head>
<body>
<main>
  <h1>StaySmart</h1>
  <form id="search-form">
    <input id="query" name="q" placeholder="quiet room at night" required>
    <button>Search</button>
  </form>
  <section id="results"></section>
</main>
<script>
const form = document.querySelector("#search-form");
const results = document.querySelector("#results");
form.addEventListener("submit", async (event) => {
  event.preventDefault();
  results.textContent = "Searching...";
  const params = new URLSearchParams(new FormData(form));
  const response = await fetch(`/search?${params}`);
  if (!response.ok) {
    const error = await response.json().catch(() => ({detail: response.statusText}));
    results.textContent = error.detail || "Search failed";
    return;
  }
  const data = await response.json();
  results.innerHTML = data.results.map((item) => `
    <article>
      <h2>${item.listing_name}</h2>
      <div class="meta">${item.review_date} · score ${item.score.toFixed(3)}</div>
      <p>${item.snippet}</p>
    </article>
  `).join("") || "No matches.";
});
</script>
</body>
</html>"""


app = create_app()

