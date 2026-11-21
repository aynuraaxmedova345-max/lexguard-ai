from pathlib import Path
from types import SimpleNamespace
import json
import pytest
from openai_analyzer_v31 import validate,bounded_rule,prepare_clause,analyze_contract_openai,_api
from legal_retrieval_v3 import ScopedRetriever
from contract_analyzer import extract_contract_text,split_clauses
ROOT=Path(__file__).resolve().parent
if not (ROOT/'data').exists():ROOT=ROOT.parent/'v3work'
@pytest.fixture(scope='module')
def engine():return ScopedRetriever(ROOT,'offline')
def base(eid,issue='Huquqiy xavf mavjud.'):
    return {'status':'potential_risk','severity':'high','issue':issue,'recommendation':'Shartni qayta ko‘ring.','rule_application':'Norma bilan solishtiring.','citations':[eid]}
def prepared(engine,doc,article,text):return prepare_clause({'clause_id':'C01','text':text},[engine.article(doc,article)],[text])
@pytest.mark.parametrize('issue,ok',[('Mehnat kodeksining 130-moddasiga zid.',True),('130-modda talabiga zid.',True),('999-modda talabiga zid.',False),('Oila kodeksining 130-moddasiga zid.',False),('https://example.com',False),('999 va 130-moddalar.',False)])
def test_citations(engine,issue,ok):
    c=prepared(engine,'labor','130','Dastlabki sinov muddati olti oy.')
    assert (validate(c,base('labor:130:0001',issue))['diagnostic_reason']=='accepted')==ok

def test_invalid_id(engine):
    c=prepared(engine,'labor','130','Dastlabki sinov muddati olti oy.')
    assert validate(c,base('fake'))['diagnostic_reason']=='invalid_evidence_id'
@pytest.mark.parametrize('text', ['4. Shartnomaning muddati. Mehnat shartnomasi nomuayyan muddatga tuziladi.', '2. Shartnoma muddati. Shartnoma nomuayyan muddatga tuziladi. Xodim 2026-yil 1-dekabrdan ish boshlaydi.','2. Shartnoma muddati. Shartnoma nomuayyan muddatga tuziladi. Xodim 2026-yil 23-noyabrdan ishga kirishadi.'])
def test_indefinite(engine,text):
    c=prepared(engine,'labor','110',text)
    assert bounded_rule(c,'mehnat',text)['status']=='no_obvious_risk'
    c['text']+=' Ish beruvchi xodimga ish haqi to‘lamaydi.'
    assert bounded_rule(c,'mehnat',c['text']) is None

def test_trial(engine):
    c=prepared(engine,'labor','130','Dastlabki sinov muddati olti oy etib belgilanadi.')
    assert bounded_rule(c,'mehnat','Xodim mutaxassis lavozimiga qabul qilinadi.')['status']=='potential_risk'
    assert bounded_rule(c,'mehnat','Xodim bosh buxgalter lavozimiga qabul qilinadi.') is None
    assert bounded_rule(c,'mehnat','Lavozim ko‘rsatilmagan.') is None

def test_service(engine):
    c=prepared(engine,'civil_2','707','Ijrochi kursni muddatidan oldin tugatishni talab qilishga haqli. Buyurtmachining aybi bo‘lmagan taqdirda ham zarar qoplanmaydi.')
    assert bounded_rule(c,'xizmat',c['text'])['status']=='potential_risk'
    c['text']=c['text'].replace('bo‘lmagan','bo‘lgan');assert bounded_rule(c,'xizmat',c['text']) is None

class Fake:
    def __init__(self,invalid=False):self.calls=[];self.invalid=invalid
    def create(self,**kwargs):
        p=json.loads(kwargs['input']); self.calls.append([c['clause_id'] for c in p['clauses']]);out={}
        for c in p['clauses']:
            out[c['clause_id']]=base(c['evidence'][0]['id'])
            if self.invalid and len(self.calls)==1 and c['clause_id']=='C02':out[c['clause_id']]['issue']='999-modda.'
        return SimpleNamespace(status='completed',output_text=json.dumps({'assessments':out}),usage=SimpleNamespace(input_tokens=100,output_tokens=20))
def test_smart_retry(engine):
    c=prepared(engine,'labor','130','Dastlabki sinov muddati olti oy.')
    c2={**c,'clause_id':'C02'}; fake=Fake(True);r={'api_calls':0,'api_errors':[],'retry_count':0,'usage':{'input_tokens':0,'output_tokens':0}}
    raw=_api(SimpleNamespace(responses=fake),'mock',[c,c2],'ctx','mehnat','mehnat','draft_or_sample',r)
    assert fake.calls==[['C01','C02'],['C02']]
    assert validate(c2,raw['C02'])['diagnostic_reason']=='accepted'
    assert c2['diagnostic_attempts'][0]['reason']=='unmatched_reference_in_text'
    assert r['retry_count']==1

def test_end_to_end(engine,tmp_path):
    p=tmp_path/'demo.txt';p.write_text('MEHNAT SHARTNOMASI. Ish beruvchi va xodim mazkur mehnat shartnomasini tuzdilar.\n1. Shartnoma nomuayyan muddatga tuziladi.',encoding='utf8')
    fake=Fake();r=analyze_contract_openai(p,client=SimpleNamespace(responses=fake),retriever=engine,consent=True,clause_ids=['C02'])
    assert r['version']=='contract-v3.1' and not r['coverage_complete']
    assert r['clauses'][0]['ai_assessment']['status']=='no_obvious_risk'
    assert r['rule_changes']==1 and len(r['clauses'][0]['diagnostic_attempts'])==2

def test_api(monkeypatch):
    from fastapi.testclient import TestClient
    import lexguard_api as api
    monkeypatch.setenv('LEXGUARD_DEMO_TOKEN','testtoken')
    monkeypatch.setattr(api,'engine',lambda:None);monkeypatch.setattr(api,'api_client',lambda:None)
    monkeypatch.setattr(api,'analyze_contract_openai',lambda *a,**k:{'filename':'temp.txt','clauses':[],'risk_count':0,'version':'contract-v3.1'})
    t=TestClient(api.app); assert t.get('/health').status_code==200
    f={'file':('test.txt',b'contract','text/plain')}
    assert t.post('/analyze',files=f,data={'consent':'true'}).status_code==401
    h={'X-Demo-Token':'testtoken'}
    assert t.post('/analyze',files=f,data={'consent':'false'},headers=h).status_code==400
    r=t.post('/analyze',files=f,data={'consent':'true'},headers=h)
    assert r.status_code==200 and r.json()['filename']=='test.txt'
