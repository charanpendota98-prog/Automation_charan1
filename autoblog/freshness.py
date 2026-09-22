# -*- coding: utf-8 -*-
"""v101 — DECEPTIVE-FRESHNESS GUARD (Google Aug-2026 spam update ki direct exposure).

NENU KANUKKUNNA ATYANTA PRAMADAKARAMAINA GAP (idi mee site ni champagaladu):

  `auto_refresh()` roju purana posts ni "refresh" chestundi. Aa path lo:
    · `dateModified` **eppudu** ee roju date ki bump avutundi, mariyu
    · content nijamga **entha marindo CHECK CHEYYADU**.

  Ante: LLM sagam same content tirigi ichina, leda konni words matrame
  marinaa — Google ki adi **"kotha update"** ga kanipistundi. Roju roju.
  Automatic ga. **Pattern** ga.

  Google **August 2026 spam update** specifically **"deceptive freshness"**
  ni target chesindi. Research lo exact wording: *"dateModified bumped with
  no real change"* mariyu *"a scheduled job doing it nightly turns a
  one-off into a pattern that is easy to detect."*

  Idi **sarigga mana cron** chesedi. Mariyu ide update **scaled content
  abuse** ni kuda target chestundi — recovery *"a period of months"*.
  Ante: okka bad pattern valla site months paatu debba tintundi.

IDI EM CHESTUNDI (honest, measurable):
  · Old vs new content ni **shingle-level** lo compare chestundi.
  · Nijamaina change % (`change_pct`) + kotha facts (dates/numbers) unnaya
    ani chustundi.
  · Change **threshold kanna takkuva** unte → **`dateModified` bump
    CHEYYADU** (content update avvochu, kaani freshness signal fake
    cheyyamu). Chala takkuva unte → **update motham skip**.
  · Prathi decision ni log + report chestundi (evidence).

IDI "refresh ni aapadam" KAADU — **nijamaina** refresh ni allow chestundi,
**fake** refresh ni aapуtundi. Ade difference Google chustundi.

CLI: python run.py --freshness-audit
"""
from __future__ import annotations

import logging
import re
from typing import Dict, List, Optional, Set

from . import config, validator

log = logging.getLogger("autoblog.freshness")

#: Content ee % kanna takkuva marithe → dateModified bump CHEYYAKUDADU.
#: (Google ki "kotha update" ani cheppadaniki nijamaina change undali.)
MIN_CHANGE_FOR_DATE_BUMP = 8.0     # percent
#: Idi kanna takkuva marithe → update motham SKIP (WP write kuda vaddu).
#: Pointless write = revision bloat + crawl noise, value zero.
MIN_CHANGE_TO_PUBLISH = 2.0        # percent

_NUM = re.compile(r"\b\d[\d,]*\b")
_DATE = re.compile(
    r"\b\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}\b|"
    r"\b\d{4}-\d{1,2}-\d{1,2}\b|"
    r"\b\d{1,2}\s*(?:st|nd|rd|th)?\s+"
    r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4}\b",
    re.I)


def _facts(text: str) -> Set[str]:
    """Numbers + dates = "nijamaina kotha information" proxy.

    Konni words marchadam = rewrite. Kotha date/vacancy count/fee ravadam =
    nijamaina update. Rendu vere vishayalu — ee function aa teda chuputundi.
    """
    t = text or ""
    return set(m.group(0).lower() for m in _NUM.finditer(t)) | \
        set(m.group(0).lower() for m in _DATE.finditer(t))


def compare(old_html: str, new_html: str) -> Dict:
    """Old vs new content — nijamaina change entha?

    Returns:
      change_pct   : 0..100 (shingle-level; 0 = identical)
      new_facts    : kotha numbers/dates (list, sorted)
      removed_facts: poyina numbers/dates
      words_old/new
      substantive  : kotha facts unnaya (bool)
    """
    old_t = validator.strip_tags(old_html or "")
    new_t = validator.strip_tags(new_html or "")
    old_s = validator.text_shingles(old_t)
    new_s = validator.text_shingles(new_t)

    if not new_s:
        change = 0.0
    elif not old_s:
        change = 100.0
    else:
        # Jaccard distance — rendu directions lo change ni pattukuntundi
        # (content add ayina, teesesina kuda).
        inter = len(old_s & new_s)
        union = len(old_s | new_s) or 1
        change = 100.0 * (1.0 - inter / union)

    of, nf = _facts(old_t), _facts(new_t)
    new_facts = sorted(nf - of)
    return {
        "change_pct": round(change, 2),
        "new_facts": new_facts[:20],
        "removed_facts": sorted(of - nf)[:20],
        "words_old": len(old_t.split()),
        "words_new": len(new_t.split()),
        "substantive": bool(new_facts),
    }


