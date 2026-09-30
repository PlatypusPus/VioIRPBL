from datetime import date

import pytest
from rank_bm25 import BM25Okapi

from staysmart.data import build_passages, normalise_reviews
from staysmart.ranking import BM25, phrase_score, proximity_score, recency_factor
from staysmart.search import SearchEngine


def passages():
    return build_passages(
        normalise_reviews(
            [
                {
                    "review_id": "old-good",
                    "listing_id": "1",
                    "listing_name": "Quiet Hotel",
                    "review_text": "The clean bathroom was spotless and the room was quiet all night.",
                    "review_date": "2020-01-01",
                },
                {
                    "review_id": "new-weak",
                    "listing_id": "2",
                    "listing_name": "New Hotel",
                    "review_text": "The bathroom exists.",
                    "review_date": "2025-01-01",
                },
                {
                    "review_id": "far",
                    "listing_id": "3",
                    "listing_name": "Far Hotel",
                    "review_text": "Clean lobby with a long corridor and many stairs before the bathroom.",
                    "review_date": "2025-01-01",
                },
            ]
        )
    )


def test_bm25_matches_installed_rank_bm25():
    corpus = [("clean", "bathroom"), ("quiet", "room")]
    ours = BM25(corpus)
    theirs = BM25Okapi([list(document) for document in corpus])

    assert ours.score(["clean"], 0) == pytest.approx(float(theirs.get_scores(["clean"])[0]))


def test_phrase_and_proximity_prefer_adjacent_terms():
    adjacent = ("clean", "bathroom")
    far = ("clean", "room", "with", "old", "bathroom")

    assert phrase_score(["clean", "bathroom"], adjacent) > phrase_score(["clean", "bathroom"], far)
    assert proximity_score(["clean", "bathroom"], adjacent) > proximity_score(["clean", "bathroom"], far)


def test_recency_is_bounded_and_missing_dates_are_neutral():
    reference = date(2026, 1, 1)

    assert recency_factor("2025-01-01", reference) > recency_factor("2010-01-01", reference)
    assert recency_factor("2010-01-01", reference) == 0.5
    assert recency_factor("", reference) == 1.0


def test_search_deduplicates_reviews_and_keeps_relevance_over_weak_recency():
    engine = SearchEngine(passages(), reference_date=date(2026, 1, 1))

    results = engine.search("clean bathroom", limit=3)

    assert results[0].review_id == "old-good"
    assert "<mark>clean</mark> <mark>bathroom</mark>" in results[0].snippet.lower()
    assert len({result.review_id for result in results}) == len(results)

