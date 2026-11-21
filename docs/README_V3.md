# LexGuard AI — V3.0 / incremental patch

## O‘rnatish
Mavjud `/content/LexGuard_AI` loyihasiga ZIP faylini oching. `data/`, `indexes/`, `retriever.py`, `contract_analyzer.py` va eski OpenAI modullari o‘zgarmaydi. Korpus va ChromaDB qayta qurilmaydi. Python 3.10+, oldingi paketlar (scikit-learn 1.8.0, chromadb, pymupdf, python-docx, openai) kerak.

```python
from google.colab import files
from pathlib import Path
import zipfile, sys
PROJECT = Path('/content/LexGuard_AI')
assert (PROJECT/'retriever.py').is_file() and (PROJECT/'data/legal_corpus_unified.jsonl').is_file() and (PROJECT/'indexes/manifest.json').is_file(), 'Avval asosiy backendni tiklang.'
uploaded = files.upload()  # LexGuard_AI_V3_PATCH.zip
with zipfile.ZipFile(next(iter(uploaded))) as z:
    z.extractall(PROJECT)
if str(PROJECT) not in sys.path: sys.path.insert(0, str(PROJECT))
from openai_analyzer_v3 import VERSION
print(VERSION)
```

```python
from google.colab import files, userdata
from openai import OpenAI
from pathlib import Path
from openai_analyzer_v3 import analyze_contract_openai
u = files.upload()  # faqat anonimlashtirilgan yoki sun’iy shartnoma
client = OpenAI(api_key=userdata.get('OPENAI_API_KEY'))
result_v3 = analyze_contract_openai(Path(next(iter(u))).resolve(), client=client,
    project_root=PROJECT, backend='chroma', model='gpt-4.1-mini',
    top_k=5, max_clauses=30, consent=True, review=True)
print(result_v3['summary'], result_v3['api_errors'], result_v3['usage'])
for c in result_v3['clauses']:
    a=c['ai_assessment']
    print(c['clause_id'], a['status'], a['issue'], a['diagnostic_reason'], a['review_status'])
    for b in a['legal_basis']:
        print(b['document_name'], b['article_number'], b['evidence_quote'])
```

## Texnik tekshiruv
`python -m pytest -q test_v3.py` — offline indeks va maket API bilan. `python regression_v3.py /path/to/old/contracts offline` — eski 7 Word fayl bilan qidiruv regressiyasi. `regression_v3.json` — ushbu bajarilgan tajriba natijasi (36/36). Testlar real OpenAI API chaqiruvini amalga oshirmaydi. ChromaDB bo‘yicha real sinov Colab muhitida bajarilishi kerak; mahalliy konteynerda chromadb paketi mavjud emas. Yangilanish ikki model so‘rovi bilan ishlaydi, shuning uchun API sarfi oshishi mumkin; `usage` haqiqiy tokenlarni qaytaradi. `review=False` tezkor rejim, ikkinchi tekshiruv yo‘q.

## Yondashuv
- Huquqiy mavzu marshrutlari va bir nechta so‘rov; amaliy sinovda uchragan mavzulardan umumlashtirilgan. Qidiruv javobi huquqiy hukm emas.
- Shartnoma kichik turini evristik aniqlash, huquqiy doira asosida yumshoq qayta saralash, bandlarni gap/nuqtali vergul bo‘yicha qidiruv birliklariga ajratish; parent C-ID saqlanadi. Segmentatsiya to‘liq lingvistik parser emas.
- Muayyan bog‘lovchi normalarni (masalan, 708, 16, 31) qidiruvga kiritish; universal moddalararo grafik hali yo‘q.
- To‘liq korpus paragraflarining aniq IDlari, har band uchun JSON schema enum, lokal ID validatsiyasi. Matnda generatsiya qilingan modda raqami va URL rad etiladi. Iqtibos to‘g‘ridan-to‘g‘ri korpusdan olinadi.
- Minimal/maksimal operator hamda sodda son-birliklarni ajratish model uchun yordamchi signal; murakkab huquqiy miqdorlar va istisnolar universal deterministik validator emas. Ikkinchi LLM tahlili dalilning mosligi, taraflar roli, istisno va mantiqni qayta baholaydi; xatosiz ekspertiza kafolatlanmaydi.
- Noto‘g‘ri javob yoki ayrim vaqtinchalik API xatolarida bir marta qayta urinish; maxfiy ma’lumotlar logga yozilmaydi. Dalil yetishmasa `insufficient_evidence`.
- Korpus, indeks va natija schema kalitlari mosligi saqlangan. `ai_assessment.legal_basis` ichida aniq paragraf matni `evidence_quote` sifatida qaytadi.

## Chegaralar
Korpus 8 071 birlik, 4 kodeks (Fuqarolik kodeksi ikki qism); barcha amaldagi normalar qamrab olinmagan, rasmiy tahrir to‘liq tekshirilmagan. 36/36 — V3 ni ishlab chiqishda ishlatilgan shartnomalarda TOP-5 qidiruv ko‘rsatkichi, yakuniy huquqiy tahlil aniqligi emas. Maxsus iste’molchilar qonuniga oid 1 xavf hisobdan alohida qoldirilgan. Yangi, ilgari ko‘rilmagan hujjatlarda keyingi mustaqil sinov zarur. FastAPI hali integratsiya qilinmagan.
