"""LexGuard AI: transparent, source-grounded hybrid retrieval.

Offline BM25 + LSA dense vectors are *both functional* without ChromaDB.
Optional ChromaDB backend uses exactly the same persisted LSA vectors.
LSA is NOT a multilingual neural embedding model; see README.
"""
from __future__ import annotations

import json
import hashlib
import re
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
from scipy import sparse
from sklearn.preprocessing import normalize

HERE = Path(__file__).resolve().parent
CORPUS = HERE / "data" / "legal_corpus_unified.jsonl"
INDEX = HERE / "indexes"

APOS = str.maketrans({"‘": "'", "’": "'", "ʻ": "'", "ʼ": "'", "`": "'", "´": "'", "ʹ": "'"})
WORD_PATTERN = re.compile(r"[^\W_]+(?:'[^\W_]+)*", re.UNICODE)


def normalize_uz(text: str) -> str:
    return text.casefold().translate(APOS).replace("–", "-").replace("—", "-")


def uz_tokenize(text: str) -> list[str]:
    return WORD_PATTERN.findall(normalize_uz(text))


def row_is_preferred(row: dict, preferred: set[str]) -> bool:
    return row.get('document_id') in preferred


def _normal_article(s: str) -> str:
    s = normalize_uz(str(s)).replace("⁰", "0").replace("¹", "1").replace("²", "2")
    return re.sub(r"\s+", "", s).replace("-modda", "").replace("modda", "").strip(". -")


