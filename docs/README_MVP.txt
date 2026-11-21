LEXGUARD AI | HACKATHON MVP

Eng tez: avvalgi Colab sessiyasida UI patchni /content/LexGuard_AI papkasiga chiqarib, V3.1 bilan ishlating. serverni localhost 7860 portida uvicorn orqali ishga tushiring; Colab output.serve_kernel_port_as_iframe(7860, height=1000) yordamida notebook ichida oching. Bu ommaviy hosting emas, notebook egasining qisqa integratsiya tekshiruvi. API key Colab Secretsda qoladi. LEXGUARD_DEMO_TOKEN server muhitida sozlanadi va interfeysga kiritiladi. Hech kimga API keyni bermang.

Lokal kompyuter: full ZIPni oddiy papkaga chiqaring. Python 3.11–3.13 kerak. Papkada terminal:
  python -m pip install -r requirements-mvp.txt
  python start_mvp.py
Default offline BM25+LSA (ChromaDB talab qilinmaydi); Chroma uchun requirements-chroma.txt o‘rnating va LEXGUARD_BACKEND=chroma belgilang. Offline indeksi aynan mavjud korpusdan; real natija Chroma bilan aynan bir xil bo‘lishi shart emas. Server lokal. Internetga faqat vaqtinchalik demo uchun tunnel qo‘shish mumkin; production emas. Maxfiy hujjat ishlatmang. API kaliti serverda; demo kodi foydalanuvchi kiritadi. 

Zaxira: web/index.html faylini papkadan brauzerda ochib 'Saqlangan demo' tugmasini bosing. Bu oldingi haqiqiy V3.0 natijasi (1 ta ma’lum asossiz xavf bilan), jonli tahlil emas. Internet kerak emas. JSON va chop etish ishlaydi. Sinov fayli web/sample.docx. 

Jonli rejim: 'Sinov faylini olish' orqali DOCX yuklab oling, yuklash maydoniga tanlang, rozilikni belgilang, demo kodini kiriting va tahlil qiling. Har bir natija xotirada 30 daqiqagacha, ko‘pi bilan 8 ta yakunlangan ish saqlanadi; server o‘chganda yo‘qoladi. Fayllar backendda vaqtincha ishlatiladi. Bir vaqtda bitta tahlil. 30 tagacha band. API chaqiruvlari real balansdan sarflanadi. JSON eksporti, filtr, bandlar va qonun iqtiboslari, LexUZ linklar, browser print PDF. Skanerlangan PDF uchun OCR yo‘q. Korpus to‘liq rasmiy verifikatsiyadan o‘tmagan. Bu dastlabki baho, yuridik ekspertiza emas.