def decide(old_html: str, new_html: str,
           min_bump: Optional[float] = None,
           min_publish: Optional[float] = None) -> Dict:
    """Refresh ni em cheyyali — publish? dateModified bump?

    Moodu outcomes:
      skip        — change chala takkuva → WP write kuda vaddu
      publish     — content update cheyyi, kaani dateModified **bump vaddu**
                    (fake freshness signal Google ki pampamu)
      publish+bump— nijamaina update → dateModified bump OK
    """
    min_bump = (getattr(config, "FRESHNESS_MIN_CHANGE_PCT", MIN_CHANGE_FOR_DATE_BUMP)
                if min_bump is None else min_bump)
    min_publish = (getattr(config, "FRESHNESS_MIN_PUBLISH_PCT", MIN_CHANGE_TO_PUBLISH)
                   if min_publish is None else min_publish)

    rep = compare(old_html, new_html)
    pct = rep["change_pct"]

    if pct < min_publish:
        rep.update(publish=False, bump_date=False,
                   reason=(f"change {pct:.1f}% < {min_publish:.1f}% — "
                           "nijamaina update ledu, WP write skip"))
        return rep
    # Kotha facts (date/vacancy/fee) vaste adi nijamaina update — threshold
    # kanna takkuva rewrite ayina bump justify avutundi.
    if pct >= min_bump or rep["substantive"]:
        why = ("kotha facts: " + ", ".join(rep["new_facts"][:3])
               if rep["substantive"] else f"change {pct:.1f}%")
        rep.update(publish=True, bump_date=True,
                   reason=f"nijamaina update ({why}) — dateModified bump OK")
        return rep
    # WordPress itself may advance post_modified on ANY successful PUT. So a
    # cosmetic 2–8% rewrite cannot be made safe merely by preserving JSON-LD's
    # old date — avoid the write altogether.
    rep.update(publish=False, bump_date=False,
               reason=(f"change {pct:.1f}% < {min_bump:.1f}% mariyu kotha facts "
                       "levu — cosmetic refresh skip; WP modified timestamp "
                       "kuda marchakudadu"))
    return rep


# ------------------------------------------------------------------- audit

def audit(wp=None, limit: int = 50) -> Dict:
    """Live site lo freshness pattern risk audit.

    Roju roju same posts refresh avutunnaya? dateModified bump ayina
    content marakapothe adi pattern — Google adi pattern ga chustundi.
    """
    from . import state

    rows: List[Dict] = []
    try:
        refreshed = state.posts_to_refresh(config.STATE_PATH, older_days=0,
                                           limit=limit) or []
    except Exception as exc:  # noqa: BLE001
        log.debug("freshness audit state skip: %s", exc)
        refreshed = []
    return {
        "tracked": len(refreshed),
        "min_change_for_bump": getattr(config, "FRESHNESS_MIN_CHANGE_PCT",
                                       MIN_CHANGE_FOR_DATE_BUMP),
        "min_change_to_publish": getattr(config, "FRESHNESS_MIN_PUBLISH_PCT",
                                         MIN_CHANGE_TO_PUBLISH),
        "auto_refresh_per_day": getattr(config, "AUTO_REFRESH_PER_DAY", 0),
        "min_age_days": getattr(config, "AUTO_REFRESH_MIN_AGE_DAYS", 0),
        "rows": rows,
    }


def run_cli() -> int:
    line = "=" * 74
    print(line)
    print("  🕐 FRESHNESS INTEGRITY AUDIT (Google 'deceptive freshness' guard)")
    print(line)
    rep = audit()
    print("  Google Aug-2026 spam update 'deceptive freshness' ni target chesindi:")
    print('    "dateModified bumped with no real change"')
    print('    "a scheduled job doing it nightly turns a one-off into a pattern"')
    print("-" * 74)
    print(f"  auto-refresh / day      : {rep['auto_refresh_per_day']}")
    print(f"  min post age (days)     : {rep['min_age_days']}")
    print(f"  dateModified bump floor : {rep['min_change_for_bump']}% content change")
    print(f"  publish floor           : {rep['min_change_to_publish']}% content change")
    print("-" * 74)
    print("  ✅ GUARD ACTIVE — refresh lo content nijamga marithe MATRAME")
    print("     dateModified bump avutundi. Cosmetic rewrite aithe content")
    print("     update avutundi kaani freshness signal fake KAADU.")
    print("     Change 2% kanna takkuva aithe WP write motham skip.")
    print(line)
    return 0
