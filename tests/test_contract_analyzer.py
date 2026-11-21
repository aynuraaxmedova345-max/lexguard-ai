from pathlib import Path
from contract_analyzer import norm, classify_contract, split_clauses, _risk_signals, analyze_contract

BASE = Path(__file__).resolve().parents[1]
EXAMPLE = BASE / 'examples/namunaviy_mehnat_shartnomasi.txt'

def mock_retrieve(query, top_k, ids):
    assert ids == ['labor']
    return {'status': 'requires_source_verification', 'results': [{
        'doc_id': 'labor:16:1', 'document_name': 'Mehnat kodeksi', 'article_number': '16',
        'article_title': 'Shartnoma va qonunchilik', 'text': 'Mehnat huquqlari... ',
        'source_url': 'https://lex.uz/uz/docs/-6257288',
        'verification_status': 'source_export_not_compared'
    }], 'warnings': ['Matn amaldagi tahrirga to‘liq qiyoslanmagan.']}

def test_normalize_apostrophes():
    assert norm("O‘zbekiston") == norm("Oʻzbekiston")

def test_classify_labor():
    assert classify_contract(EXAMPLE.read_text()) == 'mehnat'

def test_split():
    clauses = split_clauses(EXAMPLE.read_text())
    assert len(clauses) >= 5

def test_risk_signal():
    assert any(r['signal'] == 'no_leave' for r in _risk_signals('Yillik mehnat ta\'tili berilmaydi.'))

def test_pipeline_mock():
    r = analyze_contract(EXAMPLE, retrieve=mock_retrieve, max_clauses=10)
    assert r['document_type'] == 'mehnat'
    assert r['risk_count'] >= 2
    assert r['source_verification_complete'] is False
    assert r['risks'][0]['legal_basis'][0]['verification_status'] != 'verified'
    assert all('source_url' in b for c in r['clauses'] for b in c['legal_basis'])

def test_docx_extraction(tmp_path):
    from docx import Document
    from contract_analyzer import extract_contract_text
    d = Document()
    d.add_paragraph('Mehnat shartnomasi. Ish beruvchi va xodim ish haqi, ta\'til va muddat haqida kelishuvga erishdi. Mehnat shartlari yozma shaklda qayd etiladi.')
    p = tmp_path / 'demo.docx'
    d.save(p)
    assert 'Mehnat shartnomasi' in extract_contract_text(p)

def test_pdf_extraction(tmp_path):
    import fitz
    from contract_analyzer import extract_contract_text
    p = tmp_path / 'demo.pdf'
    d = fitz.open(); page = d.new_page()
    page.insert_text((70, 70), 'Sample contract text for smoke test. ' * 4)
    d.save(p); d.close()
    assert 'Sample contract text' in extract_contract_text(p)
