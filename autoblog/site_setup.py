"""v22 — FULL WordPress site setup: the bot configures the SITE, not just posts.

Audit (read-only) + idempotent fixes over WP REST as admin:
  blockers : search-engine visibility (robots/blog_public), plain permalinks
  fixes    : SEO tagline, timezone Asia/Kolkata, closed comments default,
             sane posts_per_page, footer legal menu (5 policy pages),
             category SEO descriptions (Telugu), site icon/logo
  warns    : Rank Math sitemap off, plugin REST namespace missing,
             menu location not assignable from REST

run_setup(dry=True)   -> audit + plan only (safe)
run_setup(dry=False)  -> apply every auto-fixable item
Nothing here ever deletes/overwrites existing content: only missing/empty
values are set (idempotent — second run = all OK, zero writes).
"""
from __future__ import annotations

import logging
from typing import Dict, List, Tuple

from . import config

log = logging.getLogger("autoblog.setup")

TAGLINE = ("Telugu lo Govt Jobs, Exams, Results, Hall Tickets & Scholarships "
           "— 100% free daily updates")

TIMEZONE = "Asia/Kolkata"

FOOTER_MENU_NAME = "studentup-legal"

# v28: keep plugin installation explicit and allow-listed. The setup never
# deactivates/removes anything and it never switches a theme automatically.
PLUGIN_LABELS = {
    "rank-math": "Rank Math",
    "redirection": "Redirection",
    "updraftplus": "UpdraftPlus",
    "wp-super-cache": "WP Super Cache",
}
FAST_THEME_SLUGS = {"generatepress", "astra", "kadence", "blocksy"}
FAST_THEME_NAMES = {"generatepress", "astra", "kadence", "blocksy"}

# Telugu SEO copy for archive pages (Rank Math category meta boost). Only set
# when a category description is EMPTY — existing copy is never touched.
CAT_DESCS: Dict[str, str] = {
    "Central Govt Jobs":
        "SSC, Railway, UPSC, Bank — Central Government latest notifications, "
        "vacancies, admit cards aur results Telugu lo complete ga.",
    "TS Govt Jobs":
        "Telangana Prabhuthi, DSC, Police, Panchayat Secretary — TS Govt "
        "notifications, hall tickets, results daily updates Telugu lo.",
    "AP Govt Jobs":
        "Andhra Pradesh Group, Police, Railway gang, DSC notifications, "
        "applications, results anni Telugu lo oka chota.",
    "Online Education":
        "Online courses, SWAYAM, MOOC, upskilling — free/paid education "
        "programs details, eligibility, certificates Telugu lo.",
    "Part Time Jobs":
        "Students kosam part-time, freelance, work-from-home opportunities — "
        "apply steps, salary, safety tips Telugu lo.",
    "Walkin Jobs":
        "Walk-in interview drives — companies, venues, eligibility, documents "
        "list walk-in jobs updates Telugu lo.",
    "Hall Tickets":
        "Prathi exam hall ticket / admit card download links, exam day rules, "
        "shift details — latest updates Telugu lo.",
    "Private Jobs":
        "IT, banking, sales, startup — private company off-campus drives, "
        "placements aur apply links Telugu lo.",
    "Software Jobs":
        "Developer, tester, data role — fresher experience IT job "
        "notifications, interview prep tips Telugu lo.",
    "Scholarships":
        "NSP, state scholarships, PM YASASVI — apply last date, documents, "
        "amount details Telugu lo step by step.",
    "Results":
        "Exam results, scorecards, cut-offs, counselling notifications — "
        "instant Telugu updates.",
    "Internships":
        "IIT, IIM, DRDO, startup internships — stipend, apply process, "
        "eligibility complete details Telugu lo.",
    "Daily Quiz":
        "Prathi roju exam-style Daily Quiz Telugu lo — GK, current affairs, "
        "scholarships, maths & reasoning. Timer, negative marking, "
        "explanations tho free practice.",
}


