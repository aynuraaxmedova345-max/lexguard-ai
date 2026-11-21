"""Browser interaction with intercepted mock API, no OpenAI calls."""
from pathlib import Path
import io, json, threading
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from functools import partial
from PIL import Image
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).parent
http=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=str(ROOT/'web')));threading.Thread(target=http.serve_forever,daemon=True).start()
url=f'http://127.0.0.1:{http.server_port}/';buf=io.BytesIO();Image.new('RGB',(300,400),'white').save(buf,'PNG')
files=[{'name':f'{i}.png','mimeType':'image/png','buffer':buf.getvalue()} for i in range(1,6)]
scan=[];submitted=[];errors=[]
result={'filename':'Shartnoma-5-sahifa.txt','document_type':'mehnat','total_clause_count':2,'coverage_complete':False,'clauses':[{'clause_id':'C01','text':'Sinov muddati 6 oy.','ai_assessment':{'status':'potential_risk','issue':'Sinov muddatini tekshiring.','recommendation':'Qonuniy chegaraga moslashtiring.','legal_basis':[{'document_name':'Mehnat kodeksi','article_number':'130','evidence_quote':'Sinov muddati uch oydan oshmasligi kerak.','source_url':'https://lex.uz/docs/-6257288'}]}}]}
def mock(route):
    path=route.request.url
    if path.endswith('/scan'):
        import re
        n=re.search(r'filename="(\d+)\.png"',route.request.post_data).group(1);scan.append(n);route.fulfill(json={'text':'Sahifa '+n+' matni.'})
    elif path.endswith('/jobs'):
        submitted.append(route.request.post_data);route.fulfill(json={'job_id':'test','state':'running'})
    elif path.endswith('/jobs/test'):route.fulfill(json={'state':'done','result':result})
    else:route.fulfill(status=200,content_type='text/html',body=(ROOT/'web'/'index.html').read_text())
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']);context=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,device_scale_factor=1);page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)));html=(ROOT/'web'/'index.html').read_text();stub="""<script>window.scans=[];window.submissions=[];window.fetch=async(path,opt)=>{let d;if(path==='./scan'){let name=opt.body.get('file').name.split('.')[0];window.scans.push(name);d={text:'Sahifa '+name+' matni.'}}else if(path==='./jobs'){window.submissions.push(await opt.body.get('file').text());d={job_id:'test',state:'running'}}else if(path==='./jobs/test'){d={state:'done',result:RESULT}}return {ok:true,json:async()=>d}};</script>""".replace('RESULT',json.dumps(result));page.set_content(html.replace('<script>',stub+'<script>',1));page.screenshot(path='/mnt/data/LexGuard_CLEAN_mobile.png',full_page=True)
    page.locator('#photo').set_input_files(files[:4]);page.locator('#camera').set_input_files(files[4:]);assert page.locator('.page-card').count()==5
    page.locator('.page-card').nth(1).get_by_role('button',name='↑').click();page.locator('#analyze').click();assert not page.evaluate("window.scans")
    page.locator('#consent').check();page.locator('#token').fill('2026');page.locator('#analyze').click();page.wait_for_selector('#editPanel',state='visible');assert page.evaluate('window.scans')==['2','1','3','4','5']
    text=page.locator('#scanText').input_value();assert text.startswith('Sahifa 2') and text.endswith('Sahifa 5 matni.')
    page.locator('#analyze').click();assert not page.evaluate("window.submissions")
    page.locator('#scanText').fill(text+'\nTahrirlangan.');page.locator('#reviewText').check();page.locator('#analyze').click();page.wait_for_selector('#results',state='visible',timeout=10000);assert 'Tahrirlangan.' in page.evaluate('window.submissions[0]');assert 'Qolgan bandlar' in page.locator('#warningBody').inner_text();assert page.locator('#export').inner_text()=='Word yuklash';assert page.locator('#print').inner_text()=='PDF yuklash';assert not errors,errors
    page.screenshot(path='/mnt/data/LexGuard_CLEAN_result.png',full_page=True)
    page.locator('#clear').click();assert not page.locator('#results').is_visible();assert page.locator('.page-card').count()==0
    page.set_viewport_size({'width':1280,'height':900});page.screenshot(path='/mnt/data/LexGuard_CLEAN_desktop.png',full_page=True);browser.close()
http.shutdown();print('PASS: 5 images, camera add, reorder, consent, ordered OCR, edit/confirm, analyze, warning, clear and responsive layout (mock API)')
