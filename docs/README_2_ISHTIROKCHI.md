# LexGuard AI — 2-ishtirokchi (AI Contract Analyzer MVP)

**Maqsad:** mavjud 8 071 yozuvli BM25 + ChromaDB bazasiga tegmasdan PDF/DOCX/TXT shartnomalarni dastlabki tahlil qilish.

## Google Colab usuli

1. `LexGuard_Contract_Analyzer_Colab.ipynb` ni Colab'da oching.
2. Avvalgi `/content/LexGuard_AI` loyihasi runtime'da mavjud bo'lsa, undan foydalanadi. Aks holda avvalgi `LexGuard_AI_Colab_BM25_ChromaDB_TAYYOR.zip` ni yuklang.
3. `LexGuard_Contract_Analyzer_PATCH.zip` (kichik ZIP) ni yuklang. Unda kodekslar va indekslar **yo'q**; u oldingi loyihaga qo'shiladi.
4. Kataklarni ketma-ket ishlating; avval sun'iy demo shartnomasini sinang, keyin o'z PDF/DOCX'ingizni yuklang.
5. Ixtiyoriy tarzda Gemini API kaliti bilan chuqurroq tahlil qilish mumkin. Google Colab Secrets'da `GEMINI_API_KEY` yarating. Shartnoma matni bu rejimda tashqi AI provayderiga yuboriladi — **maxfiy hujjatlarni yubormang**.

## Mahalliy chaqirish

```bash
python -m pip install -r requirements-contract.txt
python contract_analyzer.py examples/namunaviy_mehnat_shartnomasi.txt --project-root /path/to/LexGuard_AI --backend offline --output result.json
```

ChromaDB o'rnatilgan va mavjud bo'lsa `--backend chroma` ishlating.

## 2-ishtirokchi natijasi

- `contract_analyzer.py`: `analyze_contract(path, project_root=..., backend='chroma', top_k=3)`
- `examples/namunaviy_mehnat_shartnomasi.txt`: faqat sun'iy test.
- `analysis_result.json`: `document_type`, `summary`, `risks`, `clauses`, `warnings`.
- `tests/test_contract_analyzer.py`: kod ishlashini tekshiruvchi texnik testlar.

## Chegaralar

- Qidiruv BM25 + LSA/Chroma: bu neyron embedding emas.
- API kalitisiz rejim **AI emas**, matndagi ehtimoliy xavf signallari + qonun moddalarining qidiruv natijasidir.
- Qaytarilgan `legal_basis` — hozircha qidiruv nomzodi, muayyan shartnomaga normaning tatbiq etilishi tasdiqlangan emas.
- Amaldagi LexUZ matnlari bilan 8 071 yozuvning barchasi to'liq qiyoslanmagan. Har bir huquqiy xulosa oldidan tegishli normani tekshiring.
- 12 band limitli boshlang'ich MVP; ortiqcha bandlar bo'lsa `warnings`da qayd etiladi.
- Skanerlangan PDF uchun OCR hozircha mavjud emas.
- Vaqt bo'yicha qo'llaniladigan normalarni chuqur tekshirish va amaldagi tahrirni avtomatik yangilash hali qo'shilmagan.

## Tavsiya etilgan keyingi ish

3-ishtirokchining Streamlit interfeysi `analyze_contract` qaytargan JSON'ni qabul qiladi. Natijalarni «tekshiruv talab qilinadi» maqomida ko'rsatish va LexUZ havolalarini foydalanuvchiga ochib berish kerak.
