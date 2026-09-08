"""Revenue/monetization tests.

Verifies:
  1. telegram_cta_block: channel link + before-schema placement
  2. affiliate_block: keyword match, rel sponsored nofollow, disclosure,
     no-match -> empty, bad lines skipped
  3. append_blocks: schema scripts STILL LAST (valid document order)
  4. seasonal category boost + high-CPC listicle share
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from autoblog import config, monetize, state, topic_engine  # noqa: E402

HTML_WITH_SCHEMA = (
    "<p>intro para content here friends</p>"
    "<h2>Body</h2><p>body</p>"
    '<script type="application/ld+json">{"@type":"Article"}</script>'
    '<script type="application/ld+json">{"@type":"FAQPage"}</script>'
)


def main():
    print("REVENUE / MONETIZATION TESTS:")

    # ---- 1. CTA block ----
    config.TELEGRAM_CHANNEL_URL = "https://t.me/studentup"
    cta = monetize.telegram_cta_block()
    assert 'href="https://t.me/studentup"' in cta and "Telegram" in cta
    config.TELEGRAM_CHANNEL_URL = ""
    assert monetize.telegram_cta_block() == ""
    print("  1. telegram_cta_block (link + off-safe) ✔")

    # ---- 2. affiliate block ----
    config.AFFILIATE_LINKS = (
        "Free Resume Builder|https://example.com/resume?ref=su|internship,job\n"
        "Best Course Deals|https://example.com/deals|courses,online\n"
        "# comment line skip\n"
        "Broken Line without url\n"
    )
    art_job = {"title": "Top 10 Internships for Students 2026", "category": "Internships"}
    blk = monetize.affiliate_block(art_job)
    assert "https://example.com/resume?ref=su" in blk
    assert 'rel="sponsored nofollow noopener"' in blk  # Google compliant
    assert "Affiliate Disclosure" in blk               # FTC compliant
    assert "example.com/deals" not in blk              # keyword mismatch -> excluded

    art_course = {"title": "Top 8 Online Courses 2026", "category": "Education News"}
    blk2 = monetize.affiliate_block(art_course)
    assert "example.com/deals" in blk2 and "resume" not in blk2

    config.AFFILIATE_LINKS = ""
    assert monetize.affiliate_block(art_job) == ""
    print("  2. affiliate_block (match, sponsored rel, disclosure, off-safe) ✔")

    # ---- 3. append_blocks placement ----
    config.TELEGRAM_CHANNEL_URL = "https://t.me/studentup"
    config.AFFILIATE_LINKS = "Deal|https://example.com/d|courses"
    art = {"title": "Best Online Courses 2026", "category": "Education News"}
    out = monetize.append_blocks(HTML_WITH_SCHEMA, art)
    join_idx = out.find("join-alerts")
    deal_idx = out.find("example.com/d")
    schema_idx = out.find('<script type="application/ld+json">')
    assert 0 < join_idx < schema_idx and 0 < deal_idx < schema_idx
    assert out.count("application/ld+json") == 2  # schemas intact at end
    print("  3. append_blocks (blocks before schema, scripts intact) ✔")

    # ---- 4. seasonal + high-CPC ----
    db = Path("/tmp/test_monetize.db")
    db.unlink(missing_ok=True)
    state.init(db)
    # June (6): Online Education seasonal -> 300 runs lo dominance
    from collections import Counter

    picks = Counter(topic_engine.pick_category(db, month=6) for _ in range(300))
    assert picks["Online Education"] > picks["Results"], picks.most_common()
    # High-CPC share: 100 picks lo ~20-45% high-CPC ideas (30% config)
    config.HIGH_CPC_SHARE = 30
    ideas = [topic_engine.pick_listicle_idea(month=6) for _ in range(200)]
    hc = sum(1 for i in ideas if i in topic_engine.HIGH_CPC_LISTICLE_IDEAS)
    assert 25 <= hc <= 90, hc  # 30% expected, sane range
    db.unlink(missing_ok=True)
    print(f"  4. seasonal boost + high-CPC share ({hc}/200 = {hc//2}%) ✔")

    # ---- 5. money-page prioritization ----
    posts = [
        {"title": "SSC Result 2026 Check Here", "link": "l1"},
        {"title": "Top 5 Bank Jobs with Highest Salary 2026", "link": "l2"},
        {"title": "Admit Card Download Guide", "link": "l3"},
        {"title": "Education Loan Options Compared", "link": "l4"},
    ]
    ordered = monetize.prioritize_money_pages(posts)
    titles = [p["title"] for p in ordered]
    assert titles.index("Top 5 Bank Jobs with Highest Salary 2026") < \
        titles.index("SSC Result 2026 Check Here")
    assert titles.index("Education Loan Options Compared") < \
        titles.index("Admit Card Download Guide")
    assert len(ordered) == 4
    print("  5. prioritize_money_pages (money pages first) ✔")

    # ---- 6. ad slots: table position + CLS wrapper + cap ----
    from autoblog import seo as _seo

    html = ("<p>one</p><p>two</p><p>three</p>"
            "<table><tr><td>x</td></tr></table>"
            + "".join(f"<p>para {i}</p>" for i in range(8))
            + "<h2>FAQ</h2><p>faq</p>")
    out = _seo.insert_ad_shortcodes(html, "[ad1]", max_ads=3, cls_safe=True)
    assert out.count("[ad1]") == 3
    assert out.count('min-height:280px') == 3          # CLS wrapper on each
    table_end = html.find("</table>") + len("</table>")
    first_ad = out.find("[ad1]")
    assert first_ad < table_end                          # early slot (after 2nd para)
    out5 = _seo.insert_ad_shortcodes(html, "[ad2]", max_ads=5, cls_safe=False)
    assert out5.count("[ad2]") >= 4 and "min-height" not in out5  # cap 5 + no wrapper
    print("  6. ad slots (early+table+mid+FAQ, CLS wrapper, cap) ✔")

    # ---- 7. --revenue-check smoke ----
    import subprocess

    r = subprocess.run([str(Path(".venv/bin/python")), "run.py", "--revenue-check"],
                       capture_output=True, text=True, timeout=60)
    assert "REVENUE AUDIT" in r.stdout and "SITE-SIDE" in r.stdout
    assert "Bot-side score:" in r.stdout and "POLICY" in r.stdout
    print("  7. --revenue-check command ✔")

    # ---- 8. --doctor health check ----
    r2 = subprocess.run([str(Path(".venv/bin/python")), "run.py", "--doctor"],
                        capture_output=True, text=True, timeout=120)
    assert "DOCTOR" in r2.stdout
    assert "Gemini API" in r2.stdout and "WordPress REST" in r2.stdout
    assert "Storage" in r2.stdout and "Disk" in r2.stdout
    assert "Plan:" in r2.stdout
    assert r2.returncode in (0, 1)  # 1 = missing keys (sandbox) — graceful
    print("  8. --doctor command (structure + graceful) ✔")

    print("ALL REVENUE TESTS PASSED ✔")


if __name__ == "__main__":
    main()
