"""Internal rate card — v71 (single source of truth for pricing).

Enduku internal:

    Mee directive (v71): "ivanni website lo vaddu, personal ga deal cheyali."
    → Public site lo **prices/slot table ledu** (preview/pages/advertise.html lo
      partner page mattrame undi: placements + policy + WhatsApp/email route).
    → Nijamaina numbers ikkada unnayi: owner + bot (Telegram) kosam. Partner adigithe
      ee numbers tho personal ga deal cheyyandi — site lo public ga chupinchakandi.

Ee module nunchi teesukuntunnavi:
  * tools/revenue_estimate.py (direct-sales estimate lines)
  * run.py --rate-card (owner ki Telegram/console print)
"""
from __future__ import annotations

from typing import Dict, List

#: Monthly slot prices (₹, per month) — print quality band for a TS/AP student site.
SLOTS: List[Dict[str, object]] = [
    {"slot": "Top leaderboard", "telugu": "టాప్ లీడర్‌బోర్డ్", "price": 4000, "bundle": False,
     "where": "Home page, right below the header (every visitor sees it)",
     "format": "Banner — 970×90 / 728×90"},
    {"slot": "Mid-article banner", "telugu": "ఆర్టికల్ మధ్యలో", "price": 3500, "bundle": False,
     "where": "Inside every job/exam article, after the quick answer",
     "format": "Banner or card"},
    {"slot": "In-feed card", "telugu": "ఇన్-ఫీడ్ కార్డ్", "price": 3000, "bundle": False,
     "where": "Middle of the news grid while scrolling",
     "format": "Card"},
    {"slot": "Sidebar sticky", "telugu": "సైడ్‌బార్ స్టిక్కీ", "price": 2000, "bundle": False,
     "where": "Desktop sidebar, follows the scroll",
     "format": "Card"},
    {"slot": "Policy page slot", "telugu": "విధాన పేజీల స్లాట్", "price": 1000, "bundle": False,
     "where": "About / Contact / Editorial policy pages",
     "format": "Card"},
]

#: Everything together — best value for a college/coaching chain.
PACKAGE: Dict[str, object] = {
    "slot": "Full package (all slots)", "telugu": "ఫుల్ ప్యాకేజీ", "price": 8000, "bundle": True,
    "where": "All placements + slots inside every new article",
    "format": "All formats",
}

#: Premium services (higher effort → higher value). Ranges in ₹.
PREMIUM: List[Dict[str, object]] = [
    {"service": "Sponsored article (advertorial)", "price": (8000, 15000), "unit": "per article",
     "what": "A full article about your course/college/service — written and SEO-checked by our "
             "editorial team, clearly labelled SPONSORED, ready for Google News/search."},
    {"service": "Lead generation", "price": (150, 400), "unit": "per verified lead", "min": 50,
     "what": "Student name + phone + interest from our free-updates form — verified and exclusive "
             "to you (never resold)."},
    {"service": "WhatsApp / Telegram broadcast", "price": (1500, 1500), "unit": "per broadcast",
     "what": "One sponsored message with your link in our student channel, clearly labelled."},
]

#: Honest footnotes the owner can quote while dealing personally.
NOTES = (
    "GST/taxes extra. Advance payment before the placement goes live.",
    "Full refund if you cancel before the placement starts.",
    "Season-based and small-business packages available — ask personally.",
    "We never guarantee rankings, traffic or revenue; only real impressions/clicks are shared.",
)


def as_rows() -> List[Dict[str, object]]:
    """Slots + package as flat rows: {'slot','price','bundle'} (estimator + CLI use this)."""
    return [dict(s) for s in SLOTS] + [dict(PACKAGE)]


def single_slots() -> List[Dict[str, object]]:
    """Only the individual (non-bundle) placements."""
    return [dict(s) for s in SLOTS]


def highest_ticket() -> int:
    """Costliest single placement (package excluded) — used for ladder estimates."""
    return max(int(s["price"]) for s in SLOTS)


def full_package_price() -> int:
    return int(PACKAGE["price"])


def as_markdown(include_premium: bool = True) -> str:
    """Telegram/console-ready card — personal dealing kosam (site lo print cheyyaru)."""
    lines = ["**Rate card (personal — site lo public ga ledu)**", ""]
    for row in as_rows():
        star = " ⭐ (best value)" if row.get("bundle") else ""
        lines.append(f"- {row['slot']} — ₹{int(row['price']):,}/month{star} · {row['where']}")
    if include_premium:
        lines.append("")
        lines.append("**Premium services**")
        for p in PREMIUM:
            lo, hi = p["price"]  # type: ignore[misc]
            price = f"₹{lo:,}" if lo == hi else f"₹{lo:,}–₹{hi:,}"
            extra = f" (min {p['min']})" if p.get("min") else ""
            lines.append(f"- {p['service']} — {price} {p['unit']}{extra}")
        lines.append("")
        lines.extend(f"- {n}" for n in NOTES)
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover
    print(as_markdown())
