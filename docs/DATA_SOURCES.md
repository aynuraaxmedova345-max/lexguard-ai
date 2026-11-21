# Huquqiy korpus va indekslar

`data/legal_corpus_unified.jsonl` faylida O‘zbekiston Respublikasining Fuqarolik kodeksi (I va II qismlar), Mehnat kodeksi, Oila kodeksi va Uy-joy kodeksidan ajratilgan 8 071 matn birligi bor. Har bir yozuvda `source_url` orqali LexUZ sahifasiga havola, hujjat nomi va modda raqami keltirilgan.

`indexes/` katalogidagi BM25, TF-IDF/LSA va ChromaDB fayllari shu korpusdan tuzilgan. `indexes/manifest.json` korpusning SHA-256 xeshi va indekslash parametrlarini saqlaydi. Indekslar qonun matnining yangi tahrirlarini avtomatik kuzatmaydi.

**Muhim:** korpusning har bir bandi amaldagi LexUZ tahriri bilan to‘liq qo‘lda solishtirilmagan. `verification_status` maydonini ko‘ring va huquqiy xulosa chiqarishdan oldin havoladagi matnni bevosita tekshiring. LexUZ manbalariga havola berilishi ularning yangiligi yoki mustaqil qayta tarqatish huquqi tasdiqlanganini anglatmaydi.

Ushbu repozitoriyda loyiha uchun alohida ochiq kod litsenziyasi ko‘rsatilmagan. Uchinchi tomon matnlari va komponentlaridan foydalanish shartlarini alohida tekshiring.
