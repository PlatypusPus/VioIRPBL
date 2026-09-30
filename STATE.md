# StaySmart State

## Done
- Phase 0 complete: skeleton layout, pinned dependencies, pytest config, placeholder package and test.
- Phase 1 implemented: data loading, hotel-room filtering, schema normalization, deduplication, text cleaning, tokenization, passage splitting and corpus stats.
- Phase 2 implemented: positional index data, TF-IDF and BM25 with a test against installed `rank_bm25`.
- Phase 3 implemented: phrase and proximity scoring with score breakdowns.
- Phase 4 implemented: bounded recency weighting from a configurable reference date.
- Phase 5 implemented: highlighted snippets, metadata and CLI search.
- Phase 6 implemented: owner-judgment evaluation metrics and `eval/results.md` writer.
- Phase 7 implemented: FastAPI `/search` endpoint and minimal local web page.
- Index persistence implemented with `python -m staysmart.build_index`.
- Git repository initialised in `E:\Vio`.
- Verified dependency imports for FastAPI, scikit-learn, pytest, uvicorn and rank_bm25.

## Run
- Create environment: `python -m venv .venv`
- Activate on Windows PowerShell: `.venv\Scripts\Activate.ps1`
- Install dependencies: `python -m pip install -r requirements.txt`
- Run tests: `python -m pytest`
- Corpus stats: `python -m staysmart.data data/raw`
- Build index: `python -m staysmart.build_index data/raw data/processed/index.pkl`
- CLI search: `python -m staysmart.search "quiet room at night" --data data/raw --limit 5`
- API: `python -m uvicorn staysmart.api:app --reload`
- Evaluation: `python -m staysmart.evaluate data/raw eval/judgments.csv eval/results.md`

## Verified
- `python --version` -> `Python 3.14.0`
- `.venv\Scripts\python -m pip install -r requirements.txt` -> installed pinned requirements.
- `.venv\Scripts\python -m pytest` -> `12 passed, 1 warning in 3.36s`
- `.venv\Scripts\python -c "import fastapi, sklearn, pytest, uvicorn, rank_bm25; ..."` -> `fastapi 0.118.0; sklearn 1.7.2; pytest 8.4.2; uvicorn 0.37.0; rank_bm25 import ok`

## Decisions
- Use the handover defaults for Python 3.11+, `src/staysmart/`, `tests/`, `data/raw/`, `data/processed/`, and `eval/`.
- Keep `.venv` out of git.
- Use stdlib CSV/JSON loading instead of pandas.
- Persist the search engine with pickle because it is the smallest local index format for this submission.
- Keep evaluation dependent on owner judgments only.

## Known Issues
- No owner dataset is present in `data/raw/` yet.
- Real corpus size, cities, license and hotel-room coverage are unknown until the owner adds data.
- Evaluation cannot produce meaningful results until `eval/judgments.csv` is filled by the owner.
- API returns 503 until data or `STAYSMART_INDEX_PATH` is available.

## Next Phase
- Add the owner dataset to `data/raw/`, run corpus stats, fill judgments, then review result quality.
