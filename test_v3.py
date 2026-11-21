from pathlib import Path
from types import SimpleNamespace
import json
import pytest
from legal_retrieval_v3 import ScopedRetriever, subtype,semantic_units,scope_score
from openai_analyzer_v3 import analyze_contract_openai,prepare_clause,validate,schema_for,numeric_hints,document_stage
from contract_analyzer import extract_contract_text,split_clauses,classify_contract
ROOT=Path(__file__).resolve().parent

@pytest.fixture(scope='module')
def engine():return ScopedRetriever(ROOT,'offline')

def test_corpus(engine):
    assert len(engine.eng.rows)==8071

def test_subtypes():
    assert subtype('Uy-joy ijara shartnomasi. Kvartira yashash uchun beriladi.','ijara')=='residential_private'
    assert subtype('Davlat uy-joy fondi turar joy ijarasi','ijara')=='residential_public'
    assert subtype('Xaridor tovarni oilaviy ehtiyojlari uchun oladi','oldi_sotdi')=='retail'
    assert scope_score('housing','36','ijara','residential_private')<scope_score('civil_2','612','ijara','residential_private')

def test_operators_and_numbers():
    assert numeric_hints('kamida bir yarim hissa')[0]['amount']==1.5
    assert numeric_hints('kamida bir yarim hissa')[0]['direction']=='min'
    assert numeric_hints('yigirma bir kalendar kun')[0]['amount']==21
    assert document_stage('Imzo: __________')=='draft_or_sample'
    assert len(semantic_units('Ish joyi xavfsiz. Tizim ishlamay qolsa haq berilmaydi.'))==2

@pytest.mark.parametrize('text,kind,sub,expected',[
 ('Texnik ishlar tufayli ish beruvchining aybi bilan tizim ishlamay qolganda haq hisoblanmaydi.','mehnat','mehnat',('labor','266')),
 ('Ijaraga beruvchi elektr va suv kommunal xizmatlarini ta’minlaydi.','ijara','residential_private',('civil_2','605')),
 ('Ijaraga oluvchi uy-joyni sud qarorisiz majburiy ko‘chirib chiqariladi.','ijara','residential_private',('civil_2','616')),
 ('Nuqson aniqlansa xaridor almashtirishni yoki narxni kamaytirishni talab qiladi.','oldi_sotdi','retail',('civil_2','434')),
 ('Qo‘shimcha xizmat uchun majburiy to‘lov olinadi.','xizmat','xizmat',('civil_2','708')),
 ('Umumiy mulk uchun ulush 70 va 30 foiz.','nikoh','nikoh',('family','31')),
 ('Ish vaqtidan tashqari ishga kamida ikki hissa haq to‘lanadi.','mehnat','mehnat',('labor','16')),
])
def test_route(engine,text,kind,sub,expected):
    found,_=engine.candidates(text,kind,sub,5)
    assert expected in {(a['document_id'],a['article_number']) for a in found}

def test_paragraph_and_validation(engine):
    a=engine.article('civil_2','434');c=prepare_clause({'clause_id':'C01','text':'Nuqsonli tovar qaytarilganda pul ushlab qolinadi.'},[a],['test'])
    eid='civil_2:434:0007'
    assert eid in c['_evidence']
    assert 'ushlab qolishga haqli emas' in c['_evidence'][eid]['evidence_quote']
    good={'status':'potential_risk','severity':'high','issue':'Xaridorning pulini ushlab qolish cheklangan.','recommendation':'Ushlab qolish shartini olib tashlang.','rule_application':'Qaytarilayotgan nuqsonli tovar uchun norma ushlab qolishni taqiqlaydi.','citations':[eid]}
    assert validate(c,good)['status']=='potential_risk'
    assert validate(c,{**good,'citations':['fake']})['diagnostic_reason']=='invalid_evidence_id'
    assert validate(c,{**good,'issue':'999-modda talabiga zid.'})['diagnostic_reason']=='generated_reference_in_text'
    assert validate(c,{**good,'citations':[]})['status']=='insufficient_evidence'
    assert eid in schema_for([c])['properties']['assessments']['properties']['C01']['properties']['citations']['items']['enum']

class FakeResponses:
    def __init__(self):self.calls=0
    def create(self,**kwargs):
        self.calls+=1; payload=json.loads(kwargs['input']);out={}
        for c in payload['clauses']:
            out[c['clause_id']]={'status':'no_obvious_risk','severity':'unknown','issue':'Sinov javobi.','recommendation':'Qo‘lda tekshiring.','rule_application':'Bu faqat API maketi.','citations':[c['evidence'][0]['id']]}
        return SimpleNamespace(status='completed',output_text=json.dumps({'assessments':out}),usage=SimpleNamespace(input_tokens=100,output_tokens=20))

def test_mock_end_to_end(engine,tmp_path):
    p=tmp_path/'demo.txt';p.write_text('MEHNAT SHARTNOMASI. Ish beruvchi va xodim mazkur mehnat shartnomasini tuzdilar.\n1. Shartnoma nomuayyan muddatga tuziladi. Xodim ish boshlaydi.',encoding='utf8')
    client=SimpleNamespace(responses=FakeResponses())
    with pytest.raises(ValueError):analyze_contract_openai(p,client=client,retriever=engine)
    r=analyze_contract_openai(p,client=client,retriever=engine,consent=True,review=True)
    assert r['risk_count']==0 and r['insufficient_evidence_count']==0 and r['coverage_complete']
    assert r['api_calls']==2 and r['usage']['input_tokens']==200
    assert all(c['ai_assessment']['review_status']=='reviewed_by_model' for c in r['clauses'])
    assert not r['source_verification_complete']
    json.dumps(r,ensure_ascii=False)
