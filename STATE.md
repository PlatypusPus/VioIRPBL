# StaySmart State

## Done
- Phase 0 complete: skeleton layout, pinned dependencies, pytest config, placeholder package and test.
- Git repository initialised in `E:\Vio`.
- Verified dependency imports for FastAPI, scikit-learn, pytest, uvicorn and rank_bm25.

## Run
- Create environment: `python -m venv .venv`
- Activate on Windows PowerShell: `.venv\Scripts\Activate.ps1`
- Install dependencies: `python -m pip install -r requirements.txt`
- Run tests: `python -m pytest`

## Verified
- `python --version` -> `Python 3.14.0`
- `.venv\Scripts\python -m pip install -r requirements.txt` -> installed pinned requirements.
- `.venv\Scripts\python -m pytest` -> `1 passed in 0.05s`
- `.venv\Scripts\python -c "import fastapi, sklearn, pytest, uvicorn, rank_bm25; ..."` -> `fastapi 0.118.0; sklearn 1.7.2; pytest 8.4.2; uvicorn 0.37.0; rank_bm25 import ok`

## Decisions
- Use the handover defaults for Python 3.11+, `src/staysmart/`, `tests/`, `data/raw/`, `data/processed/`, and `eval/`.
- Keep `.venv` out of git.

## Known Issues
- No owner dataset is present in `data/raw/` yet.
- Later phases still need owner answers on dataset, cities, deadline, required deliverables, and rubric.

## Next Phase
- Wait for approval before Phase 1 data loading and preprocessing.
