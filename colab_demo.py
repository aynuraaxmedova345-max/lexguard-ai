"""Run from Colab. Starts the server and optionally exposes an ephemeral HTTPS link."""
from pathlib import Path
import os, sys, time, subprocess, urllib.request, re, secrets, platform, socket


def start(project='/content/LexGuard_AI', port=7862):
    root=Path(project)
    assert (root/'lexguard_mvp.py').exists() and (root/'data/legal_corpus_unified.jsonl').exists(), 'Backend yoki patch yo‘q.'
    if not os.getenv('OPENAI_API_KEY'):raise RuntimeError('OPENAI_API_KEY Colab Secrets orqali sozlanishi kerak.')
    os.environ['LEXGUARD_PROJECT']=str(root)
    os.environ.setdefault('LEXGUARD_BACKEND','chroma')
    os.environ['LEXGUARD_DEMO_TOKEN']='2026'
    os.environ.setdefault('LEXGUARD_MAX_JOBS','20')
    os.environ.setdefault('LEXGUARD_MAX_SCANS','20')
    # Re-running never attaches to a stale existing server/token.
    with socket.socket() as sock:
        try:sock.bind(('127.0.0.1',port))
        except OSError:
            sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    log=root/'mvp-server.log'
    with log.open('w') as f:
        process=subprocess.Popen([sys.executable,'-m','uvicorn','lexguard_mvp:app','--host','127.0.0.1','--port',str(port),'--no-access-log'],cwd=root,stdout=f,stderr=subprocess.STDOUT)
    for _ in range(75):
        if process.poll() is not None:raise RuntimeError('Server xatosi: '+str(log))
        try:
            with urllib.request.urlopen(f'http://127.0.0.1:{port}/health',timeout=2) as res:
                if res.status==200:break
        except Exception:time.sleep(1)
    else:process.terminate();raise RuntimeError('Server ishga tushmadi. '+str(log))
    print('✅ MVP server tayyor. Demo kirish kodi:',os.environ['LEXGUARD_DEMO_TOKEN'])
    return process,port


def tunnel(port,output='/content/LexGuard_QR.png'):
    import qrcode
    arch={'x86_64':'amd64','aarch64':'arm64'}.get(platform.machine())
    if platform.system()!='Linux' or not arch:raise RuntimeError('Bu helper Linux/Colab uchun.')
    exe=Path('/tmp/lexguard-cloudflared-'+arch)
    if not exe.exists():
        tmp=exe.with_suffix('.download')
        urllib.request.urlretrieve('https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-'+arch,tmp)
        tmp.chmod(0o755);tmp.replace(exe)
    log=Path('/tmp/lexguard-cloudflared.log')
    with log.open('w') as f:
        process=subprocess.Popen([str(exe),'tunnel','--url',f'http://127.0.0.1:{port}','--protocol','http2'],stdout=f,stderr=subprocess.STDOUT)
    urls=[]
    for _ in range(60):
        if process.poll() is not None:break
        urls=re.findall(r'https://[a-z0-9-]+\.trycloudflare\.com',log.read_text(errors='replace'))
        if urls:
            url=urls[0]
            try:
                with urllib.request.urlopen(url+'/health',timeout=4) as r:
                    if r.status==200:break
            except Exception:pass
        time.sleep(1)
    else:urls=[]
    if process.poll() is not None or not urls:
        process.terminate();raise RuntimeError('Tunnel tayyor bo‘lmadi. Lokal Colab iframe yoki oflayn demo ishlating. Log: '+str(log))
    qr=qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M,box_size=12,border=4);qr.add_data(url);qr.make(fit=True);qr.make_image(fill_color='black',back_color='white').save(output)
    print('🌐 Vaqtinchalik manzil:',url);print('QR:',output,'(kod QR ichida yo‘q)')
    return process,url
