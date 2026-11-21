"""Local MVP API. Run with one worker; API key stays server-side."""
from __future__ import annotations
import os, secrets, tempfile, threading
from functools import lru_cache
from pathlib import Path
from fastapi import FastAPI, File, Form, UploadFile, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from openai_analyzer_v31 import analyze_contract_openai, VERSION
from legal_retrieval_v3 import ScopedRetriever

ROOT=Path(os.getenv('LEXGUARD_PROJECT',str(Path(__file__).resolve().parent)))
BACKEND=os.getenv('LEXGUARD_BACKEND','chroma')
MAX_BYTES=5*1024*1024
lock=threading.Lock()
app=FastAPI(title='LexGuard AI',version=VERSION)
origins=[x.strip() for x in os.getenv('LEXGUARD_ORIGINS','http://localhost:3000,http://localhost:5173,http://127.0.0.1:5173').split(',') if x.strip()]
app.add_middleware(CORSMiddleware,allow_origins=origins,allow_methods=['GET','POST'],allow_headers=['Content-Type','X-Demo-Token'])

@lru_cache(maxsize=1)
def engine():return ScopedRetriever(ROOT,BACKEND)

@lru_cache(maxsize=1)
def api_client():
    from openai import OpenAI
    return OpenAI(timeout=75.0,max_retries=0)

@app.get('/health')
def health():
    return {'service':'LexGuard AI','version':VERSION,'corpus_present':(ROOT/'data/legal_corpus_unified.jsonl').exists(),'backend':BACKEND,'api_configured':bool(os.getenv('OPENAI_API_KEY')),'token_configured':bool(os.getenv('LEXGUARD_DEMO_TOKEN')),'source_verification_complete':False}

@app.post('/analyze')
def analyze(file:UploadFile=File(...),consent:bool=Form(False),x_demo_token:str|None=Header(None)):
    expected=os.getenv('LEXGUARD_DEMO_TOKEN','')
    if not expected:raise HTTPException(503,'Demo token serverda sozlanmagan.')
    if not x_demo_token or not secrets.compare_digest(x_demo_token,expected):raise HTTPException(401,'Ruxsat berilmagan.')
    if not consent:raise HTTPException(400,'Tashqi AI xizmatiga yuborish roziligi kerak.')
    name=Path(file.filename or 'contract').name
    ext=Path(name).suffix.lower()
    if ext not in {'.pdf','.docx','.txt'}:raise HTTPException(415,'PDF, DOCX yoki TXT yuklang.')
    if not lock.acquire(blocking=False):raise HTTPException(429,'Boshqa tahlil davom etmoqda.')
    try:
        data=file.file.read(MAX_BYTES+1)
        if len(data)>MAX_BYTES:raise HTTPException(413,'Fayl 5 MB dan katta.')
        if not data:raise HTTPException(400,'Fayl bo‘sh.')
        # Random temporary directory. Never use user path as a server path.
        with tempfile.TemporaryDirectory(prefix='lexguard_') as tmp:
            p=Path(tmp)/('contract'+ext);p.write_bytes(data)
            try:
                result=analyze_contract_openai(p,client=api_client(),project_root=ROOT,backend=BACKEND,retriever=engine(),consent=True,review=True,max_clauses=30)
            except ValueError as e:raise HTTPException(422,'Hujjatni tahlil qilib bo‘lmadi. Matnli PDF, DOCX yoki UTF-8 TXT tekshiring.') from e
            except Exception as e:raise HTTPException(503,'Tahlil servisi vaqtincha ishlamadi. Server konfiguratsiyasini tekshiring.') from e
        result['filename']=name
        # Diagnostic raw model outputs and full retrieved texts are not UI evidence.
        for clause in result['clauses']:
            clause.pop('diagnostic_attempts',None);clause.pop('pre_rule_assessment',None)
            for law in clause.get('legal_basis',[]):law.pop('text',None)
        return result
    finally:
        file.file.close();lock.release()
