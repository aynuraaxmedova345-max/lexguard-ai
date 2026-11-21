# LexGuard AI — BM25 + ChromaDB uchun RAG qidiruv moduli

**Holat: 2026-11-20.** 4 ta kodeks, Fuqarolik kodeksi I va II qismlari, hamda Mehnat kodeksiga O‘RQ–1189 o‘zgarishi qo‘llangan **8 071** ta faol yozuv asosida tayyorlandi.

## Nima **tayyor** va nima **hali bajarilishi kerak**?

| Komponent | Holati |
|---|---|
| `data/legal_corpus_unified.jsonl` — asl RAG korpusi | Tayyor |
| `indexes/bm25_weights.npz` — haqiqiy BM25 indeksi (13 183 atama) | **Tayyor va sinovdan o‘tgan** |
| `indexes/dense_lsa_vectors.npy` — 96D mahalliy vektorlar | **Tayyor va sinovdan o‘tgan** |
| `retriever.py` — hybrid qidiruv: BM25 + mahalliy LSA | **Tayyor va sinovdan o‘tgan** |
| `build_chroma.py` — real ChromaDB bazasini yaratish | **Tayyor kod; ushbu muhitda ishga tushmagan** |
| Real `indexes/chroma_db/` katalogi | **Hali mavjud emas**: ChromaDB kutubxonasini internetdan o‘rnatish imkoni bo‘lmadi |
| Multilingual E5 neural embedding ChromaDB | **Ixtiyoriy takomillashtirish**; foydalanuvchi kompyuterida modelni yuklab, indekslash zarur |

> **Huquqiy eslatma:** yuklangan kodekslarning barcha moddalari rasmiy LexUZ sahifalaridagi amaldagi tahrirlar bilan so‘zma-so‘z tekshirilmagan. `verification_status` maydonini olib tashlamang; `version_date=null` bo‘lsa, uni taxminiy sana bilan to‘ldirmang.

## A. Darhol ishlatish — Windows, hech qanday AI API kerak emas

Python 3.11 yoki 3.12 tavsiya etiladi. Arxivni bitta katalogga oching. Shu katalogda terminal ishga tushiring:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python retriever.py "Ijara shartnomasini bekor qilish" --top-k 5
```

BM25 va mahalliy LSA indekslari **allaqachon tayyor**, qaytadan hisoblash shart emas. Bu rejimda ChromaDB kerak emas. `scikit-learn` versiyalari mos kelmasa, yangi indekslarni qurish uchun `python build_indexes.py` ishga tushiring.

```python
from retriever import search_law

items = search_law(
    "Ijaraga oluvchining majburiyatlari",
    top_k=5,
    include_full_article=True,
)
for item in items:
    print(item['document_name'], item['article_number'], item['source_url'])
    print(item['verification_status'], item['text'])
