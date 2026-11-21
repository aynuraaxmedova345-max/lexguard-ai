"""Build REAL ChromaDB persistent collection on a computer with dependencies.

Modes:
 lsa - imports the included precomputed offline 96D vectors (no network/model).
 e5  - builds actual multilingual neural embeddings using multilingual-e5-small;
       requires sentence-transformers and one-time model download (~several hundred MB).
"""
import argparse
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent


def build(rebuild: bool = False, batch_size: int = 200, mode: str = 'lsa'):
    try:
        import chromadb
    except ImportError as e:
        raise SystemExit('ChromaDB mavjud emas. Internetda: pip install chromadb') from e
    manifest = json.loads((ROOT / 'indexes/manifest.json').read_text(encoding='utf8'))
    model = None
    embeddings = None
    if mode == 'lsa':
        embeddings = np.load(ROOT/'indexes/dense_lsa_vectors.npy', mmap_mode='r')
    elif mode == 'e5':
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as e:
            raise SystemExit('E5 uchun pip install sentence-transformers kerak') from e
        print('Loading intfloat/multilingual-e5-small', flush=True)
        model = SentenceTransformer('intfloat/multilingual-e5-small')
        model.max_seq_length = 512
    else:
        raise ValueError('mode lsa yoki e5 bo‘lishi kerak')
    p = ROOT/'indexes/chroma_db'
    client = chromadb.PersistentClient(path=str(p))
    name = f'lexguard_legal_{mode}'
    existing = {c.name for c in client.list_collections()}
    if name in existing and rebuild:
        client.delete_collection(name)
        existing.remove(name)
    if name in existing:
        raise SystemExit('ChromaDB oldin yaratilgan. Yangilash uchun --rebuild ni qo‘shing.')
    collection = client.create_collection(name=name, metadata={
        'hnsw:space': 'cosine', 'corpus_sha256': manifest['source_corpus_sha256'],
        'embedding_mode': mode,
    })
    corpus = [json.loads(l) for l in (ROOT/'data/legal_corpus_unified.jsonl').open(encoding='utf8') if l.strip()]
    if mode == 'lsa':
        assert len(corpus) == embeddings.shape[0]
    for st in range(0, len(corpus), batch_size):
        batch = corpus[st:st+batch_size]
        metadata = [{
            'document_id': r['document_id'],
            'document_name': r['document_name'],
            'article_number': r['article_number'],
            'source_url': r.get('source_url') or r.get('source_document_url') or '',
            'verification_status': r.get('verification_status') or 'unknown',
            'legal_domain': r.get('legal_domain') or '',
        } for r in batch]
        if mode == 'lsa':
            vector_batch = np.asarray(embeddings[st:st+len(batch)], dtype=np.float32)
        else:
            vector_batch = model.encode(
                ['passage: ' + r['retrieval_text'] for r in batch],
                normalize_embeddings=True, batch_size=min(batch_size, 32), show_progress_bar=False,
            )
        collection.upsert(
            ids=[r['doc_id'] for r in batch],
            documents=[r['retrieval_text'] for r in batch],
            embeddings=vector_batch.tolist(),
            metadatas=metadata,
        )
        print(f'ChromaDB ({mode}): {min(st+batch_size, len(corpus))}/{len(corpus)}', flush=True)
    assert collection.count() == len(corpus), (collection.count(), len(corpus))
    manifest_path = ROOT/'indexes/manifest.json'
    manifest[f'chroma_{mode}_status'] = 'created'
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf8')
    print(f'ChromaDB ready: {p}  collection={name} rows={collection.count()}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--rebuild', action='store_true')
    parser.add_argument('--batch-size', type=int, default=200)
    parser.add_argument('--mode', choices=['lsa', 'e5'], default='lsa')
    args = parser.parse_args()
    build(args.rebuild, args.batch_size, args.mode)
