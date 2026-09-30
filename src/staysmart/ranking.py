import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date

from sklearn.feature_extraction.text import TfidfVectorizer

from .data import Passage
from .text import tokenize


@dataclass(frozen=True)
class ScoreBreakdown:
    bm25: float
    tfidf: float
    phrase: float
    proximity: float
    recency: float
    final: float


class BM25:
    def __init__(self, documents: list[tuple[str, ...]], k1: float = 1.5, b: float = 0.75, epsilon: float = 0.25):
        self.documents = documents
        self.k1 = k1
        self.b = b
        self.doc_len = [len(document) for document in documents]
        self.avgdl = sum(self.doc_len) / len(self.doc_len) if self.doc_len else 0
        self.doc_freqs = [Counter(document) for document in documents]
        nd: Counter[str] = Counter()
        for freqs in self.doc_freqs:
            nd.update(freqs.keys())
        self.idf = _rank_bm25_idf(nd, len(documents), epsilon)

    def score(self, query: list[str], index: int) -> float:
        if not self.documents or not self.avgdl:
            return 0.0
        score = 0.0
        freqs = self.doc_freqs[index]
        doc_len = self.doc_len[index]
        for term in query:
            term_freq = freqs.get(term, 0)
            if term_freq:
                denominator = term_freq + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl)
                score += self.idf.get(term, 0.0) * (term_freq * (self.k1 + 1) / denominator)
        return score


class Ranker:
    def __init__(
        self,
        passages: list[Passage],
        reference_date: date | None = None,
        half_life_years: float = 2.0,
        recency_floor: float = 0.5,
    ):
        self.passages = passages
        self.reference_date = reference_date or date.today()
        self.half_life_years = half_life_years
        self.recency_floor = recency_floor
        self.bm25 = BM25([passage.tokens for passage in passages])
        self.positions = _positions(passages)
        self.vectorizer = TfidfVectorizer(tokenizer=tokenize, lowercase=False, token_pattern=None)
        corpus = [" ".join(passage.tokens) for passage in passages]
        self.tfidf = self.vectorizer.fit_transform(corpus) if corpus else None

    def score(self, query: str, index: int) -> ScoreBreakdown:
        query_tokens = tokenize(query)
        if not query_tokens:
            return ScoreBreakdown(0, 0, 0, 0, 1, 0)

        passage = self.passages[index]
        bm25 = self.bm25.score(query_tokens, index)
        tfidf = self._tfidf_score(query_tokens, index)
        phrase = phrase_score(query_tokens, passage.tokens)
        proximity = proximity_score(query_tokens, passage.tokens)
        recency = recency_factor(passage.review_date, self.reference_date, self.half_life_years, self.recency_floor)
        relevance = max(0.0, bm25) + (0.5 * tfidf) + phrase + proximity
        return ScoreBreakdown(bm25, tfidf, phrase, proximity, recency, relevance * recency)

    def _tfidf_score(self, query_tokens: list[str], index: int) -> float:
        if self.tfidf is None:
            return 0.0
        query_vector = self.vectorizer.transform([" ".join(query_tokens)])
        return float(self.tfidf[index].multiply(query_vector).sum())


def phrase_score(query_tokens: list[str], passage_tokens: tuple[str, ...]) -> float:
    if len(query_tokens) < 2 or len(query_tokens) > len(passage_tokens):
        return 0.0
    width = len(query_tokens)
    matches = sum(1 for i in range(len(passage_tokens) - width + 1) if list(passage_tokens[i : i + width]) == query_tokens)
    return float(matches)


def proximity_score(query_tokens: list[str], passage_tokens: tuple[str, ...]) -> float:
    required = set(query_tokens)
    if len(required) < 2 or not required.issubset(passage_tokens):
        return 0.0

    best_span = len(passage_tokens) + 1
    left = 0
    counts: Counter[str] = Counter()
    matched: list[tuple[int, str]] = [(i, token) for i, token in enumerate(passage_tokens) if token in required]
    for right, (position, token) in enumerate(matched):
        counts[token] += 1
        while len(counts) == len(required):
            start, start_token = matched[left]
            best_span = min(best_span, position - start + 1)
            counts[start_token] -= 1
            if counts[start_token] == 0:
                del counts[start_token]
            left += 1
    return len(required) / best_span if best_span <= len(passage_tokens) else 0.0


def recency_factor(value: str, reference_date: date, half_life_years: float = 2.0, floor: float = 0.5) -> float:
    try:
        review_date = date.fromisoformat(value[:10])
    except (TypeError, ValueError):
        return 1.0
    age_years = max(0.0, (reference_date - review_date).days / 365.25)
    return max(floor, 0.5 ** (age_years / half_life_years))


def _rank_bm25_idf(nd: Counter[str], corpus_size: int, epsilon: float) -> dict[str, float]:
    idf = {}
    idf_sum = 0.0
    negative = []
    for word, freq in nd.items():
        value = math.log(corpus_size - freq + 0.5) - math.log(freq + 0.5)
        idf[word] = value
        idf_sum += value
        if value < 0:
            negative.append(word)
    average_idf = idf_sum / len(idf) if idf else 0.0
    for word in negative:
        idf[word] = epsilon * average_idf
    return idf


def _positions(passages: list[Passage]) -> dict[str, dict[str, list[int]]]:
    index: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))
    for passage in passages:
        for position, token in enumerate(passage.tokens):
            index[token][passage.passage_id].append(position)
    return {term: dict(postings) for term, postings in index.items()}
