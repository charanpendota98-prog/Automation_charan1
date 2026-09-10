"""v20 — Authority hub pages (playbook Phase 2/3: exam hubs = topical
authority + session depth + internal-link hubs).

For each HUB_EXAMS entry: search published posts matching the exam, build one
hub PAGE (idempotent upsert by slug) that lists everything with links, plus
cross-links between hubs (cluster). Pages with <2 matching posts are SKIPPED —
thin hub pages are exactly the 'scaled content' spam pattern; we never make
empty shelves.
"""
from __future__ import annotations

import logging
import re
from datetime import date

from . import config, seo
from .wordpress_client import WordPressClient

log = logging.getLogger("autoblog.hubs")


def _slugify(text: str) -> str:
    t = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return (t or "hub")[:55]


def build_hub_html(exam: str, posts: list, year: int,
                   all_exams: list) -> str:
    """Pure builder — testable without network. posts: [{title, link, date}]."""
    esc = seo._esc
    rows = "".join(
        "<tr><td><a href=\"{lk}\">{ti}</a></td><td>{dt}</td></tr>".format(
            lk=p.get("link", ""), ti=esc(p.get("title", "")[:70]),
            dt=(p.get("date") or "")[:10])
        for p in posts[:12]
    )
    lis = "".join(
        f"<li><a href=\"{p.get('link', '')}\">{_short(p.get('title', ''))}</a></li>"
        for p in posts[:8]
    )
    cross = "".join(
        "<li><a href=\"{base}/{sl}/\">{ex} {yr} — Hub</a></li>".format(
            base=config.WP_SITE.rstrip("/"), sl=_slugify(ex) + "-hub",
            ex=esc(ex), yr=year)
        for ex in all_exams if ex != exam)[:1200] or "<li>—</li>"
    return (
        f"<p><strong>{exam} {year}</strong> — latest notifications, results, "
        "hall tickets, answer keys aur important dates anni okkada. Prathi "
        "update check chesi 24 hours lo ee page add chestam; bookmark cheyandi.</p>"
        f"<h2>{exam}: Latest Updates</h2>"
        "<table><tr><th>Post</th><th>Published</th></tr>"
        f"{rows}</table>"
        f"<h2>{exam} — Quick Links ({year})</h2>"
        f"<ul>{lis}</ul>"
        "<h2>EE Page Enduku Useful?</h2>"
        "<ul><li>Notification → apply steps okka chota</li>"
        "<li>Results + hall tickets fast links</li>"
        "<li>Cut off, salary, eligibility explainers</li>"
        "<li>Missed deadline → next exam dates</li></ul>"
        f"<h2>More Exam Hubs ({year})</h2>"
        f"<ul>{cross}</ul>"
        f"<p style=\"font-size:13px;color:#57616B;\">\U0001f504 Last updated: "
        f"{date.today().isoformat()} \\u00b7 Correction undo? "
        f"<a href=\"mailto:{config.SUPPORT_EMAIL}\">{config.SUPPORT_EMAIL}</a>"
        " — 24h fix.</p>"
    )


def _short(title: str, words: int = 8) -> str:
    parts = (title or "").strip().split()
    return " ".join(parts[:words]) + (" …" if len(parts) > words else "")


def rebuild_hubs(dry_run: bool = False) -> list:
    """Create/update one hub page per exam with >=2 matching posts."""
    wp = WordPressClient()
    year = date.today().year
    out = []
    for exam in config.HUB_EXAMS:
        posts = wp.search_posts(exam, per_page=12) or []
        if len(posts) < 2:
            log.info("HUB skip: '%s' — %d posts (need 2+; no thin pages)",
                     exam, len(posts))
            continue
        html = build_hub_html(exam, posts, year, config.HUB_EXAMS)
        slug = _slugify(exam) + "-hub"
        title = f"{exam} {year} Hub: Notifications, Results & Hall Tickets"[:70]
        if dry_run:
            out.append({"exam": exam, "slug": slug, "posts": len(posts),
                        "dry": True})
            continue
        try:
            res = wp.upsert_page(title, html, slug)
            out.append({"exam": exam, "slug": slug, "posts": len(posts),
                        "link": res.get("link")})
            log.info("HUB %s ✔ (%d posts linked) %s", slug, len(posts),
                     res.get("link", ""))
        except Exception as exc:  # noqa: BLE001 — one hub fail skip
            log.warning("HUB %s failed: %s", slug, exc)
    log.info("Hubs rebuilt: %d pages", len(out))
    return out