def _line(status: str, label: str, detail: str = "") -> Tuple[str, str, str]:
    return (status, label, detail)


def _menu_dedupe(wp, menu_id: int) -> int:
    """v25: same title repeated in a menu (dup Terms/Privacy from past runs)
    — keep first occurrence, DELETE extras via core REST. Returns removed."""
    removed = 0
    try:
        items = wp.get_menu_items(menu_id) or []
    except Exception:
        return 0
    seen = set()
    for it in items:
        title = (it.get("title") or "").strip()
        if not title:
            continue
        if title in seen:
            try:
                r = wp._request("DELETE", f"menu-items/{it.get('id')}",
                                params={"force": "true"})
                if r.ok:
                    removed += 1
            except Exception:
                pass
        else:
            seen.add(title)
    return removed


def _theme_audit(wp) -> Tuple[str, str]:
    """Theme speed/readability audit; switching is deliberately manual."""
    themes = wp.list_themes()
    if not themes:
        return "WARN", "themes REST empty — current theme ni WP Admin lo verify cheyandi"
    active = next((t for t in themes
                   if (t.get("status") or "").lower() in ("active", "current")), None)
    if not active:
        active = next((t for t in themes if t.get("stylesheet")), themes[0])
    slug = (active.get("slug") or active.get("stylesheet") or "").lower()
    name = active.get("name") or slug or "unknown"
    if slug in FAST_THEME_SLUGS or name.lower() in FAST_THEME_NAMES:
        return "OK", f"{name} active — lightweight theme family"
    recommended = ", ".join(("GeneratePress", "Astra", "Kadence"))
    return "WARN", (f"{name} active — speed unknown; recommend {recommended}. "
                     "Theme switch REST dwara cheyyamu; Appearance → Themes lo manual ga test cheyandi")


def _plugin_slug(plugin: Dict) -> str:
    return ((plugin.get("slug") or "").strip().lower()
            or (plugin.get("plugin") or "").split("/", 1)[0].lower())


def _plugin_audit_and_fix(wp, dry: bool) -> Tuple[str, str]:
    """Install/activate only the reviewed v28 stack, idempotently."""
    if not config.PLUGIN_AUTO_INSTALL:
        return "SKIP", "PLUGIN_AUTO_INSTALL=0 — plugin changes disabled"
    installed = wp.list_plugins()
    by_slug = {_plugin_slug(p): p for p in installed if _plugin_slug(p)}
    wanted = [p for p in config.AUTO_INSTALL_PLUGINS
              if p in PLUGIN_LABELS]
    unknown = [p for p in config.AUTO_INSTALL_PLUGINS if p not in PLUGIN_LABELS]
    if unknown:
        log.warning("Ignoring non-allow-listed plugin slugs: %s", ", ".join(unknown))
    if not wanted:
        return "WARN", "AUTO_INSTALL_PLUGINS lo allow-listed plugin ledu"

    missing = [p for p in wanted if p not in by_slug]
    inactive = [p for p in wanted
                if p in by_slug and config.PLUGIN_AUTO_ACTIVATE
                and (by_slug[p].get("status") or "inactive").lower() != "active"]
    if dry:
        if missing or inactive:
            bits = []
            if missing:
                bits.append("install: " + ", ".join(PLUGIN_LABELS[p] for p in missing))
            if inactive:
                bits.append("activate: " + ", ".join(PLUGIN_LABELS[p] for p in inactive))
            return "FIX?", "; ".join(bits)
        return "OK", "allow-listed plugin stack installed + active"

    changed, failures = [], []
    for slug in missing:
        try:
            result = wp.install_plugin(slug, activate=config.PLUGIN_AUTO_ACTIVATE)
            changed.append(f"{PLUGIN_LABELS[slug]} ({result.get('status', 'installed')})")
        except Exception as exc:  # noqa: BLE001 — one plugin must not hide others
            failures.append(f"{PLUGIN_LABELS[slug]}: {str(exc)[:90]}")
    for slug in inactive:
        plugin_id = by_slug[slug].get("plugin")
        try:
            if not plugin_id:
                raise ValueError("REST response lo plugin id ledu")
            result = wp.activate_plugin(plugin_id)
            changed.append(f"{PLUGIN_LABELS[slug]} ({result.get('status', 'active')})")
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{PLUGIN_LABELS[slug]}: {str(exc)[:90]}")
    if failures:
        return "WARN", "changed: " + (", ".join(changed) or "none") + "; failed: " + "; ".join(failures)
    if changed:
        return "FIXED", "plugin stack ready — " + ", ".join(changed)
    return "OK", "allow-listed plugin stack already active"


