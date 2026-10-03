# -*- coding: utf-8 -*-
"""v197.2 — DEPLOY VERIFY (zip upload tarvata live site nijamga update ayyinda?).

Enduku ee module: `--live-audit` (v186) site health ni chustundi, kaani "kotha
theme **nijamga** deploy ayyinda? quiz + poll + menu live lo render avutunnaya?"
anedi veru. Owner zip upload chesi, "Run setup now" nokkina tarvata ee okka
command tho motta proof vastundi:

    python run.py --verify-deploy                 # .env lo WP_SITE use cheyy
    python run.py --verify-deploy --verify-url https://studentup.in --verify-notify

Checks (11) — anni read-only HTTP GET (emi marchadu, emi publish cheyyadu):

  V1  theme version live (style.css) — 1.9.39+ leda "zip upload pending"
  V2  mega menu home lo (su-has-mega · data-su-mega · recommended card · aria)
  V3  menu JS + engage JS serve avutunnaya (content lo expected strings)
  V4  quiz home lo — server-rendered questions + nonce form + Quiz JSON-LD
  V5  poll home lo — options + Question schema
  V6  /daily-quiz/ page (200 · quiz + poll + canonical) → setup step finish ayyinda
  V7  worldclass.css v197 classes serve (`.su-mega-col` · `.su-quiz-card` · `.su-poll-opt`)
  V8  sprite block + prathi `<use href="#su-i-…">` ki symbol undi (blank icon guard)
  V9  sitemap lo daily-quiz URL undi
  V10 poll REST route (`/wp-json/studentup/v1/poll`) JSON istundi
  V11 raw-SVG-as-text regression live lo ledu (theme toggle JS innerHTML)

Exit: 0 = fail ledu (warnings ok) · 1 = fail undi · 2 = site reach avvatledu.
Report: `output/deploy-verify.json` + readable text (+ optional Telegram).
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

UA = ("Mozilla/5.0 (compatible; StudentUpDeployVerify/1.0; +https://studentup.in) "
      "AppleWebKit/537.36 Chrome/120 Safari/537.36")

THEME_MIN = "1.9.39"
TE = re.compile(r"[\u0C00-\u0C7F]")


def _now() -> datetime:
    from datetime import timedelta
    return datetime.now(timezone(timedelta(hours=5, minutes=30)))


def _res(cid: str, name: str, status: str, detail: str = "") -> Dict:
    """status: pass | warn | fail | skip"""
    return {"id": cid, "name": name, "status": status, "detail": detail}


class Fetcher:
    """Chinna HTTP layer — tests lo fake tho swap cheyyachu (offline safe)."""

    def __init__(self, timeout: int = 25) -> None:
        self.timeout = max(5, int(timeout or 25))

    def get(self, url: str) -> Tuple[int, str, Dict[str, str]]:
        import requests

        r = requests.get(url, timeout=self.timeout, allow_redirects=True,
                         headers={"User-Agent": UA, "Accept": "text/html,*/*"})
        return r.status_code, r.text or "", dict(r.headers or {})


# --------------------------------------------------------------- utilities

def _vnum(v: str) -> Tuple[int, ...]:
    try:
        return tuple(int(x) for x in re.findall(r"\d+", v)[:3]) or (0,)
    except Exception:  # noqa: BLE001
        return (0,)


def _quiz_block(html: str) -> str:
    """Quiz card + form markup (home lo section id 'daily-quiz' tho vastundi)."""
    m = re.search(r'<section[^>]*class="[^"]*su-quiz[^"]*".*?</section>', html, re.S)
    return m.group(0) if m else ""


def _poll_block(html: str) -> str:
    m = re.search(r'<section[^>]*class="[^"]*su-poll[^"]*".*?</section>', html, re.S)
    return m.group(0) if m else ""


def verify(url: str, fetcher: Optional[Fetcher] = None,
           timeout: int = 25) -> Dict:
    """Anni checks run chesi report istundi (raise cheyyadu — report istundi)."""
    url = (url or "").rstrip("/")
    f = fetcher or Fetcher(timeout=timeout)
    checks: List[Dict] = []
    next_steps: List[str] = []

    # ---- reachability + home (okkasari fetch, anni checks ki reuse)
    home = ""
    try:
        status, home, _h = f.get(url + "/")
    except Exception as exc:  # noqa: BLE001 — SSL/timeout: clean report
        return {
            "url": url, "at": _now().isoformat(timespec="seconds"),
            "theme_live": "?", "theme_min": THEME_MIN,
            "verdict": "UNREACHABLE", "score": 0,
            "counts": {"pass": 0, "warn": 0, "fail": 1, "skip": 0},
            "checks": [_res("V0", "site reachable", "fail",
                            f"{type(exc).__name__}: {str(exc)[:160]}")],
            "next_steps": ["Hosting status / SSL chudandi (MilesWeb). "
                           "Tarvata malli ee command run cheyyandi."],
        }
    if status >= 400:
        checks.append(_res("V0", "site reachable", "fail", f"HTTP {status}"))
    else:
        checks.append(_res("V0", "site reachable", "pass", f"HTTP {status} · {len(home)} B"))

    # ---- V1 theme version (style.css = source of truth)
    ver = ""
    try:
        st, css, _ = f.get(url + "/wp-content/themes/studentup/style.css")
        m = re.search(r"Version:\s*([0-9.]+)", css or "")
        ver = m.group(1) if m else ""
        if st >= 400 or not ver:
            checks.append(_res("V1", "theme version live", "warn",
                               f"style.css HTTP {st} — theme folder name/path veru undi?"))
        elif _vnum(ver) >= _vnum(THEME_MIN):
            checks.append(_res("V1", "theme version live", "pass", f"v{ver} ≥ {THEME_MIN}"))
        else:
            checks.append(_res("V1", "theme version live", "fail",
                               f"v{ver} (kavalsindi {THEME_MIN}+) — zip upload pending"))
            next_steps.append("WP Admin → Appearance → Themes → Add New → Upload Theme → "
                              "studentup-theme.zip → Install → Activate")
    except Exception as exc:  # noqa: BLE001
        checks.append(_res("V1", "theme version live", "warn", type(exc).__name__))

    # ---- V2 mega menu
    mega_ok = ("su-has-mega" in home and "data-su-mega" in home
               and "su-mega-feat" in home and 'aria-haspopup="true"' in home)
    checks.append(_res("V2", "advanced mega menu (home)", "pass" if mega_ok else "fail",
                       "columns + recommended card + aria" if mega_ok else
                       "mega markup ledu — theme 1.9.39+ activate ayyinda?"))
    if not mega_ok:
        next_steps.append("Theme activate tarvata cache clear (LiteSpeed → Purge All) "
                          "chesi malli chudandi")

    # ---- V3 menu + engage JS
    for fname, needle, cid, nm in (
        ("studentup-menu.js", "aria-expanded", "V3a", "menu JS (keyboard/aria)"),
        ("studentup-engage.js", "su_quiz_streak", "V3b", "engage JS (quiz/poll)"),
    ):
        try:
            st, js, _ = f.get(url + "/wp-content/themes/studentup/assets/js/" + fname)
            ok = st < 400 and needle in (js or "")
            checks.append(_res(cid, nm, "pass" if ok else "fail",
                               f"HTTP {st} · {len(js or '')} B" +
                               ("" if ok else f" · '{needle}' ledu")))
        except Exception as exc:  # noqa: BLE001
            checks.append(_res(cid, nm, "warn", type(exc).__name__))

    # ---- V4 quiz (server-rendered + no-JS form + schema)
    qb = _quiz_block(home)
    q_count = qb.count('class="su-q"')
    q_ok = ("data-su-quiz-form" in qb and "su_quiz_nonce" in qb
            and q_count >= 1 and "data-su-why" in qb)
    checks.append(_res("V4", "daily quiz on home (server-rendered · no-JS form)",
                       "pass" if q_ok else "fail",
                       f"{q_count} question(s) + nonce" if q_ok else
                       "quiz markup ledu — front-page call / module require chudandi"))
    if q_ok and '"Quiz"' not in home:
        checks.append(_res("V4b", "Quiz JSON-LD", "warn", "schema block kanipinchaledu"))
    elif q_ok:
        checks.append(_res("V4b", "Quiz JSON-LD", "pass", "'@type: Quiz' served"))

    # ---- V5 poll
    pb = _poll_block(home)
    p_ok = ("data-su-poll" in pb and pb.count("su-poll-opt") >= 3)
    checks.append(_res("V5", "reader poll on home", "pass" if p_ok else "fail",
                       f"{pb.count('su-poll-opt')} option(s)" if p_ok else
                       "poll markup ledu"))

    # ---- V6 /daily-quiz/ page (setup step)
    try:
        st, page, _ = f.get(url + "/daily-quiz/")
        ok = st < 400 and "data-su-quiz-form" in page and "data-su-poll" in page
        checks.append(_res("V6", "/daily-quiz/ page", "pass" if ok else "fail",
                           f"HTTP {st} · quiz+poll render" if ok else
                           f"HTTP {st} — page/setup missing"))
        if not ok:
            next_steps.append("WP Admin → StudentUp → **Run setup now** "
                              "(idi /daily-quiz/ page ni create chestundi)")
        elif TE.search(page):
            checks.append(_res("V6b", "quiz page English-only (v73)", "warn",
                               "Telugu text kanipinchindi"))
        else:
            checks.append(_res("V6b", "quiz page English-only (v73)", "pass", "clean"))
    except Exception as exc:  # noqa: BLE001
        checks.append(_res("V6", "/daily-quiz/ page", "warn", type(exc).__name__))

    # ---- V7 CSS v197 classes served
    try:
        st, css, _ = f.get(url + "/wp-content/themes/studentup/assets/css/worldclass.css")
        need = (".su-mega-col", ".su-quiz-card", ".su-poll-opt")
        missing = [n for n in need if n not in (css or "")]
        checks.append(_res("V7", "worldclass.css v197 classes",
                           "pass" if st < 400 and not missing else "fail",
                           f"HTTP {st} · {len(css or '')} B" if not missing else
                           f"missing: {', '.join(missing)}"))
    except Exception as exc:  # noqa: BLE001
        checks.append(_res("V7", "worldclass.css v197 classes", "warn", type(exc).__name__))

    # ---- V8 sprite completeness (blank icon guard)
    symbols = set(re.findall(r'<symbol[^>]*id="(su-i-[a-z0-9_-]+)"', home))
    used = set(re.findall(r'href="#(su-i-[a-z0-9_-]+)"', home))
    missing = sorted(used - symbols)
    checks.append(_res("V8", "icon sprite complete", "pass" if used and not missing else "fail",
                       f"{len(used)} icons · all resolved" if used and not missing else
                       (f"missing: {missing[:4]}" if missing else "sprite ledu — blank icons risk")))

    # ---- V9 sitemap has the quiz page
    try:
        st, sm, _ = f.get(url + "/page-sitemap.xml")
        if st >= 400:
            st2, sm, _ = f.get(url + "/sitemap_index.xml")
        ok = st < 400 and "daily-quiz" in (sm or "")
        checks.append(_res("V9", "sitemap lo daily-quiz", "pass" if ok else "warn",
                           "URL undi" if ok else "kanipinchaledu (setup tarvata regenerate)"))
    except Exception as exc:  # noqa: BLE001
        checks.append(_res("V9", "sitemap lo daily-quiz", "warn", type(exc).__name__))

    # ---- V10 poll REST route
    try:
        st, body, _ = f.get(url + "/wp-json/studentup/v1/poll")
        ok = st < 400 and '"question"' in (body or "")
        checks.append(_res("V10", "poll REST route", "pass" if ok else "warn",
                           f"HTTP {st}" if ok else f"HTTP {st} — route ledu/permission"))
    except Exception as exc:  # noqa: BLE001
        checks.append(_res("V10", "poll REST route", "warn", type(exc).__name__))

    # ---- V11 raw-SVG-as-text regression (live)
    try:
        st, js, _ = f.get(url + "/wp-content/themes/studentup/assets/js/studentup.js")
        bad = re.search(r"textContent\s*=\s*[^\n;]*<svg", js or "")
        checks.append(_res("V11", "theme toggle: no raw SVG text",
                           "fail" if bad else "pass",
                           "textContent ki SVG assign avutundi!" if bad else
                           "innerHTML path clean"))
    except Exception as exc:  # noqa: BLE001
        checks.append(_res("V11", "theme toggle: no raw SVG text", "warn", type(exc).__name__))

    counts = {"pass": 0, "warn": 0, "fail": 0, "skip": 0}
    for c in checks:
        counts[c["status"]] = counts.get(c["status"], 0) + 1
    total = max(1, counts["pass"] + counts["warn"] + counts["fail"])
    score = int(round(counts["pass"] / total * 100))
    verdict = "LIVE ✔" if not counts["fail"] else ("PARTIAL — zip/setup pending"
                                                   if counts["pass"] else "NOT DEPLOYED")
    return {"url": url, "at": _now().isoformat(timespec="seconds"),
            "theme_live": ver or "?", "theme_min": THEME_MIN,
            "verdict": verdict, "score": score, "counts": counts,
            "checks": checks, "next_steps": next_steps}


# ------------------------------------------------------------------ output

ICON = {"pass": "✅", "warn": "⚠️ ", "fail": "❌", "skip": "⏭️ "}


def report_text(rep: Dict) -> str:
    lines = ["=" * 74,
             "  🚀 DEPLOY VERIFY (v197) — live site lo kotha theme nijamga unda?",
             "=" * 74,
             f"  url   : {rep['url']}",
             f"  theme : v{rep.get('theme_live', '?')} (kavalsindi {rep.get('theme_min')}+)"
             f" · {len(rep['checks'])} checks",
             f"  verdict: {rep['verdict']} · score {rep['score']}/100 · "
             + " · ".join(f"{k} {v}" for k, v in rep["counts"].items() if v),
             "-" * 74]
    for c in rep["checks"]:
        lines.append(f"  {ICON.get(c['status'], '·')} {c['id']:<4} {c['name']}"
                     + (f" — {c['detail']}" if c["detail"] else ""))
    if rep.get("next_steps"):
        lines += ["-" * 74, "  NEXT STEPS:"]
        lines += [f"    {i}. {s}" for i, s in enumerate(rep["next_steps"], 1)]
    lines.append("=" * 74)
    return "\n".join(lines)


def save_report(rep: Dict, out: Optional[Path] = None) -> Path:
    from . import config

    path = Path(out or config.OUTPUT_DIR / "deploy-verify.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
    md = path.with_suffix(".md")
    md.write_text(report_text(rep), encoding="utf-8")
    return path


def run(url: str = "", notify: bool = False, timeout: int = 25,
        fetcher: Optional[Fetcher] = None) -> Dict:
    from . import config

    target = (url or getattr(config, "WP_SITE", "") or "").strip()
    if not target.startswith(("http://", "https://")):
        print("  ❌ URL kavali: --verify-url https://studentup.in "
              "(leda .env lo WP_SITE)")
        return {"error": "no-url"}
    rep = verify(target, fetcher=fetcher, timeout=timeout)
    print(report_text(rep))
    if "error" not in rep:
        p = save_report(rep)
        print(f"  📄 {p} · {p.with_suffix('.md')}")
    if notify and rep.get("url"):
        try:
            from . import notifier
            head = " | ".join(f"{k} {v}" for k, v in rep["counts"].items() if v)
            notifier.send_telegram(
                f"🚀 <b>Deploy verify {rep['verdict']}</b> · score {rep['score']}/100\n"
                f"theme v{rep.get('theme_live', '?')} · {head}\n{rep['url']}")
        except Exception as exc:  # noqa: BLE001 — notify fail verify ni aapadu
            print(f"  ⚠️ notify fail: {exc}")
    return rep


def run_cli(url: str = "", notify: bool = False, timeout: int = 25) -> int:
    rep = run(url=url, notify=notify, timeout=timeout)
    if rep.get("error") == "no-url":
        return 2
    if rep.get("verdict") == "UNREACHABLE":
        return 2
    return 1 if rep["counts"]["fail"] else 0
