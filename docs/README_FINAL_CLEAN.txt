LexGuard AI — yakuniy interfeys yangilanishi (2026-11-21)
V3.1 analizatori, korpus, BM25, ChromaDB o'zgarmaydi. Bitta faol AI tahlili/scan rejimi saqlanadi. Oldingi parallel patch ishlatilgan bo'lsa, original bir ishli API qayta tiklanadi.
1. Colab'da reportlab python-docx o'rnatilgan bo'lishi kerak.
2. ZIPni /content/LexGuard_AI ichiga chiqarish; LEXGUARD_DEMO_TOKEN=2026.
3. Amaldagi serverni to'xtatib aynan eski portda uvicorn lexguard_mvp:app bilan qayta ishga tushirish. Tunnelni qayta ochmang. Jarayon davomida faol tahlil bo'lmasin. Eski natijalar RAMdan o'chadi.
4. Saytni yangilang; eski QR tunnel faol bo'lsa o'zgarishsiz.
5. JPG/PNG: 5 tagacha sahifa, har biri 10 MB; avval rozilik va demo kodi, keyin umumiy tahlil tugmasi matnni avtomatik ajratadi. Matnni tekshirish va tasdiqlashdan so'ng bitta TXT sifatida V3.1 ga uzatiladi. Har rasm bitta Vision chaqiruv; 20 scan va 20 tahlil server sessiyasi limiti. 2026 — faqat qisqa demo uchun, ommaviy xavfsiz autentifikatsiya emas. Faqat anonim hujjatlar.
6. Word/PDF serverda mavjud tahlil natijasidan yaratiladi. Natija 30 daqiqagacha xotirada turadi (yoki sakkiz natijadan oshsa, avvalroq o'chishi mumkin). PDF iOS Safari'da ochilsa Share > Save to Files.
7. Oflayn HTML alohida, o'zgarishsiz. Asosiy saytda arxiv/demo yo'q. Testlar mock AI; jonli API/telefon sinovi qilinmagan.