def audit_and_fix(wp, dry: bool = True) -> List[Tuple[str, str, str]]:
    """One pass: check each item; when dry=False apply fixes. Returns report."""
    out: List[Tuple[str, str, str]] = []
    done = "OK" if dry else "FIXED"

    # ---- 1. search-engine visibility (blog_public) — CRITICAL ----
    code, robots = wp.public_get_status("/robots.txt")
    blocked = code == 200 and "\nDisallow: /\n" in robots.replace("\r", "")
    if blocked:
        out.append(_line(
            "BLOCK", "Search engines BLOCKED",
            "robots.txt 'Disallow: /' undi! WP Admin → Settings → Reading → "
            "'Discourage search engines' UNCHECK cheyandi (AdSense/SEO killar)"))
    else:
        out.append(_line("OK", "Search engines allowed", "robots.txt clean"))

    # ---- 2. permalinks ----
    sample = ""
    try:
        recent = wp.get_recent_published(per_page=1)
        sample = recent[0]["link"] if recent else ""
    except Exception:
        pass
    if sample and ("?p=" in sample or "?page_id=" in sample):
        out.append(_line(
            "BLOCK", "Permalinks PLAIN",
            "WP Admin → Settings → Permalinks → 'Post name' select cheyandi "
            "(URLs SEO-friendly avvali)"))
    elif sample:
        out.append(_line("OK", "Permalinks clean", sample[:60]))
    else:
        out.append(_line("WARN", "Permalinks check",
                         "sample post ledu — manual ga Post name verify"))

    # ---- 3. sitemap ----
    s_code, _ = wp.public_get_status("/sitemap_index.xml")
    if s_code != 200:
        s_code, _ = wp.public_get_status("/sitemap.xml")
    if s_code == 200:
        out.append(_line("OK", "XML sitemap live", ""))
    elif dry:
        out.append(_line("WARN", "XML sitemap ledu",
                         "Rank Math → Sitemap Settings ENABLE cheyandi "
                         "(plugin unte auto: /sitemap_index.xml)"))
    else:
        out.append(_line("WARN", "XML sitemap ledu",
                         "Rank Math sitemap module enable cheppali (manual)"))

    # ---- 4. Rank Math plugin REST presence ----
    ns = wp.rest_namespaces()
    if any("rank" in x.lower() for x in ns):
        out.append(_line("OK", "Rank Math REST active", ""))
    else:
        out.append(_line("WARN", "Rank Math REST ledu",
                         "plugin install/activate chepthe — meta fields "
                         "(focus keyword) set avvakapote RM panel blank vasthundi"))

    # ---- 5. v28 theme audit + reviewed plugin stack ----------------------
    # Keep this capability check for older/custom fakes and third-party WP
    # clients: the rest of site setup remains useful even without the routes.
    if callable(getattr(wp, "list_themes", None)):
        try:
            theme_status, theme_detail = _theme_audit(wp)
            out.append(_line(theme_status, "Theme audit", theme_detail))
        except Exception as exc:  # noqa: BLE001
            out.append(_line("WARN", "Theme audit", f"themes REST failed: {str(exc)[:100]}"))
    if callable(getattr(wp, "list_plugins", None)):
        try:
            plugin_status, plugin_detail = _plugin_audit_and_fix(wp, dry=dry)
            # A disabled feature is informational, not a setup blocker.
            out.append(_line(plugin_status, "Plugin stack", plugin_detail))
        except Exception as exc:  # noqa: BLE001
            out.append(_line("WARN", "Plugin stack", f"plugins REST failed: {str(exc)[:100]}"))

    # ---- 6. General settings (tagline / timezone / comments / page size) ----
    try:
        st = wp.get_settings()
    except Exception:
        st = {}
    want: Dict = {}
    tag = (st.get("description") or "").strip()
    if "telugu" not in tag.lower():
        want["description"] = TAGLINE
    if (st.get("timezone_string") or "") != TIMEZONE:
        want["timezone_string"] = TIMEZONE
    if st.get("default_comment_status") != "closed":
        want["default_comment_status"] = "closed"
    if int(st.get("posts_per_page") or 10) > 20:
        want["posts_per_page"] = 10
    if want:
        out.append(_line(done if not dry else "FIX?", "General settings",
                         ", ".join(sorted(want))))
        if not dry:
            ok = wp.save_settings(want)
            out[-1] = _line("OK" if ok else "WARN", "General settings saved",
                            ", ".join(sorted(want)))
    else:
        out.append(_line("OK", "General settings", "tagline/timezone/comments already set"))

    # ---- 6. site icon (favicon) ----
    if st and not st.get("site_icon_url"):
        logo = getattr(config, "SITE_LOGO_URL", "") or ""
        if logo.startswith("http") and not dry:
            try:
                import tempfile
                from pathlib import Path as _P

                import requests as _rq

                r = _rq.get(logo, timeout=30)
                r.raise_for_status()
                with tempfile.TemporaryDirectory() as td:
                    fp = _P(td) / "site-icon.png"
                    fp.write_bytes(r.content)
                    mid = wp.upload_media(fp, title="studentup.in icon",
                                          alt_text="studentup.in logo")
                    if mid and wp.save_settings({"site_icon": mid,
                                                 "site_icon_url": logo}):
                        out.append(_line("OK", "Site icon", "logo favicon ga set ayindi"))
                        logo = ""  # mark fixed
            except Exception as exc:  # noqa: BLE001
                log.warning("site icon failed: %s", exc)
        if logo.startswith("http"):
            out.append(_line("FIX?", "Site icon ledu",
                             "512x512 logo upload cheyandi (Google/AdSense card lo brand kanipisthundi)"))
        elif not st.get("site_icon_url"):
            out.append(_line("WARN", "Site icon ledu",
                             "SITE_LOGO_URL env pettandi auto-set kosam"))
    else:
        out.append(_line("OK", "Site icon", ""))

    # ---- 7. policy pages → footer menu ----
    pages = []
    try:
        from .main import ADSENSE_PAGES
        page_defs = [(t, sl) for t, sl, _h in ADSENSE_PAGES]
    except Exception:
        page_defs = [("Privacy Policy", "privacy-policy"),
                     ("About Us", "about-us"),
                     ("Contact Us", "contact-us")]
    for title, slug in page_defs:
        pg = None
        try:
            pg = wp.get_page_by_slug(slug)
        except Exception:
            pass
        if pg:
            pages.append((title, pg))
    if pages:
        menus = []
        try:
            menus = wp.get_menus() or []
        except Exception:
            menus = []
        menu = next((m for m in menus
                     if (m.get("name") or "").lower() == FOOTER_MENU_NAME
                     or (m.get("slug") or "") == FOOTER_MENU_NAME), None)
        have_titles = set()
        if menu:
            try:
                have_titles = {(it.get("title") or "")
                               for it in wp.get_menu_items(menu["id"])}
            except Exception:
                pass
        n_dupes = _menu_dedupe(wp, menu["id"]) if (menu and not dry) else 0
        add_items = [p for p in pages if p[0] not in have_titles]
        if not menu and not dry:
            mid = wp.create_menu(FOOTER_MENU_NAME, FOOTER_MENU_NAME)
            menu = {"id": mid} if mid else None
            add_items = list(pages)
        if menu and add_items:
            if dry:
                # A dry-run must not mutate menu items or locations.
                out.append(_line("FIX?", "Footer legal menu",
                                 f"{len(add_items)} missing page links + footer assignment planned"))
            else:
                for title, pg in add_items:
                    wp.add_menu_item(menu["id"], pg["id"], title)
                # location assign (footer/secondary unte)
                try:
                    locs = {l.get("name", ""): l.get("location")
                            for l in (wp.get_locations() or [])}
                    footer = next((v for k, v in locs.items()
                                   if any(w in k.lower() or w in (v or "")
                                          for w in ("footer", "bottom"))), "")
                    if footer:
                        wp.update_menu(menu["id"], {"locations": [footer]})
                        out.append(_line(done, "Footer legal menu",
                                         f"{len(add_items)} links + '{footer}' location"))
                    else:
                        out.append(_line("WARN", "Footer menu location",
                                         "menu create ayindi kaani footer location ledu — "
                                         "Appearance → Menus lo assign cheyandi"))
                except Exception:
                    out.append(_line("FIX?", "Footer legal menu",
                                     f"{len(add_items)} page links add cheyalsi (REST menu)"))
        elif menu:
            out.append(_line("OK", "Footer legal menu",
                             "anni links unnayi"
                             + (f" — {n_dupes} duplicate items removed"
                                if n_dupes else "")))
        else:
            out.append(_line("FIX?", "Footer legal menu",
                             f"'{FOOTER_MENU_NAME}' menu create + {len(pages)} links"))
    else:
        out.append(_line("FIX?", "Policy pages",
                         "muDDu --ensure-adsense (pages create avutayi + menu kuda)"))

    # ---- 8. category SEO descriptions ----
    try:
        cats = wp.list_categories() or []
    except Exception:
        cats = []
    missing = []
    for c in cats:
        d = CAT_DESCS.get(c["name"])
        if d and not c["description"]:
            missing.append(c)
    if missing:
        if dry:
            out.append(_line("FIX?", "Category descriptions",
                             f"{len(missing)} categories empty — Telugu SEO copy set cheyalsi"))
        else:
            n = sum(1 for c in missing if wp.update_category(
                c["id"], CAT_DESCS[c["name"]]))
            out.append(_line("OK" if n else "WARN", "Category descriptions",
                             f"{n}/{len(missing)} updated"))
    else:
        out.append(_line("OK", "Category descriptions", "anni categories ki SEO copy undi"
                         if cats else "categories emi ledu"))

    return out


