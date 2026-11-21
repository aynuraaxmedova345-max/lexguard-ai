from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from retriever import search_law, LegalRetriever, uz_tokenize


def test_index_row_count():
    r = LegalRetriever()
    assert len(r.rows) == 8071
    assert r.bm25.shape[0] == len(r.rows)
    assert r.dense.shape[0] == len(r.rows)


def test_hybrid_search_grounded():
    res = search_law('mehnat shartnomasini bekor qilish tartibi', 5)
    assert res
    assert all(item['source_url'].startswith('https://lex.uz/') for item in res)
    assert all('verification_status' in item for item in res)
    assert all(item['rrf_score'] > 0 for item in res)


def test_specific_new_amendment():
    res = search_law('Mehnat va mashg‘ulotlar sohasida shahvoniy shilqimlikka yo‘l qo‘ymaslik', 5,
                     document_ids=['labor'], article_number='8-1')
    assert res
    assert all(x['article_number'] == '8-1' for x in res)
    assert 'shahvoniy shilqimlik' in res[0]['text']


def test_full_article_context():
    res = search_law('Nikoh shartnomasi', 3, document_ids=['family'], include_full_article=True)
    assert res
    assert all('article_full_text' in r for r in res)


def test_filters_and_empty():
    assert search_law('', top_k=4) == []
    assert search_law('ijara', document_ids=['nonexistent']) == []
    res = search_law('Ijara shartnomasini bekor qilish', top_k=5, document_ids=['civil_2'])
    assert all(r['document_id'] == 'civil_2' for r in res)


def test_dedup_articles():
    res = search_law('Ish vaqti ta’til mehnat', 10)
    assert len({(x['document_id'], x['article_number']) for x in res}) == len(res)


def test_normalized_apostrophes():
    assert uz_tokenize("O‘zbekiston O'zbekiston Oʻzbekiston") == ["o'zbekiston"] * 3


def test_ijara_routes_to_civil_or_housing():
    r = search_law('Ijara shartnomasini bekor qilish', top_k=3)
    assert r[0]['document_id'] in ('civil_2', 'housing')
    assert r[0]['article_number'] in ('615', '78', '69')


def test_labor_amendment_top_result():
    r = search_law('Shahvoniy shilqimlik mehnat ish joyida', top_k=3)
    assert r[0]['document_id'] == 'labor'
    assert r[0]['article_number'] == '8-1'


def test_nikoh_shartnomasi_tuzish():
    r = search_law('Nikoh shartnomasi tuzish tartibi', top_k=3)
    assert r[0]['document_id'] == 'family'
    assert r[0]['article_number'] == '30'
