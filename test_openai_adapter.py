import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from openai_analyzer import analyze_contract_openai, _validate

QUOTE='Xodimning ta’til huquqi qonun bilan kafolatlanadi.'
ROW={'doc_id':'demo:1','document_name':'Sinov manbasi','article_number':'1','text':QUOTE,'source_url':'https://lex.uz/uz/docs/example','verification_status':'source_export_not_compared'}
CLAUSE={'clause_id':'C01','legal_basis':[ROW]}
ANSWER={'clause_id':'C01','status':'potential_risk','severity':'high','issue':'Ehtimoliy xavf','recommendation':'Tekshiring','citations':[{'evidence_id':'E1','quote':QUOTE}]}

def test_valid_quote():
    assert _validate(CLAUSE,ANSWER)['legal_basis'][0]['source_url']==ROW['source_url']

def test_fake_id():
    assert _validate(CLAUSE,{**ANSWER,'citations':[{'evidence_id':'E99','quote':QUOTE}]})['status']=='insufficient_evidence'

def test_fake_quote():
    assert _validate(CLAUSE,{**ANSWER,'citations':[{'evidence_id':'E1','quote':'Yetarlicha uzun, ammo uydirma jumla.'}]})['status']=='insufficient_evidence'

def test_no_evidence():
    assert _validate({**CLAUSE,'legal_basis':[]},ANSWER)['status']=='insufficient_evidence'

class Fake:
    def __init__(self,fail=False): self.responses=self; self.fail=fail
    def create(self, **kwargs):
        assert kwargs['store'] is False and kwargs['text']['format']['strict'] is True
        if self.fail: raise RuntimeError('mock API failure')
        clauses=json.loads(kwargs['input'])['clauses']
        return SimpleNamespace(status='completed',output_text=json.dumps({'assessments':[{**ANSWER,'clause_id':c['clause_id']} for c in clauses]}),usage=SimpleNamespace(input_tokens=100,output_tokens=20))

def mock_retrieve(query, top_k, ids): return {'results':[ROW], 'warnings':[], 'status':'requires_source_verification'}

@pytest.fixture
def doc(tmp_path):
    p=tmp_path/'demo.txt'; p.write_text('MEHNAT SHARTNOMASI\n1. Ish beruvchi va xodim ushbu shartnomada mehnat shartlarini belgilaydi.\n2. Xodimga ta’til berilmaydi.',encoding='utf-8'); return p

def test_pipeline(doc):
    r=analyze_contract_openai(doc,client=Fake(),consent=True,retrieve=mock_retrieve)
    assert r['api_calls']==1 and r['risk_count']==len(r['clauses']) and r['source_verification_complete'] is False
    assert r['coverage_complete'] and r['usage']['input_tokens']==100
    assert all(not x['legal_evidence_established'] for x in r['risks'])

def test_api_failure(doc):
    r=analyze_contract_openai(doc,client=Fake(True),consent=True,retrieve=mock_retrieve)
    assert r['api_errors'] and r['risk_count']==0 and r['insufficient_evidence_count']==len(r['clauses']) and r['rule_based_risks']

def test_consent(doc):
    with pytest.raises(ValueError): analyze_contract_openai(doc,client=Fake(),retrieve=mock_retrieve)
