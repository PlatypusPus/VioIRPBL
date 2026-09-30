import pickle
from pathlib import Path


def save_engine(engine: object, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        pickle.dump(engine, handle)


def load_engine(path: Path) -> object:
    with path.open("rb") as handle:
        return pickle.load(handle)

