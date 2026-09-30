import argparse
import re
from dataclasses import asdict, dataclass
from datetime import date
from html import escape
from pathlib import Path

from .data import Passage, load_corpus
from .ranking import Ranker, ScoreBreakdown
from .store import load_engine
from .text import tokenize


@dataclass(frozen=True)
class SearchResult:
    review_id: str
    listing_id: str
    listing_name: str
    snippet: str
    review_date: str
    rating: str | None
    city: str | None
    score: float
    breakdown: ScoreBreakdown

    def as_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["breakdown"] = asdict(self.breakdown)
        return data


class SearchEngine:
    def __init__(self, passages: list[Passage], reference_date: date | None = None):
        self.passages = passages
        self.ranker = Ranker(passages, reference_date=reference_date)

    @classmethod
    def from_raw_dir(cls, raw_dir: Path, reference_date: date | None = None) -> "SearchEngine":
        return cls(load_corpus(raw_dir), reference_date=reference_date)

    def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        best_by_review: dict[str, SearchResult] = {}
        terms = tokenize(query)
        for index, passage in enumerate(self.passages):
            breakdown = self.ranker.score(query, index)
            if breakdown.final <= 0:
                continue
            result = SearchResult(
                review_id=passage.review_id,
                listing_id=passage.listing_id,
                listing_name=passage.listing_name,
                snippet=highlight(passage.text, terms),
                review_date=passage.review_date,
                rating=passage.rating,
                city=passage.city,
                score=breakdown.final,
                breakdown=breakdown,
            )
            previous = best_by_review.get(passage.review_id)
            if previous is None or result.score > previous.score:
                best_by_review[passage.review_id] = result
        return sorted(best_by_review.values(), key=lambda item: item.score, reverse=True)[:limit]


def highlight(text: str, terms: list[str]) -> str:
    escaped = escape(text)
    unique_terms = sorted(set(terms), key=len, reverse=True)
    if not unique_terms:
        return escaped
    pattern = re.compile(r"\b(" + "|".join(re.escape(term) for term in unique_terms) + r")\b", re.IGNORECASE)
    return pattern.sub(r"<mark>\1</mark>", escaped)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("--data", default="data/raw")
    parser.add_argument("--index")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--reference-date")
    args = parser.parse_args(argv)
    reference_date = date.fromisoformat(args.reference_date) if args.reference_date else None
    engine = load_engine(Path(args.index)) if args.index else SearchEngine.from_raw_dir(Path(args.data), reference_date=reference_date)
    for rank, result in enumerate(engine.search(args.query, limit=args.limit), 1):
        print(f"{rank}. {result.listing_name} ({result.review_date}) score={result.score:.3f}")
        print(f"   {result.snippet}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
