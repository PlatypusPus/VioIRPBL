import os
from datetime import date
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse

from .search import SearchEngine
from .store import load_engine


def create_app(engine: SearchEngine | None = None) -> FastAPI:
    app = FastAPI(title="StaySmart")
    cache = {"engine": engine}

    def get_engine() -> SearchEngine:
        if cache["engine"] is None:
            index_path = os.getenv("STAYSMART_INDEX_PATH")
            if index_path:
                cache["engine"] = load_engine(Path(index_path))
                return cache["engine"]
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

    @app.get("/locations")
    def locations() -> dict[str, object]:
        return {"locations": get_engine().locations()}

    @app.get("/search")
    def search(q: str = Query(..., min_length=1), limit: int = Query(10, ge=1, le=50), city: str = "") -> dict[str, object]:
        selected_city = city or None
        results = [result.as_dict() for result in get_engine().search(q, limit=limit, city=selected_city)]
        return {"query": q, "city": selected_city, "count": len(results), "results": results}

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
    form { display: grid; grid-template-columns: 1fr 180px auto; gap: 8px; margin: 20px 0; }
    input, select { padding: 12px; border: 1px solid #c7ccd1; border-radius: 6px; font-size: 16px; background: white; }
    button { padding: 12px 16px; border: 0; border-radius: 6px; background: #155eef; color: white; font-size: 16px; }
    article { background: white; border: 1px solid #dde1e6; border-radius: 8px; padding: 16px; margin: 12px 0; }
    h1 { margin: 0; font-size: 32px; }
    h2 { margin: 0 0 8px; font-size: 18px; }
    a[target="_blank"] { display: inline-block; margin-top: 8px; color: #155eef; font-weight: 600; }
    mark { background: #fff1a8; }
    .meta { color: #5f6368; font-size: 14px; }
    @media (max-width: 720px) { form { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
<main>
  <h1>StaySmart</h1>
  <form id="search-form">
    <input id="query" name="q" placeholder="quiet room at night" required>
    <select id="city" name="city" aria-label="Location">
      <option value="">All locations</option>
    </select>
    <button>Search</button>
  </form>
  <section id="results"></section>
</main>
<script>
const form = document.querySelector("#search-form");
const results = document.querySelector("#results");
const city = document.querySelector("#city");
loadLocations();
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
      <h2>${escapeHtml(item.listing_name)}</h2>
      <div class="meta">${item.review_date} · score ${item.score.toFixed(3)}</div>
      <p>${item.snippet}</p>
      ${safeAirbnbUrl(item.listing_url) ? `<a href="${safeAirbnbUrl(item.listing_url)}" target="_blank" rel="noopener noreferrer">Open listing</a>` : ""}
    </article>
  `).join("") || "No matches.";
});
async function loadLocations() {
  const response = await fetch("/locations");
  if (!response.ok) return;
  const data = await response.json();
  city.insertAdjacentHTML("beforeend", data.locations.map((name) =>
    `<option value="${escapeHtml(name)}">${escapeHtml(name)}</option>`
  ).join(""));
}
function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
  }[char]));
}
function safeAirbnbUrl(value) {
  const text = String(value || "");
  return text.startsWith("https://www.airbnb.com/rooms/") ? text : "";
}
</script>
</body>
</html>"""


app = create_app()