class LegalRetriever:
    def __init__(self, root: str | Path = HERE, backend: str = "offline"):
        self.root = Path(root)
        self.idx = self.root / "indexes"
        self.rows = [json.loads(l) for l in (self.root / "data/legal_corpus_unified.jsonl").open(encoding="utf-8") if l.strip()]
        self.bm25 = sparse.load_npz(self.idx / "bm25_weights.npz").tocsr()
        self.bm25_vectorizer = joblib.load(self.idx / "bm25_vectorizer.joblib")
        self.word_tfidf = joblib.load(self.idx / "word_tfidf.joblib")
        self.svd = joblib.load(self.idx / "lsa_svd.joblib")
        self.dense = np.load(self.idx / "dense_lsa_vectors.npy", mmap_mode="r")
        with (self.idx / "manifest.json").open(encoding="utf8") as f:
            self.manifest = json.load(f)
        if len(self.rows) != self.bm25.shape[0] or len(self.rows) != self.dense.shape[0]:
            raise ValueError("Korpus va indeks hajmlari farq qiladi. python build_indexes.py ni bajaring.")
        current_sha = hashlib.sha256((self.root / "data/legal_corpus_unified.jsonl").read_bytes()).hexdigest()
        if current_sha != self.manifest.get("source_corpus_sha256"):
            raise ValueError("Huquqiy korpus o‘zgargan. Eski indeksni ishlatmang; python build_indexes.py ni qayta bajaring.")
        self.ids = {r['doc_id']: i for i, r in enumerate(self.rows)}
        self.backend = backend
        self.collection = None
        if backend in ("chroma", "chroma_e5"):
            try:
                import chromadb
            except ImportError as exc:
                raise RuntimeError("ChromaDB o‘rnatilmagan: pip install chromadb; python build_chroma.py") from exc
            client = chromadb.PersistentClient(path=str(self.idx / "chroma_db"))
            name = "lexguard_legal_e5" if backend == "chroma_e5" else "lexguard_legal_lsa"
            self.collection = client.get_collection(name)
            if (self.collection.metadata or {}).get('corpus_sha256') != current_sha:
                raise ValueError('ChromaDB korpusi o‘zgargan; python build_chroma.py --rebuild')
            if self.collection.count() != len(self.rows):
                raise ValueError("ChromaDB indeksida yozuvlar soni noto‘g‘ri; build_chroma.py --rebuild")
        self.by_article = {}
        for i, row in enumerate(self.rows):
            self.by_article.setdefault((row["document_id"], row["article_number"]), []).append(i)

    def _vector(self, query: str) -> np.ndarray:
        if self.backend == "chroma_e5":
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:
                raise RuntimeError('pip install sentence-transformers talab qilinadi') from exc
            if not hasattr(self, '_e5_model'):
                self._e5_model = SentenceTransformer('intfloat/multilingual-e5-small')
            return np.asarray(self._e5_model.encode(['query: '+query], normalize_embeddings=True)[0], dtype=np.float32)
        q = self.word_tfidf.transform([query])
        vec = self.svd.transform(q).astype(np.float32)
        return normalize(vec, norm="l2")[0]

    def _bm25_search(self, query: str, allowed: np.ndarray, n: int) -> list[int]:
        q = self.bm25_vectorizer.transform([query])
        if q.nnz == 0:
            return []
        q.data.fill(1)
        scores = (self.bm25 @ q.T).toarray().ravel()
        scores[~allowed] = -np.inf
        k = min(n, int(allowed.sum()))
        if k < 1:
            return []
        indices = np.argpartition(-scores, k-1)[:k]
        return [int(i) for i in indices[np.argsort(-scores[indices])]
                if np.isfinite(scores[i]) and scores[i] > 0]

    def _dense_search(self, query: str, allowed: np.ndarray, n: int) -> list[int]:
        vec = self._vector(query)
        if not np.any(vec):
            return []
        if self.collection is not None:
            count = min(len(self.rows), max(n * 8, 100))
            result = self.collection.query(query_embeddings=[vec.tolist()], n_results=count, include=["distances"])
            out = [self.ids[i] for i in result['ids'][0] if i in self.ids and allowed[self.ids[i]]]
            return out[:n]
        scores = np.asarray(self.dense @ vec)
        scores[~allowed] = -np.inf
        k = min(n, int(allowed.sum()))
        if k < 1:
            return []
        indices = np.argpartition(-scores, k-1)[:k]
        return [int(i) for i in indices[np.argsort(-scores[indices])]
                if np.isfinite(scores[i]) and scores[i] > 0]

    def search(self, query: str, top_k: int = 5, domain: str | None = None,
               document_ids: list[str] | None = None, article_number: str | None = None,
               group_by_article: bool = True, include_full_article: bool = False,
               use_domain_hints: bool = True) -> list[dict]:
        if not query or not query.strip():
            return []
        if not 1 <= top_k <= 100:
            raise ValueError("top_k 1 dan 100 gacha bo‘lishi kerak")
        allowed = np.array([r.get("is_active_in_index", True)
                            and (not domain or r.get("legal_domain") == domain)
                            and (not document_ids or r.get("document_id") in document_ids)
                            and (article_number is None or _normal_article(r["article_number"]) == _normal_article(article_number))
                            for r in self.rows], dtype=bool)
        if not allowed.any():
            return []
        # More candidates are needed to deduplicate many clauses of one article.
        pool = min(len(self.rows), max(top_k * 25, 160))
        bm = self._bm25_search(query, allowed, pool)
        dense = self._dense_search(query, allowed, pool)
        # Article-level reciprocal rank fusion: multiple paragraphs of a long article
        # must not crowd out other relevant legal norms.
        scores = {}
        representatives = {}
        for weight, ranked in ((0.82, bm), (0.18, dense)):
            unique_articles = []
            seen_modality = set()
            for index in ranked:
                r = self.rows[index]
                key = (r["document_id"], r["article_number"]) if group_by_article else (index,)
                if key in seen_modality:
                    continue
                seen_modality.add(key)
                unique_articles.append((key, index))
            for rank, (key, index) in enumerate(unique_articles, start=1):
                scores[key] = scores.get(key, 0.0) + weight / (60 + rank)
                # Prefer the BM25-matching clause as an evidence excerpt.
                representatives.setdefault(key, index)
        # Soft, explainable legal-domain hints; never exclude other codes.
        qwords = set(uz_tokenize(query))
        preferred = set()
        if any(w.startswith("ijara") for w in qwords):
            preferred.update(("civil_2", "housing"))
        if any(w.startswith("mehnat") or w.startswith("xodim") for w in qwords):
            preferred.add("labor")
        if any(w.startswith("nikoh") or w.startswith("er-xotin") for w in qwords):
            preferred.add("family")
        if ("uy" in qwords or "uy-joy" in normalize_uz(query) or "turar" in qwords) and                 not any(w.startswith("mehnat") for w in qwords):
            preferred.add("housing")
        if ({"oldi", "sotdi"} <= qwords or "sotuvchi" in qwords or "sotib" in qwords):
            preferred.add("civil_2")
        for key, idx in representatives.items():
            row = self.rows[idx]
            if use_domain_hints and row['document_id'] in preferred:
                scores[key] += .0040
            title = normalize_uz(row.get('article_title') or '')
            if len(query.strip()) >= 9 and normalize_uz(query).strip() in title:
                scores[key] += .0030
        ranked_keys = sorted(scores, key=lambda key: scores[key], reverse=True)
        ranked = [representatives[key] for key in ranked_keys]
        indexed_scores = {representatives[key]: scores[key] for key in ranked_keys}
        # A numeric article filter is safest; do not infer article numbers from arbitrary numbers in query.
        results, seen_articles = [], set()
        for i in ranked:
            r = self.rows[i]
            art = (r["document_id"], r["article_number"])
            if group_by_article and art in seen_articles:
                continue
            seen_articles.add(art)
            out = {
                "doc_id": r["doc_id"],
                "document_id": r["document_id"],
                "document_name": r["document_name"],
                "article_number": r["article_number"],
                "article_title": r.get("article_title"),
                "part_number": r.get("part_number"),
                "text": r["text"],
                "source_url": r.get("source_url") or r.get("source_document_url"),
                "source_document_url": r.get("source_document_url"),
                "verification_status": r.get("verification_status", "unknown"),
                "version_date": r.get("version_date"),
                "rrf_score": round(float(indexed_scores[i]), 8),
                "is_legally_verified": r.get("verification_status") == "verified",
                "retrieval_backend": ("bm25+chroma-e5" if self.backend == "chroma_e5" else "bm25+chroma-lsa") if self.collection is not None else "bm25+local-lsa",
                "domain_hint_applied": bool(use_domain_hints and row_is_preferred(r, preferred)),
            }
            if include_full_article:
                siblings = self.by_article[art]
                # 20k characters cap is for prompt safety; truncate is announced.
                merged = "\n".join(self.rows[j]["text"] for j in siblings)
                out["article_full_text"] = merged[:20000]
                out["article_truncated"] = len(merged) > 20000
            results.append(out)
            if len(results) >= top_k:
                break
        return results


@lru_cache(maxsize=2)
def _instance(backend: str) -> LegalRetriever:
    return LegalRetriever(backend=backend)


def search_law(query: str, top_k: int = 5, backend: str = "offline", **kwargs) -> list[dict]:
    """Main API for AI Engineer. No LLM or network calls here."""
    return _instance(backend).search(query, top_k=top_k, **kwargs)


if __name__ == "__main__":
    import argparse
    a = argparse.ArgumentParser(description="LexGuard qonun qidiruvi")
    a.add_argument("query", nargs="?", default="Ijara shartnomasini bekor qilish")
    a.add_argument("--backend", choices=["offline", "chroma", "chroma_e5"], default="offline")
    a.add_argument("--top-k", type=int, default=5)
    a.add_argument("--domain", default=None)
    a.add_argument("--article", default=None)
    args = a.parse_args()
    print(json.dumps(search_law(args.query, args.top_k, backend=args.backend, domain=args.domain,
                                article_number=args.article), ensure_ascii=False, indent=2))
