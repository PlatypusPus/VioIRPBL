import csv
import gzip
import json
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .text import clean_text, split_passages, tokenize


REQUIRED_FIELDS = {"review_id", "listing_id", "listing_name", "review_text", "review_date"}
HOTEL_ROOM_TYPES = {"hotel room"}


@dataclass(frozen=True)
class Review:
    review_id: str
    listing_id: str
    listing_name: str
    review_text: str
    review_date: str
    rating: str | None = None
    city: str | None = None


@dataclass(frozen=True)
class Passage:
    passage_id: str
    review_id: str
    listing_id: str
    listing_name: str
    text: str
    tokens: tuple[str, ...]
    review_date: str
    rating: str | None = None
    city: str | None = None


def read_rows(path: Path) -> list[dict[str, str]]:
    if path.suffixes[-2:] == [".csv", ".gz"]:
        with gzip.open(path, "rt", newline="", encoding="utf-8-sig") as handle:
            return list(csv.DictReader(handle))
    if path.suffix.lower() == ".jsonl":
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else data["reviews"]
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def normalise_reviews(rows: Iterable[dict[str, object]], listings: dict[str, dict[str, object]] | None = None) -> list[Review]:
    reviews: list[Review] = []
    seen: set[str] = set()
    listings = listings or {}

    for row in rows:
        listing_id = str(row.get("listing_id") or "").strip()
        listing = listings.get(listing_id, {})
        review_id = str(row.get("review_id") or row.get("id") or "").strip()
        review_text = clean_text(row.get("review_text") or row.get("comments"))
        review_date = str(row.get("review_date") or row.get("date") or "").strip()
        listing_name = clean_text(row.get("listing_name") or listing.get("name"))

        if not review_id or review_id in seen or not review_text:
            continue
        seen.add(review_id)
        reviews.append(
            Review(
                review_id=review_id,
                listing_id=listing_id,
                listing_name=listing_name,
                review_text=review_text,
                review_date=review_date,
                rating=_optional(row.get("rating") or row.get("review_scores_rating") or listing.get("review_scores_rating")),
                city=_optional(row.get("city") or listing.get("city") or listing.get("neighbourhood_cleansed")),
            )
        )

    missing = REQUIRED_FIELDS - {field for review in reviews for field, value in review.__dict__.items() if value}
    if missing:
        raise ValueError(f"missing required fields: {', '.join(sorted(missing))}")
    return reviews


def load_listings(path: Path) -> dict[str, dict[str, object]]:
    rows = read_rows(path)
    hotels = {}
    for row in rows:
        listing_id = str(row.get("listing_id") or row.get("id") or "").strip()
        room_type = str(row.get("room_type") or "").strip().lower()
        if listing_id and room_type in HOTEL_ROOM_TYPES:
            hotels[listing_id] = row
    return hotels


def load_corpus(raw_dir: Path) -> list[Passage]:
    review_path = _first_existing(raw_dir, ("reviews.csv", "reviews.csv.gz", "reviews.jsonl", "reviews.json"))
    listing_path = _first_existing(raw_dir, ("listings.csv", "listings.csv.gz", "listings.jsonl", "listings.json"), required=False)
    listings = load_listings(listing_path) if listing_path else {}
    reviews = normalise_reviews(read_rows(review_path), listings or None)
    if listings:
        reviews = [review for review in reviews if review.listing_id in listings]
    return build_passages(reviews)


def build_passages(reviews: Iterable[Review], window_size: int = 30) -> list[Passage]:
    passages: list[Passage] = []
    for review in reviews:
        for index, text in enumerate(split_passages(review.review_text, window_size=window_size)):
            tokens = tuple(tokenize(text))
            if tokens:
                passages.append(
                    Passage(
                        passage_id=f"{review.review_id}:{index}",
                        review_id=review.review_id,
                        listing_id=review.listing_id,
                        listing_name=review.listing_name,
                        text=text,
                        tokens=tokens,
                        review_date=review.review_date,
                        rating=review.rating,
                        city=review.city,
                    )
                )
    return passages


def corpus_stats(passages: list[Passage]) -> dict[str, float]:
    review_ids = {passage.review_id for passage in passages}
    listing_ids = {passage.listing_id for passage in passages}
    token_counts = [len(passage.tokens) for passage in passages]
    return {
        "passages": len(passages),
        "reviews": len(review_ids),
        "listings": len(listing_ids),
        "avg_tokens": round(sum(token_counts) / len(token_counts), 2) if token_counts else 0.0,
    }


def _first_existing(raw_dir: Path, names: tuple[str, ...], required: bool = True) -> Path | None:
    for name in names:
        path = raw_dir / name
        if path.exists():
            return path
    if required:
        raise FileNotFoundError(f"expected one of {', '.join(names)} in {raw_dir}")
    return None


def _optional(value: object) -> str | None:
    text = clean_text(value)
    return text or None


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    raw_dir = Path(args[0]) if args else Path("data/raw")
    passages = load_corpus(raw_dir)
    print(corpus_stats(passages))
    for passage in random.Random(0).sample(passages, min(20, len(passages))):
        print(_console_safe(f"{passage.passage_id}\t{passage.listing_name}\t{passage.text}"))
    return 0


def _console_safe(value: str) -> str:
    encoding = sys.stdout.encoding or "utf-8"
    return value.encode(encoding, errors="replace").decode(encoding)


if __name__ == "__main__":
    raise SystemExit(main())
