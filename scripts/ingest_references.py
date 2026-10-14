import os
import httpx
from pathlib import Path

API_URL = os.getenv("API_URL", "http://localhost:8001/ingest/pdf")
ROOT_DIR = Path(__file__).resolve().parent.parent
REF_DIR = ROOT_DIR / "data" / "tài liệu tham khảo"
if not REF_DIR.exists():
    REF_DIR = ROOT_DIR / "tài liệu tham khảo"

def ingest_all():
    print(f"Checking {REF_DIR}...")
    files = list(REF_DIR.glob("*.pdf")) + list(REF_DIR.glob("*.docx")) if REF_DIR.exists() else []
    for fpath in files:
        print(f"Ingesting: {fpath.name}...")
        try:
            with open(fpath, "rb") as f:
                resp = httpx.post(API_URL, files={"file": (fpath.name, f, "application/octet-stream")}, timeout=300)
                print(f"  Response: {resp.status_code} | {resp.text[:100]}")
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    ingest_all()
