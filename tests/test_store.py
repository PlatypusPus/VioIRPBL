from datetime import date

from staysmart.data import build_passages, normalise_reviews
from staysmart.search import SearchEngine
from staysmart.store import load_engine, save_engine


def test_engine_round_trips_through_pickle(tmp_path):
    passages = build_passages(
        normalise_reviews(
            [
                {
                    "review_id": "r1",
                    "listing_id": "1",
                    "listing_name": "Hotel",
                    "review_text": "Good wifi for work.",
                    "review_date": "2025-01-01",
                }
            ]
        )
    )
    path = tmp_path / "index.pkl"

    save_engine(SearchEngine(passages, reference_date=date(2026, 1, 1)), path)
    loaded = load_engine(path)

    assert loaded.search("wifi")[0].review_id == "r1"

