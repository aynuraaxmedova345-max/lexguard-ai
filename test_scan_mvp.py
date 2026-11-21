import io,time
from types import SimpleNamespace as NS
from PIL import Image
from fastapi.testclient import TestClient
import lexguard_mvp as ui


def test_scan(monkeypatch):
    monkeypatch.setenv('LEXGUARD_DEMO_TOKEN','demo-test')
    monkeypatch.setattr(ui,'SCAN_COUNT',0)
    h={'X-Demo-Token':'demo-test'};c=TestClient(ui.app)
    image=io.BytesIO();Image.new('RGB',(400,500),'white').save(image,'PNG');data=image.getvalue()
    f={'file':('test.png',data,'image/png')}
    calls=[]
    def create(**kw):
        calls.append(kw);return NS(choices=[NS(message=NS(content='1. Sinov muddati 6 oy.'),finish_reason='stop')])
    monkeypatch.setattr(ui,'api_client',lambda:NS(chat=NS(completions=NS(create=create))))
    assert c.post('/scan',files=f,data={'consent':'true'}).status_code==401
    assert c.post('/scan',files=f,data={'consent':'false'},headers=h).status_code==400
    assert c.post('/scan',files={'file':('test.png',b'broken')},data={'consent':'true'},headers=h).status_code==422
    r=c.post('/scan',files=f,data={'consent':'true'},headers=h)
    assert r.status_code==200 and r.json()['text']=='1. Sinov muddati 6 oy.' and r.json()['requires_review']
    assert len(calls)==1 and calls[0]['messages'][1]['content'][1]['image_url']['url'].startswith('data:image/jpeg;base64,')
    assert c.post('/analyze',files={'file':('demo.txt',b'foo')},data={'consent':'true'},headers=h).status_code==404
    monkeypatch.setenv('LEXGUARD_MAX_SCANS','1')
    assert c.post('/scan',files=f,data={'consent':'true'},headers=h).status_code==429
