"""Local single-worker demo; no Colab dependency. Key never written to disk."""
import argparse, getpass, json, os, platform, re, socket, subprocess, sys, time
import urllib.request, webbrowser
from pathlib import Path
ROOT = Path(__file__).resolve().parent
PORT = 7862

def check(backend):
    from legal_retrieval_v3 import ScopedRetriever
    eng = ScopedRetriever(ROOT, backend)
    assert len(eng.eng.rows) == 8071
    assert eng.candidates('Xodim haftasiga 48 soat ishlashi shart.', 'mehnat', '', top_k=5)
    print(f'OK: 8071 huquqiy birlik, {backend} qidiruvi.', flush=True)

def download_tunnel():
    arch = {'amd64':'amd64','x86_64':'amd64','arm64':'arm64','aarch64':'arm64'}.get(platform.machine().lower())
    if not arch: raise RuntimeError('Cloudflare: noma’lum protsessor turi.')
    target = ROOT/'cloudflared.exe'
    if not target.exists():
        url = f'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-{arch}.exe'
        tmp = target.with_suffix('.download')
        print('Cloudflare rasmiy GitHub sahifasidan yuklanmoqda...', flush=True)
        try:
            with urllib.request.urlopen(url, timeout=45) as response, tmp.open('wb') as out:
                while chunk := response.read(1024*1024): out.write(chunk)
            tmp.replace(target)
        finally:
            tmp.unlink(missing_ok=True)
    subprocess.run([str(target), '--version'], check=True, timeout=15)
    return target

def health(url):
    with urllib.request.urlopen(url+'/health',timeout=4) as r:
        obj=json.load(r)
    return obj.get('service')=='LexGuard AI' and obj.get('corpus_present') and obj.get('api_configured') and obj.get('token_configured')

def wait_health(proc,url,seconds):
    deadline=time.monotonic()+seconds
    while time.monotonic()<deadline and proc.poll() is None:
        try:
            if health(url):return True
        except Exception:pass
        time.sleep(1)
    return False

def stop(p):
    if p is None or p.poll() is not None:return
    p.terminate()
    try:p.wait(timeout=8)
    except subprocess.TimeoutExpired:p.kill();p.wait()

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--offline',action='store_true',help='ChromaDB o‘rniga diskdagi BM25 + LSA. API baribir internet talab qiladi.')
    p.add_argument('--check',action='store_true')
    p.add_argument('--local-only',action='store_true')
    args=p.parse_args()
    os.chdir(ROOT)
    backend='offline' if args.offline else 'chroma'
    try:check(backend)
    except Exception as exc:
        if args.offline or args.check:raise
        print('ChromaDB tekshiruvi muvaffaqiyatsiz:',type(exc).__name__)
        print('Zaxira BM25 + LSA qidiruvi tekshirilmoqda. Bu ChromaDB ishlatilayotganini anglatmaydi.')
        backend='offline';check(backend)
    if args.check:return
    env=os.environ.copy()
    key=env.get('OPENAI_API_KEY') or getpass.getpass('OpenAI API kalitini kiriting (ko‘rinmaydi): ').strip()
    if not key:raise RuntimeError('API kaliti kiritilmadi.')
    env.update(OPENAI_API_KEY=key,LEXGUARD_PROJECT=str(ROOT),LEXGUARD_BACKEND=backend,LEXGUARD_DEMO_TOKEN='2026',LEXGUARD_MAX_JOBS='20',LEXGUARD_MAX_SCANS='20',PYTHONUTF8='1')
    with socket.socket() as s:
        try:s.bind(('127.0.0.1',PORT));port=PORT
        except OSError:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
    local=f'http://127.0.0.1:{port}'
    server=tunnel=None
    # Old QR/URL should never be mistaken for the current session.
    for f in ('LexGuard_QR.png','LexGuard_URL.txt'):(ROOT/f).unlink(missing_ok=True)
    try:
        with (ROOT/'mvp-server.log').open('w',encoding='utf-8') as log:
            server=subprocess.Popen([sys.executable,'-m','uvicorn','lexguard_mvp:app','--host','127.0.0.1','--port',str(port),'--workers','1','--no-access-log'],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
        if not wait_health(server,local,90):raise RuntimeError('Server tayyor emas: mvp-server.log faylini tekshiring.')
        print('\nLOKAL SAYT:',local,'\nDEMO KOD: 2026\nQIDIRUV:',backend,flush=True)
        webbrowser.open(local)
        if not args.local_only:
            try:
                import qrcode
                exe=download_tunnel()
                # No OpenAI key is passed to cloudflared.
                tenv=os.environ.copy();tenv.pop('OPENAI_API_KEY',None)
                with (ROOT/'cloudflare.log').open('w',encoding='utf-8') as log:
                    tunnel=subprocess.Popen([str(exe),'tunnel','--url',local,'--protocol','http2'],cwd=ROOT,env=tenv,stdout=log,stderr=subprocess.STDOUT)
                deadline=time.monotonic()+90; public=None
                while time.monotonic()<deadline and tunnel.poll() is None:
                    urls=re.findall(r'https://[a-z0-9-]+\.trycloudflare\.com',(ROOT/'cloudflare.log').read_text(encoding='utf-8',errors='replace'))
                    if urls:
                        try:
                            if health(urls[0]):public=urls[0];break
                        except Exception:pass
                    time.sleep(1)
                if not public:raise RuntimeError('Tunnel tayyor emas. cloudflare.log faylini tekshiring.')
                qr=qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M,box_size=12,border=4);qr.add_data(public);qr.make(fit=True);qr.make_image(fill_color='black',back_color='white').save(ROOT/'LexGuard_QR.png')
                (ROOT/'LexGuard_URL.txt').write_text(public+'\n',encoding='utf-8')
                print('\nINTERNET SAYTI:',public,'\nQR: LexGuard_QR.png',flush=True)
                webbrowser.open(public)
            except Exception as exc:
                stop(tunnel);tunnel=None
                print('TUNNEL XATOSI:',str(exc),'\nLokal sayt ishlashda davom etadi.',flush=True)
        print('\nUshbu oynani ochiq qoldiring. To‘xtatish: Ctrl+C.',flush=True)
        warned=False
        while server.poll() is None:
            if tunnel is not None and tunnel.poll() is not None and not warned:
                warned=True;print('Tunnel to‘xtadi. Lokal sayt ishlamoqda. Qayta ishga tushirib yangi QR oling.',flush=True)
            time.sleep(2)
        raise RuntimeError('Server to‘xtadi. mvp-server.log faylini tekshiring.')
    except KeyboardInterrupt:print('\nServer to‘xtatilmoqda.')
    finally:stop(tunnel);stop(server)

if __name__=='__main__':main()
