import csv
import math
import sys
from collections import defaultdict
from pathlib import Path

from .search import SearchEngine


def precision_at_k(labels: list[int], k: int) -> float:
    top = labels[:k]
    return sum(1 for label in top if label > 0) / k if k else 0.0


def ndcg_at_k(labels: list[int], k: int) -> float:
    top = labels[:k]
    dcg = sum((2**label - 1) / math.log2(index + 2) for index, label in enumerate(top))
    ideal = sorted(labels, reverse=True)[:k]
    idcg = sum((2**label - 1) / math.log2(index + 2) for index, label in enumerate(ideal))
    return dcg / idcg if idcg else 0.0


def load_judgments(path: Path) -> dict[str, dict[str, int]]:
    judgments: dict[str, dict[str, int]] = defaultdict(dict)
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            judgments[row["query"]][row["review_id"]] = int(row["relevance"])
    return dict(judgments)


def evaluate(engine: SearchEngine, judgments: dict[str, dict[str, int]], k: int = 5) -> list[dict[str, object]]:
    rows = []
    for query, labels_by_review in judgments.items():
        results = engine.search(query, limit=k)
        labels = [labels_by_review.get(result.review_id, 0) for result in results]
        labels.extend([0] * (k - len(labels)))
        rows.append({"query": query, f"p@{k}": precision_at_k(labels, k), f"ndcg@{k}": ndcg_at_k(labels, k)})
    return rows


def write_results(rows: list[dict[str, object]], path: Path) -> None:
    lines = ["# Evaluation Results", "", "| Query | P@5 | nDCG@5 |", "|---|---:|---:|"]
    for row in rows:
        lines.append(f"| {row['query']} | {row['p@5']:.3f} | {row['ndcg@5']:.3f} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    data_dir = Path(args[0]) if args else Path("data/raw")
    judgments_path = Path(args[1]) if len(args) > 1 else Path("eval/judgments.csv")
    output_path = Path(args[2]) if len(args) > 2 else Path("eval/results.md")
    if not judgments_path.exists():
        print(f"missing judgments file: {judgments_path}", file=sys.stderr)
        return 1
    rows = evaluate(SearchEngine.from_raw_dir(data_dir), load_judgments(judgments_path))
    write_results(rows, output_path)
    print(f"wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

