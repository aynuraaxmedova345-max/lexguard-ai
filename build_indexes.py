"""Create actual offline BM25 and dense-approximation (TF-IDF + SVD) indexes.

Python dependencies: numpy, scipy, scikit-learn, joblib. No internet needed.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from collections import Counter
from datetime import date
from pathlib import Path

import joblib
import numpy as np
from scipy import sparse
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.preprocessing import normalize

from retriever import uz_tokenize

ROOT = Path(__file__).resolve().parent
CORPUS = ROOT / "data/legal_corpus_unified.jsonl"
IDX = ROOT / "indexes"


def build(rebuild: bool = True):
    IDX.mkdir(exist_ok=True)
    corpus_hash = hashlib.sha256(CORPUS.read_bytes()).hexdigest()
    rows = [json.loads(l) for l in CORPUS.open(encoding="utf8") if l.strip()]
    active_rows = [r for r in rows if r.get("is_active_in_index", True)]
    if len(active_rows) != len(rows):
        raise ValueError("All records must be active for row-aligned index. Regenerate corpus / filter at retrieval stage.")
    ids = [r['doc_id'] for r in rows]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate doc_id in source corpus")
    texts = [r['retrieval_text'] for r in rows]
    n = len(texts)
    print(f"Building BM25 for {n} units", flush=True)
    count_vec = CountVectorizer(tokenizer=uz_tokenize, token_pattern=None, lowercase=False,
                                max_features=110000, dtype=np.int32)
    counts = count_vec.fit_transform(texts).tocsr()
    doclens = np.asarray(counts.sum(axis=1)).ravel().astype(np.float32)
    average = float(doclens.mean())
    df = np.asarray((counts > 0).sum(axis=0)).ravel().astype(np.float32)
    idf = np.log(1 + (n - df + .5) / (df + .5)).astype(np.float32)
    k1, b = 1.5, .75
    data = counts.data.astype(np.float32)
    per_row = np.repeat(doclens, np.diff(counts.indptr))
    denom = data + k1 * (1 - b + b * per_row / average)
    data = data * (k1 + 1) / denom
    data *= idf[counts.indices]
    bm25 = sparse.csr_matrix((data, counts.indices.copy(), counts.indptr.copy()), shape=counts.shape)
    sparse.save_npz(IDX / "bm25_weights.npz", bm25, compressed=True)
    joblib.dump(count_vec, IDX / "bm25_vectorizer.joblib", compress=3)
    print(f"BM25 saved: {bm25.shape}, {bm25.nnz} weighted terms", flush=True)
    del counts, bm25

    print("Training offline LSA approximation (not a transformer embedding)...", flush=True)
    tfidf = TfidfVectorizer(tokenizer=uz_tokenize, token_pattern=None, lowercase=False,
                            ngram_range=(1, 2), min_df=2, max_df=.98, max_features=30000,
                            sublinear_tf=True, dtype=np.float32)
    X = tfidf.fit_transform(texts)
    dims = min(96, min(X.shape) - 1)
    model = TruncatedSVD(n_components=dims, n_iter=3, random_state=42)
    dense = model.fit_transform(X).astype(np.float32)
    dense = normalize(dense, norm='l2').astype(np.float32)
    np.save(IDX / "dense_lsa_vectors.npy", dense)
    joblib.dump(tfidf, IDX / "word_tfidf.joblib", compress=3)
    joblib.dump(model, IDX / "lsa_svd.joblib", compress=3)
    del X
    manifest = {
        'index_schema': 'lexguard-hybrid-v1',
        'source_corpus_sha256': corpus_hash,
        'indexed_at': date.today().isoformat(),
        'row_count': n,
        'document_ids': dict(Counter(r['document_id'] for r in rows)),
        'bm25_vocabulary': len(count_vec.vocabulary_),
        'bm25_parameters': {'k1': k1, 'b': b},
        'dense_model': 'TF-IDF word 1-2 grams + TruncatedSVD LSA (offline approximation, NOT neural semantic embeddings)',
        'dense_dimensions': dims,
        'embedding_storage': 'dense_lsa_vectors.npy',
        'chroma_status': 'requires import via build_chroma.py; not automatically created',
        'source_legal_verification': 'Not fully compared to live LexUZ; use per-record verification_status'
    }
    (IDX / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    print('Saved index manifest', flush=True)
    return manifest


if __name__ == '__main__':
    print(json.dumps(build(), ensure_ascii=False, indent=2))
