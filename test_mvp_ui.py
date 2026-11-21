import time
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
import lexguard_mvp as ui

def test_mvp(monkeypatch):
    monkeypatch.setenv('LEXGUARD_DEMO_TOKEN','test-only')
    observed=[]
    def fake(file, consent, token):
        observed.append((file.filename,file.file.read(),consent,token))
        return {'version':'contract-v3.1','filename':file.filename,'clauses':[], 'api_errors':[], 'ai_assessed_count':1}
    monkeypatch.setattr(ui,'analyze',fake)
    c=TestClient(ui.app);h={'X-Demo-Token':'test-only'}
    assert c.get('/').status_code==200 and 'LexGuard' in c.get('/').text
    assert c.get('/demo-data.js').status_code==200
    assert c.get('/sample').content[:2]==b'PK'
    f={'file':('fake.txt',b'example','text/plain')}
    assert c.post('/jobs',files=f,data={'consent':'true'}).status_code==401
    assert c.post('/jobs',files=f,data={'consent':'false'},headers=h).status_code==400
    assert c.post('/jobs',files={'file':('fake.exe',b'abc')},data={'consent':'true'},headers=h).status_code==415
    r=c.post('/jobs',files=f,data={'consent':'true'},headers=h);assert r.status_code==202
    jid=r.json()['job_id'];assert c.get('/jobs/'+jid).status_code==401
    for _ in range(50):
        v=c.get('/jobs/'+jid,headers=h).json()
        if v['state']!='running':break
        time.sleep(.02)
    assert v['state']=='done' and v['result']['filename']=='fake.txt'
    assert observed==[('fake.txt',b'example',True,'test-only')]
