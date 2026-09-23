# -*- coding: utf-8 -*-
"""v109 — mobile performance, accessibility and CWV audit.

SEO content cannot compensate for a slow or inaccessible page. Uses the public
PageSpeed Insights endpoint when available; stores the result for comparison.
No fake PASS when the API is unavailable.
"""
from __future__ import annotations
import json
from datetime import date
from pathlib import Path
from typing import Dict
import requests
from . import config


def _out() -> Path:
    p = Path(config.OUTPUT_DIR) / "performance_audits"
    p.mkdir(parents=True, exist_ok=True)
    return p


def fetch(url: str, strategy: str = "mobile") -> Dict:
    params = {"url": url, "strategy": strategy,
              "category": ["performance", "accessibility", "seo"]}
    key = getattr(config, "PAGESPEED_API_KEY", "")
    if key:
        params["key"] = key
    r = requests.get("https://www.googleapis.com/pagespeedonline/v5/runPagespeed",
                     params=params, timeout=config.HTTP_TIMEOUT)
    if r.status_code != 200:
        raise RuntimeError(f"PageSpeed HTTP {r.status_code}: {r.text[:250]}")
    raw = r.json()
    cats = raw.get("lighthouseResult", {}).get("categories", {})
    audits = raw.get("lighthouseResult", {}).get("audits", {})
    def score(name):
        value = cats.get(name, {}).get("score")
        return round(value * 100) if isinstance(value, (int, float)) else None
    metrics = {}
    for key_name in ("largest-contentful-paint", "cumulative-layout-shift",
                     "interaction-to-next-paint", "first-contentful-paint"):
        a = audits.get(key_name, {})
        metrics[key_name] = {"numeric": a.get("numericValue"),
                             "display": a.get("displayValue"),
                             "score": a.get("score")}
    result = {"version": "v109", "url": url, "strategy": strategy,
              "checked_at": date.today().isoformat(),
              "scores": {"performance": score("performance"),
                         "accessibility": score("accessibility"),
                         "seo": score("seo")},
              "metrics": metrics,
              "opportunities": []}
    for aid, a in audits.items():
        if a.get("details", {}).get("type") == "opportunity" and a.get("score", 1) < 0.9:
            result["opportunities"].append({"id": aid, "title": a.get("title", ""),
                                             "display": a.get("displayValue", "")})
    result["opportunities"] = result["opportunities"][:25]
    result["status"] = "pass" if all((v or 0) >= 80 for v in result["scores"].values()) else "review"
    return result


def save(result: Dict) -> Path:
    slug = result.get("url", "site").replace("https://", "").replace("http://", "")
    slug = "".join(c if c.isalnum() else "-" for c in slug).strip("-")[:120]
    path = _out() / f"{slug or 'site'}.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def run_cli(url: str) -> int:
    try:
        result = fetch(url)
        path = save(result)
    except Exception as exc:  # noqa: BLE001
        print(f"❌ PageSpeed audit unavailable: {exc}")
        print("   API fail aithe fake performance PASS create cheyyamu.")
        return 1
    print("=" * 74)
    print(f"  MOBILE PERFORMANCE AUDIT: {url}")
    print("=" * 74)
    for k, v in result["scores"].items():
        print(f"  {k:16}: {v}/100")
    for k, v in result["metrics"].items():
        print(f"  {k:28}: {v.get('display') or v.get('numeric')}")
    print(f"  status            : {result['status']}")
    print(f"  report            : {path}")
    print("-" * 74)
    for item in result["opportunities"][:10]:
        print(f"  • {item['title']} {item['display']}")
    return 0
