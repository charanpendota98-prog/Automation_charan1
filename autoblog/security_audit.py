# -*- coding: utf-8 -*-
"""v116 — repository secret and unsafe-deployment audit."""
from __future__ import annotations
import re, subprocess
from pathlib import Path
from typing import Dict, List

ROOT=Path(__file__).resolve().parent.parent
_SKIP={".env.example","security_audit.py"}
_PATTERNS=[
 ("private-key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
 ("telegram-token", re.compile(r"\b\d{8,12}:[A-Za-z0-9_-]{30,}\b")),
 ("google-api-key", re.compile(r"\bAIza[0-9A-Za-z_-]{30,}\b")),
 ("github-token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b")),
 ("generic-secret", re.compile(r"(?i)(?:api[_-]?key|app[_-]?password|client_secret)\s*[:=]\s*['\"]?[A-Za-z0-9_\-/+=]{20,}")),
]

def tracked_files()->List[Path]:
 try:
  out=subprocess.check_output(["git","ls-files"],cwd=ROOT,text=True,stderr=subprocess.DEVNULL,timeout=10)
  return [ROOT/x for x in out.splitlines() if x and Path(x).name not in _SKIP]
 except Exception:return []

def scan()->Dict:
 findings=[]
 for path in tracked_files():
  if not path.is_file() or path.stat().st_size>2_000_000:continue
  try:text=path.read_text(encoding="utf-8",errors="ignore")
  except OSError:continue
  for name,pat in _PATTERNS:
   for match in pat.finditer(text):
    line=text.count("\n",0,match.start())+1
    findings.append({"type":name,"file":str(path.relative_to(ROOT)),"line":line})
 return {"status":"clean" if not findings else "review","findings":findings,"tracked_files":len(tracked_files())}

def run_cli()->int:
 r=scan();print("="*72);print(f"  SECURITY AUDIT: {r['status']} · {r['tracked_files']} tracked files")
 for x in r["findings"][:30]:print(f"  ❌ {x['type']} {x['file']}:{x['line']}")
 if not r["findings"]:print("  ✅ no tracked credential patterns found")
 return 0 if not r["findings"] else 1
