"""Run locally after installing the included requirements."""
import os, getpass, secrets, threading, webbrowser
from pathlib import Path
os.chdir(Path(__file__).resolve().parent)
os.environ.setdefault('LEXGUARD_PROJECT',str(Path(__file__).resolve().parent))
os.environ.setdefault('LEXGUARD_BACKEND','offline')
if not os.environ.get('OPENAI_API_KEY'):
    os.environ['OPENAI_API_KEY']=getpass.getpass('OpenAI API key (ekranda ko‘rinmaydi): ').strip()
os.environ.setdefault('LEXGUARD_DEMO_TOKEN',secrets.token_urlsafe(12))
print('\nDemo kirish kodi:',os.environ['LEXGUARD_DEMO_TOKEN'],'\nManzil: http://127.0.0.1:7860\n',flush=True)
threading.Timer(2,lambda:webbrowser.open('http://127.0.0.1:7860')).start()
import uvicorn
uvicorn.run('lexguard_mvp:app',host='127.0.0.1',port=7860,workers=1,access_log=False)
