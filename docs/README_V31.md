# LexGuard AI V3.1 — hackathon MVP

Bu patch `LexGuard_AI` ildiziga chiqariladi. Korpus va indekslar o‘zgarmaydi. V3.0 fayllari ham saqlanadi. Yangi entrypoint: `openai_analyzer_v31.analyze_contract_openai`. V3.1 barcha huquqiy normalarni avtomatik ekspertiza qilmaydi. Korpusning amaldagi tahriri to‘liq tasdiqlanmagan.

## Colab
1. Patchni `/content/LexGuard_AI` ichiga unpack qiling.
2. `%pip -q install -r /content/LexGuard_AI/requirements-v31.txt`
3. `%cd /content/LexGuard_AI` va `!python -m pytest -q test_v31.py`.
4. `targeted_v31.run_targeted('/content/LexGuard_Benchmark', '/content/LexGuard_AI', client, '/content/V31_targeted', ids=('03','05','07'))` — oldingi benchmark ochilgan bo‘lsa. 11 ta oldindan tanlangan band, mustaqil test emas. To‘liq shartnoma konteksti saqlanadi. Natijalar har bir hujjat uchun JSONga yoziladi. `coverage_complete=False` maqsadli sinov uchun kutilgan holat. Oldingi V3 benchmark runner yangi versiyani qabul qilmaydi.

## API (lokal yoki jamoa serveri)
Asosiy backend va V3.1 patch bir papkada bo‘lishi kerak. Tavsiya: Python 3.11/3.12, scikit-learn==1.8.0 (indeks shu versiyada yaratilgan). Avvalgi Chroma bazasi mos kelmasa, `LEXGUARD_BACKEND=offline` ayni BM25+LSA indekslaridan foydalanadi (Chroma rejimi emas). Boshqa indekslar yoki yangi corpus aralashtirilmasin.
```
python -m pip install -r requirements-chroma.txt -r requirements-contract.txt -r requirements-v31.txt scikit-learn==1.8.0
```
Server muhiti: `OPENAI_API_KEY` (hech qachon frontendga joylamang), `LEXGUARD_DEMO_TOKEN` (demo uchun alohida tasodifiy token), `LEXGUARD_ORIGINS` (frontendning aniq origin manzili), ixtiyoriy `LEXGUARD_BACKEND=chroma` yoki `offline`. API bir ishchi bilan ishlatiladi:
```
python -m uvicorn lexguard_api:app --host 127.0.0.1 --port 8000
```
`GET /health` — konfiguratsiya holati; real API yoki retriever tekshiruvi emas.
`POST /analyze` — `multipart/form-data` maydonlari: `file` (PDF/DOCX/TXT, maksimal 5 MB), `consent=true`, `X-Demo-Token` header. Faqat ruxsatli, anonimlashtirilgan hujjatlar. Skan PDF uchun OCR mavjud emas. API 30 bandgacha tahlil qiladi; qamrov to‘liq bo‘lmasa natijada ogohlantiradi. Javob maydonlari: `version`, `document_type`, `document_subtype`, `document_status`, `risk_count`, `ai_assessed_count`, `insufficient_evidence_count`, `coverage_complete`, `warnings`, `risks[]`, `clauses[]`, `usage`, `api_errors[]`. Har bir `clauses[].ai_assessment`: `status`, `severity`, `issue`, `recommendation`, `rule_application`, `legal_basis[]`, `diagnostic_reason`, `review_status`. `legal_basis[]` ichida `document_name`, `article_number`, `evidence_quote`, `source_url`, `verification_status`. Frontendda 1–3 iqtibos ko‘rinsin, qolganlari ochiladigan bo‘lsin. `no_obvious_risk` — xavf aniqlanmadi, qonuniylik sertifikati emas. `insufficient_evidence` — qo‘lda tekshirish kerak. `review_unresolved_first_pass_risk` — dastlabki xavf, reviewer texnik xato tufayli yakunlanmagan. `bounded_corpus_rule` — tor doiradagi korpus qoidasi.

Frontend JS (demo tokenni foydalanuvchi sessiyasida kiritsin; doimiy maxfiy kalit yoki OpenAI keyni bundle ichiga yozmang):
```js
async function analyze(file, consent, demoToken) {
  const data = new FormData();
  data.append('file', file);
  data.append('consent', String(consent));
  const res = await fetch('http://127.0.0.1:8000/analyze', {
    method: 'POST', headers: {'X-Demo-Token': demoToken}, body: data
  });
  if (!res.ok) throw new Error((await res.json()).detail || 'Tahlil xatosi');
  return await res.json();
}
```
Lokal `127.0.0.1` faqat shu kompyuterdan ishlaydi. Internetda HTTPS, autentifikatsiya, server upload cheklovi, real rate limit va maxfiylik talablari kerak. Bu demo API, ommaviy production emas. Colab'da TestClient orqali real OpenAI tahlilini tekshirish mumkin, lekin bu tashqi serverga deploy qilinganligini anglatmaydi.

## Mahalliy test
15 ta pytest test o‘tdi, haqiqiy lokal korpus va offline BM25+LSA bilan. OpenAI chaqiruvlari maket; FastAPI endpoint maket tahlilchi bilan tekshirildi. Chroma va real OpenAI V3.1 tahlili Colab'da tasdiqlanishi kerak. Benchmark bo‘yicha yangi aniqlik yoki xarajat kamayishi hali o‘lchanmagan. Modda raqami va ID tekshiruvi semantik qonuniylikni kafolatlamaydi.