```

Muhim parametrlar:
- `domain='labor'` yoki `domain='civil'` — faqat tegishli huquqiy sohaga tegishli yozuvlar.
- `document_ids=['civil_2']` — aniq hujjat ID bo‘yicha qidirish: `civil_1`, `civil_2`, `labor`, `housing`, `family`.
- `article_number='8-1'` — raqami ma’lum modda bo‘yicha cheklash.
- `group_by_article=True` — bitta moddaning ko‘plab paragraflari boshqa moddalarni siqib chiqarmaydi.
- `include_full_article=True` — topilgan normaning butun moddasini qaytaradi, 20 000 belgigacha.
- `use_domain_hints=True` — “ijara”, “mehnat”, “nikoh” kabi ishoralarga yengil ustuvorlik beradi, **boshqa kodekslarni o‘chirib tashlamaydi**.

**Natijadagi `rrf_score` huquqiy ishonchlilik foizi emas.** Bu qidiruv tartibini belgilovchi kombinatsiyalangan baho. Huquqiy xulosalar uchun `verification_status` va `source_url` kerak.

## B. Haqiqiy ChromaDB'ni ishga tushirish — tayyor vektorlardan

Internetga ulangan, ChromaDB o‘rnatish mumkin bo‘lgan kompyuteringizda:

```powershell
python -m pip install -r requirements-chroma.txt
python build_chroma.py --mode lsa
python retriever.py "Mehnat shartnomasini bekor qilish" --backend chroma
```

Bu qadam `indexes/chroma_db/` katalogida **haqiqiy persistent ChromaDB** kolleksiyasini yaratadi; yangi embedding API/model yuklab olmaydi. Bir nechta ishga tushirish uchun `python build_chroma.py --mode lsa --rebuild` ishlating.

> **Diqqat:** bunda ChromaDB saqlash va vektorlar bo‘yicha qidirish vositasi sifatida ishlatiladi, ammo 96D vektorlarning o‘zi neyron embedding emas, TF-IDF + LSA bilan olingan. Uni professional semantik qidiruv bilan adashtirmang.

## C. Tavsiya etiladigan keyingi bosqich — multilingual E5

Semantik qidiruv sifatini oshirish uchun (`intfloat/multilingual-e5-small`, bir martalik model yuklab olish talab etiladi):

```powershell
python -m pip install -r requirements-e5.txt
python build_chroma.py --mode e5
python retriever.py "Turar joy ijarasi" --backend chroma_e5
```

Bu rejimda matnga `passage: `, savolga `query: ` prefikslari beriladi, normalizatsiyalangan multilingual embeddings ChromaDB'da saqlanadi. Bu kod ushbu muhitda **model yo‘qligi sabab bajarilmagan va sinovdan o‘tkazilmagan**. Dastlabki xatolar uchun `--mode lsa` variantidan boshlang. CPU qurilmasida E5 modeli indekslash uchun sezilarli vaqt talab qilishi mumkin.

## D. Qayta indekslash va yangilangan qonunlarni kiritish

Korpus o‘zgartirilsa, eski indekslardan foydalanmang. `retriever.py` korpusning SHA-256 xeshini tekshiradi va nomuvofiqlik bo‘lsa xato beradi.

```powershell
python build_indexes.py
python build_chroma.py --mode lsa --rebuild
```

Agar E5 ham yoqilgan bo‘lsa, uni ham `python build_chroma.py --mode e5 --rebuild` bilan yangilang.

## E. API natija strukturasi

```json
{
  "doc_id": "civil_2:615:0001",
  "document_id": "civil_2",
  "document_name": "Fuqarolik kodeksi (II qism)",
  "article_number": "615",
  "article_title": "Ijara shartnomasini bekor qilish",
  "part_number": "1",
  "text": "... asl norma matni ...",
  "source_url": "https://lex.uz/uz/docs/-180552#...",
  "verification_status": "source_export_not_compared",
  "version_date": null,
  "rrf_score": 0.0,
  "is_legally_verified": false,
  "retrieval_backend": "bm25+local-lsa"
}
```

Yuqoridagi JSON **sxema misoli**, aniq yozuv ID/balli emas. Haqiqiy qiymatlarni `search_law()` beradi.

## F. Fayl tuzilishi

```text
LexGuard_BM25_Chroma_RAG_2026-11-20/
├── data/legal_corpus_unified.jsonl   # 8 071 ta manbali huquqiy yozuv
├── indexes/bm25_weights.npz           # BM25 sparse index
├── indexes/bm25_vectorizer.joblib
├── indexes/word_tfidf.joblib
├── indexes/lsa_svd.joblib
├── indexes/dense_lsa_vectors.npy
├── indexes/manifest.json
├── build_indexes.py                   # offline qayta indekslash
├── build_chroma.py                    # ChromaDB kolleksiyasi yaratish
├── retriever.py                       # search_law() interfeysi
├── tests/test_retriever.py            # texnik testlar
├── examples/integration_example.py
├── examples/demo_results.json
├── requirements.txt
├── requirements-chroma.txt
└── requirements-e5.txt
```

## G. Sinovlar va cheklovlar

```powershell
python -m pip install pytest
python -m pytest -q
```

Mahalliy muhitdagi tekshiruv: **10/10 test muvaffaqiyatli**. Aniq huquqiy norma havolalari, qidiruv filtrlari va o‘zgartirilgan 8¹-moddaning topilishi sinovdan o‘tgan. Bu testlar **barcha yuridik savollarda aniqlik kafolati emas**. BM25 qidiruvi aniq atamalarda kuchli; LSA mazmunni taxminiy o‘xshatadi va ba’zan yaroqsiz huquqiy moddalarni yuqoriga chiqarishi mumkin. Natijani LLM yordamida yuridik tahlil qilishdan oldin asl matn bilan tekshiring.

**Xavfsizlik:** `joblib` serializatsiya fayllarini faqat ishonchli manbadan yuklang. `LexUZ` manba havolasi matnning oxirgi tahrir ekanligini o‘zi isbotlamaydi.
