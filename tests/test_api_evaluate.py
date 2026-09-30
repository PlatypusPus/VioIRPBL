from datetime import date

from fastapi.testclient import TestClient

from staysmart.api import create_app
from staysmart.data import build_passages, normalise_reviews
from staysmart.evaluate import evaluate, ndcg_at_k, precision_at_k
from staysmart.search import SearchEngine


def engine():
    passages = build_passages(
        normalise_reviews(
            [
                {
                    "review_id": "r1",
                    "listing_id": "1",
                    "listing_name": "Hotel One",
                    "review_text": "Quiet room and clean bathroom.",
                    "review_date": "2025-01-01",
                }
            ]
        )
    )
    return SearchEngine(passages, reference_date=date(2026, 1, 1))


def test_api_search_returns_ranked_results():
    client = TestClient(create_app(engine()))

    response = client.get("/search", params={"q": "quiet room"})

    assert response.status_code == 200
    assert response.json()["results"][0]["listing_name"] == "Hotel One"
    assert response.json()["results"][0]["listing_url"] == "https://www.airbnb.com/rooms/1"


def test_metrics_compute_precision_and_ndcg():
    assert precision_at_k([2, 0, 1], 3) == 2 / 3
    assert ndcg_at_k([2, 0, 1], 3) < 1


def test_evaluate_uses_owner_judgments():
    rows = evaluate(engine(), {"quiet room": {"r1": 2}}, k=1)

    assert rows == [{"query": "quiet room", "p@1": 1.0, "ndcg@1": 1.0}]
