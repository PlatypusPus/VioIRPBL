from pathlib import Path

from staysmart.data import build_passages, corpus_stats, load_corpus, normalise_reviews
from staysmart.text import clean_text, split_passages, tokenize


def test_text_cleaning_tokenizing_and_passage_splitting():
    text = "Quiet&nbsp;room! <b>Good Wi-Fi</b> for work."

    assert clean_text(text) == "Quiet room! Good Wi-Fi for work."
    assert tokenize(text) == ["quiet", "room", "good", "wi", "fi", "for", "work"]
    assert split_passages(text) == ["Quiet room!", "Good Wi-Fi for work."]


def test_normalise_reviews_maps_inside_airbnb_rows():
    rows = [{"id": "r1", "listing_id": "10", "date": "2025-01-01", "comments": "Clean bathroom."}]
    listings = {"10": {"name": "Hotel Blue", "city": "Paris", "review_scores_rating": "4.8"}}

    reviews = normalise_reviews(rows, listings)

    assert reviews[0].review_id == "r1"
    assert reviews[0].listing_name == "Hotel Blue"
    assert reviews[0].city == "Paris"
    assert reviews[0].listing_url == "https://www.airbnb.com/rooms/10"


def test_load_corpus_filters_to_hotel_rooms(tmp_path: Path):
    (tmp_path / "reviews.csv").write_text(
        "id,listing_id,date,comments\nr1,1,2025-01-01,Quiet room\nr2,2,2025-01-01,Loud flat\n",
        encoding="utf-8",
    )
    (tmp_path / "listings.csv").write_text(
        "id,name,room_type,city\n1,Hotel One,Hotel room,Paris\n2,Flat Two,Entire home/apt,Paris\n",
        encoding="utf-8",
    )

    passages = load_corpus(tmp_path)

    assert [passage.listing_name for passage in passages] == ["Hotel One"]


def test_build_passages_and_stats():
    reviews = normalise_reviews(
        [{"review_id": "r1", "listing_id": "1", "listing_name": "Hotel", "review_text": "Clean. Quiet.", "review_date": "2025-01-01"}]
    )

    passages = build_passages(reviews)

    assert [passage.text for passage in passages] == ["Clean.", "Quiet."]
    assert corpus_stats(passages)["reviews"] == 1
