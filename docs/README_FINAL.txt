LEXGUARD AI — FINAL MVP (V3.1 huquqiy analizator saqlangan)

Mavjud Colab: LexGuard_AI_FINAL_PATCH.zip ichidagi fayllarni /content/LexGuard_AI ga oching.
Pillow va qrcode[pil] qo‘shiladi. V3.1 va mavjud indekslarni qayta yaratish kerak emas.
Server ishga tushishi uchun avval OPENAI_API_KEY Colab Secrets sozlangan bo‘lsin.

from google.colab import userdata, output
import sys, os
sys.path.insert(0, '/content/LexGuard_AI')
os.environ['OPENAI_API_KEY']=userdata.get('OPENAI_API_KEY')
from colab_demo import start, tunnel
server, port=start()
output.serve_kernel_port_as_iframe(port, height=1000)

tunnel_process, public_url=tunnel(port)
from IPython.display import display, Image
display(Image(filename='/content/LexGuard_QR.png'))

QR faqat URLni o‘z ichiga oladi. Demo kirish kodi hakamlarga alohida beriladi.
Tunnel doimiy hosting emas: runtime yoki tunnel o‘chsa URL ishlamaydi, qayta ochilganda URL o‘zgaradi.
Faqat anonim/sun’iy hujjatlar bilan demo qiling. OpenAI matn/rasmni qayta ishlaydi; huquqiy xulosalar dastlabki.
Har bir rasm alohida sahifa; JPG/PNG <=10 MB, 30 MP. PDF/DOCX/TXT <=5 MB, tahlil 30 bandgacha.
PDF skaneri faqat matnli PDF uchun; rasmli PDF sahifasini JPG/PNG qilib yuboring.
Telefon kamerasi HTML capture orqali ishlaydi, aniq xatti-harakat brauzer/OSga bog‘liq.
Tahlil va skanerlash jonli API talab qiladi. Saqlangan arxiv V3.0 haqiqiy avvalgi sinov; jonli V3.1 emas.
PDF hisobot: PDF / Chop etish -> Save as PDF. Matnni tahrirlash va tasdiqlash shart.
Tavsiyalar tayyor yuridik tahrir deb da'vo qilinmaydi. LexUZ bilan to‘liq rasmiy verifikatsiya hali bajarilmagan.
API token frontendga joylanmagan, 20 tahlil/20 skan limitlari server jarayoniga tegishli.
To‘liq paket: talablar uchun pip install -r requirements-mvp.txt -r requirements-chroma.txt; python start_mvp.py.
Colab qayta ishga tushirilsa oldin server.terminate() va tunnel_process.terminate() bilan eski jarayonlarni yoping.
Test: python -m pytest -q test_scan_mvp.py test_mvp_ui.py (mock API).