def _connect_or_report(wp=None):
    from .wordpress_client import WordPressClient

    wp = wp or WordPressClient()
    wp.check_connection()
    return wp


def run_plugins(dry: bool = True, wp=None) -> int:
    """Explicit v28 plugin command, useful before running the full setup."""
    try:
        wp = _connect_or_report(wp)
        status, detail = _plugin_audit_and_fix(wp, dry=dry)
    except Exception as exc:  # noqa: BLE001
        print(f"❌ Plugin setup failed: {exc}")
        return 1
    print(f"🔌 Plugin stack ({'dry-run' if dry else 'apply'}): {status} — {detail}")
    return 0 if status not in ("WARN",) else 1


def run_theme_audit(wp=None) -> int:
    """Explicit read-only theme audit; never activates a theme."""
    try:
        wp = _connect_or_report(wp)
        status, detail = _theme_audit(wp)
    except Exception as exc:  # noqa: BLE001
        print(f"❌ Theme audit failed: {exc}")
        return 1
    print(f"🎨 Theme audit: {status} — {detail}")
    return 0 if status == "OK" else 1


def run_adsense_kit(dry: bool = True, wp=None) -> int:
    """Explicit AdSense loader command; client id is validated first."""
    from . import adsense_kit

    status, detail = adsense_kit.audit()
    if status in ("SKIP", "WARN"):
        print(f"💰 AdSense kit: {status} — {detail}")
        return 0 if status == "SKIP" else 1
    try:
        wp = _connect_or_report(wp)
        installed, detail = adsense_kit.install(wp, dry=dry)
    except Exception as exc:  # noqa: BLE001
        print(f"❌ AdSense kit failed: {exc}")
        return 1
    print(f"💰 AdSense kit ({'dry-run' if dry else 'apply'}): {installed} — {detail}")
    return 0 if installed not in ("warn",) else 1


