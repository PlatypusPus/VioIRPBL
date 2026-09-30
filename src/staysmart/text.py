import html
import re


TAG_RE = re.compile(r"<[^>]+>")
TOKEN_RE = re.compile(r"[a-z0-9]+(?:'[a-z0-9]+)?")
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


def clean_text(value: object) -> str:
    text = "" if value is None else str(value)
    text = html.unescape(TAG_RE.sub(" ", text))
    return re.sub(r"\s+", " ", text).strip()


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(clean_text(text).lower())


def split_passages(text: str, window_size: int = 30) -> list[str]:
    cleaned = clean_text(text)
    if not cleaned:
        return []

    sentences = [part.strip() for part in SENTENCE_RE.split(cleaned) if part.strip()]
    passages: list[str] = []
    for sentence in sentences:
        tokens = sentence.split()
        if len(tokens) <= window_size:
            passages.append(sentence)
        else:
            passages.extend(" ".join(tokens[i : i + window_size]) for i in range(0, len(tokens), window_size))
    return passages

