"""Restore the original ChromaDB SQLite snapshot losslessly, once per clone."""
from pathlib import Path
import gzip, hashlib, shutil

root = Path(__file__).resolve().parent / "indexes" / "chroma_db"
target = root / "chroma.sqlite3"
if target.exists():
    print("ChromaDB fayli mavjud.")
else:
    expected = (root / "chroma.sqlite3.sha256").read_text().strip()
    temp = root / "chroma.sqlite3.tmp"
    try:
        with gzip.open(root / "chroma.sqlite3.gz", "rb") as src, temp.open("wb") as dst:
            shutil.copyfileobj(src, dst)
        if hashlib.sha256(temp.read_bytes()).hexdigest() != expected:
            raise RuntimeError("ChromaDB snapshot checksum mismatch")
        temp.replace(target)
        print("ChromaDB tiklandi (SHA-256 mos).")
    finally:
        temp.unlink(missing_ok=True)
