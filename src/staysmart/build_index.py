import sys
from pathlib import Path

from .search import SearchEngine
from .store import save_engine


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    data_dir = Path(args[0]) if args else Path("data/raw")
    output = Path(args[1]) if len(args) > 1 else Path("data/processed/index.pkl")
    engine = SearchEngine.from_raw_dir(data_dir)
    save_engine(engine, output)
    print(f"wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

