"""Mock API tests; never call external model. Run with python test_final.py."""
import os, sys, types, threading, time, io, json, copy
from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image
from docx import Document
os.environ['LEXGUARD_DEMO_TOKEN']='2026'
fake=types.ModuleType('lexguard_api');fake.app=FastAPI();fake.MAX_BYTES=5242880;fake.lock=threading.Lock()
entered=threading.Event(); release=threading.Event()
R={'filename':'Namuna.txt','document_type':'mehnat','version':'contract-v3.1','coverage_complete':True,'total_clause_count':1,'clauses':[{'clause_id':'C01','text':'Sinov muddati 6 oy.','ai_assessment':{'status':'potential_risk','issue':'Sinov muddati qayta ko‘rib chiqilishi kerak.','recommendation':'Qonuniy chegaraga moslashtiring.','legal_basis':[{'document_name':'Mehnat kodeksi','article_number':'130','evidence_quote':'Sinov muddati uch oydan oshmasligi kerak.','source_url':'https://lex.uz/docs/-6257288'}]}}]}
def analyze(file,consent,token):
    entered.set(); assert release.wait(15); r=copy.deepcopy(R);r['filename']=file.filename;return r
fake.analyze=analyze
class Vision:
    def create(self,**kwargs):return types.SimpleNamespace(choices=[types.SimpleNamespace(finish_reason='stop',message=types.SimpleNamespace(content='Sahifa matni.'))])
fake.api_client=lambda:types.SimpleNamespace(chat=types.SimpleNamespace(completions=Vision()))
sys.modules['lexguard_api']=fake
import lexguard_mvp as m
c=TestClient(m.app); h={'X-Demo-Token':'2026'}
assert c.get('/').status_code==200
assert c.get('/demo-data.js').status_code==404
assert c.get('/sample').status_code==404
assert c.post('/analyze').status_code==404
f={'file':('contract.txt',b'Test')}
assert c.post('/jobs',files=f,data={'consent':'false'},headers=h).status_code==400
assert c.post('/jobs',files=f,data={'consent':'true'},headers={'X-Demo-Token':'1234'}).status_code==401
img=io.BytesIO();Image.new('RGB',(300,300),'white').save(img,'PNG')
for i in range(5):
    resp=c.post('/scan',files={'file':(f'{i}.png',img.getvalue())},data={'consent':'true'},headers=h);assert resp.json()['text']=='Sahifa matni.',resp.text
j=c.post('/jobs',files=f,data={'consent':'true'},headers=h).json()['job_id'];assert entered.wait(2)
assert c.post('/jobs',files=f,data={'consent':'true'},headers=h).status_code==429
assert c.post('/scan',files={'file':('page.png',img.getvalue())},data={'consent':'true'},headers=h).status_code==429
release.set()
for _ in range(100):
    item=c.get('/jobs/'+j,headers=h).json()
    if item['state']=='done': break
    time.sleep(.02)
assert item['state']=='done';assert c.get('/jobs/'+j,headers={'X-Demo-Token':'wrong'}).status_code==401
for ext in ['pdf','docx']:
    response=c.post('/report.'+ext,data={'job_id':j,'demo_token':'2026'});assert response.status_code==200,response.text[:200]
    assert c.post('/report.'+ext,data={'job_id':j,'demo_token':'wrong'}).status_code==401
    if ext=='pdf':assert response.content.startswith(b'%PDF')
    else:assert 'LexGuard AI' in Document(io.BytesIO(response.content)).paragraphs[0].text
    Path('/tmp/lexguard_qa.'+ext).write_bytes(response.content)
print('PASS: 5 scans, auth, consent, single active AI, job isolation, PDF/DOCX endpoints, removed public demo routes')
