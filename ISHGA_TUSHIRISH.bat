@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
if not exist ".venv\Scripts\python.exe" (
  echo [1/3] Python virtual muhiti yaratilmoqda...
  py -3.13 -m venv .venv 2>nul
  if errorlevel 1 py -3.12 -m venv .venv 2>nul
  if not exist ".venv\Scripts\python.exe" (
    python -c "import sys,struct; assert sys.version_info[:2] in [(3,12),(3,13)] and struct.calcsize('P')==8" 2>nul
    if errorlevel 1 goto nopython
    python -m venv .venv
    if errorlevel 1 goto failed
  )
)
if not exist ".venv\lexguard_ready" (
  echo [2/3] Kerakli kutubxonalar o'rnatilmoqda...
  ".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements-mvp.txt reportlab
  if errorlevel 1 goto failed
  echo ChromaDB o'rnatilmoqda. Ishlamasa dastur BM25+LSA zaxira rejimini taklif qiladi.
  ".venv\Scripts\python.exe" -m pip install --disable-pip-version-check "chromadb>=1.0,<2.0"
  if errorlevel 1 echo ChromaDB o'rnatilmadi. Diskdagi BM25+LSA indekslari saqlangan.
  echo ok>".venv\lexguard_ready"
)
echo [3/3] LexGuard AI ishga tushirilmoqda...
".venv\Scripts\python.exe" restore_indexes.py
if errorlevel 1 goto failed
".venv\Scripts\python.exe" windows_demo.py %*
if errorlevel 1 goto failed
pause
exit /b 0
:nopython
echo Python 3.12 yoki 3.13 64-bit kerak: https://www.python.org/downloads/windows/
pause
exit /b 1
:failed
echo Xatolik yuz berdi. Yuqoridagi xatolikni nusxalab yuboring. API kalitini yubormang.
pause
exit /b 1