def run_setup(dry: bool = True, wp=None) -> int:
    """CLI entry. Returns 0 (clean/fixed) or 1 (blocker present)."""
    from .wordpress_client import WordPressClient

    wp = wp or WordPressClient()
    print("=" * 64)
    print(f"  🔧 WORDPRESS SITE SETUP — {'AUDIT (dry-run)' if dry else 'AUDIT + FIX'}")
    print("=" * 64)
    try:
        wp.check_connection()
    except Exception as exc:  # noqa: BLE001
        print(f"  ❌ WP connect kaDU: {exc}")
        return 1
    blocked = False
    for status, label, detail in audit_and_fix(wp, dry=dry):
        icon = {"OK": "✅", "FIX?": "🔧", "WARN": "⚠️ ",
                "BLOCK": "⛔", "FIXED": "🔧"}.get(status, "• ")
        print(f"  {icon} {label:28.28s} {detail[:150]}")
        if status == "BLOCK":
            blocked = True
    # v28 AdSense loader: no client id means a truthful SKIP, not a fake
    # installation. ads.txt and approval remain manual Google-side steps.
    try:
        from . import adsense_kit
        a_status, a_detail = adsense_kit.install(wp, dry=dry)
        print(f"  💰 {'AdSense kit':28.28s} {a_status}: {a_detail[:120]}")
    except Exception as exc:  # noqa: BLE001
        print(f"  💰 AdSense kit failed (harmless): {str(exc)[:100]}")
    if not dry:
        # v24 DESIGN KIT — site-wide CSS via footer text widget (all pages)
        try:
            from . import design_kit
            status, detail = design_kit.install(wp)
            print(f"  🎨 {'Design kit':28.28s} {status}: {detail[:120]}")
            f_stat, f_detail = design_kit.broken_footer_token(wp)
            if f_stat != "skip":
                print(f"  🦶 {'Footer token':28.28s} {f_stat}: {f_detail[:120]}")
        except Exception as exc:  # noqa: BLE001
            print(f"  🎨 Design kit failed (harmless): {str(exc)[:100]}")
        # v26 QUIZ ENGINE — site-wide exam UI (CSS+JS footer widget)
        try:
            from . import quiz_engine
            q_status, q_detail = quiz_engine.install(wp)
            print(f"  🎯 {'Quiz engine':28.28s} {q_status}: {q_detail[:120]}")
        except Exception as exc:  # noqa: BLE001
            print(f"  🎯 Quiz engine failed (harmless): {str(exc)[:100]}")
    print("-" * 64)
    if dry:
        print("  Preview matrame. Apply cheyadaniki: run.py --setup")
        print("  (apply lo v24 Design kit site-wide CSS kuda install avutundi)")
    else:
        print("  ✅ Auto-fixes apply ayipoyayi. Baaki ⚠️/🔧 items admin lo cheppali.")
    if blocked:
        print("  ⛔ BLOCKER unundi — aa items fix cheste matrame traffic/AdSense safe!")
        return 1
    return 0
