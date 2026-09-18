# -*- coding: utf-8 -*-
"""v67: DEEP THEME AUDIT (expert/BA level) — pass 2.

`theme_audit.py` basic checks (undefined functions · options · hooks). Idi **deeper**:
templates · security/nonces · escaping patterns · performance · accessibility ·
SEO/noindex · ads/policy spacing · i18n · module wiring · WordPress theme standards.

Prathi rule: **nijamaina** problem matrame flag chestundi (false positive ledu ane target).
Exit code logic theme_audit lo ne — errors unte build fail.

Run: python tools/theme_audit_deep.py        (standalone)
     python tools/theme_audit.py             (basic + deep, ee module ni call chestundi)
"""
from __future__ import annotations

import json
import re
import struct
import sys
from pathlib import Path

from theme_audit import THEME, WP_CORE, _php_files, _strip_php_comments, _tpl_raw  # noqa: F401

# top themes ki kavalsina WordPress standard files
REQUIRED_FILES = ("style.css", "index.php", "functions.php", "header.php", "footer.php",
                  "single.php", "page.php", "archive.php", "search.php", "404.php",
                  "theme.json", "screenshot.png")
RECOMMENDED_FILES = ("comments.php", "sidebar.php", "languages/studentup.pot", "readme.txt")

# ee modules functions.php lo require avvali (module file undi kaani load avvakapote dead code)
REQUIRED_MODULES = ("options.php", "template.php", "ads.php", "breaking.php", "toc.php",
                    "schema.php", "author-box.php", "pwa.php", "seo-bridge.php",
                    "consent.php", "ads-txt.php", "perf.php", "news-sitemap.php")

DANGEROUS = {
    "eval(": "eval — remote code execution risk",
    "base64_decode(": "base64_decode — obfuscated code risk",
    "shell_exec(": "shell_exec — RCE",
    "passthru(": "passthru — RCE",
    "system(": "system() — RCE",
    "extract(": "extract() — variable injection",
    "create_function(": "create_function — deprecated + unsafe",
    "file_put_contents(": "file_put_contents — hosting lo write risk (disable)",
    "unserialize(": "unserialize — object injection (json_decode vaadandi)",
}

A11Y_NEEDS = (
    (r'<html[^>]*\blang=', "html tag ki lang attribute (a11y + SEO)"),
    (r'<button[^>]*type=["\']button', "<button> ki type=\"button\" (form submit avvakudadu)"),
    (r'aria-label', "interactive elements ki aria-label"),
)

PERF_NEEDS = (
    (r"wp_enqueue_script\([^)]*,\s*array\([^)]*'jquery'", "script ki jquery dependency (slow)"),
)

AD_POSITIONS = ("leaderboard", "in-feed", "mid", "sidebar", "below-content", "anchor")


def _files_text() -> dict:
    out = {}
    for path in _php_files():
        out[path.relative_to(THEME).as_posix()] = (path.read_text(encoding="utf-8"),
                                                  _strip_php_comments(path.read_text(encoding="utf-8")))
    return out


def deep_checks(report: dict) -> dict:
    errors, warnings, info = report["errors"], report["warnings"], report["info"]
    texts = _files_text()
    style = (THEME / "style.css").read_text(encoding="utf-8")
    style_code = re.sub(r"/\*.*?\*/", "", style, flags=re.S)
    theme_json = (THEME / "theme.json")
    js_path = THEME / "assets" / "js" / "studentup.js"
    js = js_path.read_text(encoding="utf-8") if js_path.exists() else ""
    fn = texts.get("functions.php", ("", ""))[0]

    # ---------------------------------------------------------------- 1) TEMPLATES
    for rel in REQUIRED_FILES:
        if not (THEME / rel).exists():
            errors.append(f"template missing: {rel} — WordPress theme standard ki kaavali")
    for rel in RECOMMENDED_FILES:
        if not (THEME / rel).exists():
            warnings.append(f"recommended file ledu: {rel} (top-theme standard)")
    header = style[:2000]
    for needle, why in (("Theme Name:", "theme name"), ("Version:", "version"),
                        ("Text Domain:", "i18n text domain"), ("License:", "license"),
                        ("Requires at least:", "WP requirement"), ("Requires PHP:", "PHP requirement")):
        if needle not in header:
            warnings.append(f"style.css header lo '{needle}' ledu — {why}")
    if theme_json.exists():
        try:
            tj = json.loads(theme_json.read_text(encoding="utf-8"))
            if int(tj.get("version", 0)) < 2:
                warnings.append("theme.json version 2+ (WP 5.9+ settings) vaadandi")
            if not tj.get("settings", {}).get("layout"):
                warnings.append("theme.json lo layout settings ledu (content width) — "
                                "wide/full alignment raadu")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"theme.json invalid JSON: {type(exc).__name__}")
    else:
        errors.append("theme.json ledu (block editor styles raavu)")

    # 404/search: noindex + search form (thin page policy)
    for rel in ("404.php", "search.php", "archive.php"):
        raw, code = texts.get(rel, ("", ""))
        if raw and "get_search_form" not in raw and rel != "archive.php":
            warnings.append(f"{rel}: search form ledu (user ki exit path ivvali)")
    if "wp_robots" not in "".join(code for _, code in texts.values()):
        warnings.append("search/404 ki noindex filter (wp_robots) ledu — thin pages "
                        "index ayyi crawl budget thintayi")

    # ---------------------------------------------------------------- 2) SECURITY
    for rel, (raw, code) in texts.items():
        if "ABSPATH" not in raw:
            errors.append(f"{rel}: ABSPATH guard ledu (direct access protect)")
        for needle, why in DANGEROUS.items():
            if needle in code:
                errors.append(f"{rel}: {why}")
        if "wp_remote_get(" not in code and re.search(r"file_get_contents\(\s*['\"]https?://", code):
            errors.append(f"{rel}: file_get_contents(remote) — wp_remote_get vaadandi "
                          f"(hosting lo allow_url_fopen off untundi)")
    opts = texts.get("inc/options.php", ("", ""))[1]
    # Settings API (settings_fields + register_setting) lo nonce ni WP core verify chestundi.
    # Manual $_POST handling unte mattrame nonce manual ga kaavali.
    manual_post = re.search(r"\$_POST\s*\[", opts) and "settings_fields(" not in opts
    if manual_post and "check_admin_referer" not in opts and "wp_verify_nonce" not in opts:
        errors.append("inc/options.php: manual $_POST handling — nonce verify ledu (CSRF risk)")
    if "settings_fields(" not in opts and "wp_nonce_field" not in opts:
        errors.append("inc/options.php: admin form lo nonce ledu (settings_fields/wp_nonce_field)")
    for m in re.finditer(r"register_rest_route\([^;]+", opts, flags=re.S):
        if "permission_callback" not in m.group(0):
            errors.append("inc/options.php: REST route ki permission_callback ledu (open API!)")
    for m in re.finditer(r"register_setting\(([^;]+)\)", opts, flags=re.S):
        args = m.group(1)
        if args.count(",") < 2:
            warnings.append("register_setting() ki sanitize_callback ledu — option "
                            "sanitize avvadu (unsafe save)")
    adm = [rel for rel, (_r, c) in texts.items()
           if "add_menu_page(" in c or "register_setting(" in c]
    for rel in adm:
        code = texts[rel][1]
        if "current_user_can" not in code:
            errors.append(f"{rel}: admin action ki current_user_can check ledu")

    # ---------------------------------------------------------------- 3) ESCAPING
    for rel, (_raw, code) in texts.items():
        for line in code.splitlines():
            if re.search(r"\becho\b", line) and "$" in line:
                if not re.search(r"esc_(html|attr|url|js|textarea)|\(int\)|\(float\)|"
                                 r"wp_json_encode|number_format|wp_kses|absint|intval|"
                                 r"studentup_ad\(|implode|join|\.\s*'", line):
                    warnings.append(f"{rel}: echo lo variable escape avvaledu → esc_html() "
                                    f"wrap cheyandi: {line.strip()[:60]}")

    # ---------------------------------------------------------------- 4) PERFORMANCE
    if "wp_enqueue_script" in fn and "true" not in fn:
        warnings.append("functions.php: script footer lo load avvatledu (blocking)")
    if "$ver" not in fn and "filemtime" not in fn:
        info.append("functions.php: enqueue version — theme version vaadutunnaru (ok)")
    preconn = sum(1 for host in ("adsbygoogle", "googletagmanager", "google-analytics",
                                 "fonts.gstatic") if host in fn or host in texts.get("inc/perf.php", ("", ""))[1])
    if preconn < 2:
        warnings.append("preconnect hints takkuva (adsense/analytics) — 3rd-party latency")
    if "@import" in style_code:
        errors.append("style.css lo @import — render blocking (enqueue vaadandi)")
    size_kb = len(style.encode("utf-8")) / 1024
    if size_kb > 120:
        warnings.append(f"style.css {size_kb:.0f} KB — 120 KB kanna peddadi (split cheyandi)")
    if 'display=swap' not in style + fn and "fonts.googleapis" in style + fn:
        warnings.append("Google Fonts ki display=swap ledu (FOIT)")

    # ---------------------------------------------------------------- 5) A11Y
    header_raw = texts.get("header.php", ("", ""))[0]
    footer_raw = texts.get("footer.php", ("", ""))[0]
    all_raw = "\n".join(r for r, _ in texts.values())
    if not re.search(r'class=["\'][^"\']*skip-link', all_raw):
        warnings.append("skip-link ledu (keyboard users ki main content ki jump)")
    for pattern, why in A11Y_NEEDS:
        if pattern.startswith(r'<html'):
            if "language_attributes()" in all_raw or re.search(pattern, all_raw):
                continue
            warnings.append(f"{why} ledu")
            continue
        if not re.search(pattern, all_raw):
            warnings.append(f"{why} ledu")
    if "focus-visible" not in style_code:
        warnings.append("style.css lo :focus-visible ledu (keyboard focus kanipinchadu)")
    navs = re.findall(r"<nav[^>]*>", all_raw)
    if navs and not all('aria-label' in n or 'aria-labelledby' in n for n in navs):
        warnings.append("`<nav>` ki aria-label ledu (screen reader)")
    if "sr-only" not in style_code and "screen-reader-text" not in style_code:
        warnings.append("screen-reader-only CSS ledu (a11y labels)")
    buttons = re.findall(r"<button(?![^>]*type=)[^>]*>", all_raw)
    if buttons:
        warnings.append(f"{len(buttons)} <button> ki type attribute ledu")

    # ---------------------------------------------------------------- 6) SEO surface
    h1_files = []
    for rel, (raw, _code) in texts.items():
        if rel.endswith(".php") and raw.count("<h1") > 1:
            h1_files.append(rel)
    if h1_files:
        warnings.append("multi-H1 templates: " + ", ".join(h1_files))
    if "wp_head()" in header_raw and "canonical" not in all_raw.lower():
        info.append("canonical WP core/Rank Math nunchi vastundi (ok)")
    if "og:image" not in all_raw and "og:image" not in texts.get("inc/schema.php", ("", ""))[0]:
        info.append("og:image — Rank Math handle chestundi (verify cheyandi)")

    # ---------------------------------------------------------------- 7) ADS / MONEY
    ads_code = texts.get("inc/ads.php", ("", ""))[1]
    positions = [p for p in AD_POSITIONS if p in ads_code]
    missing_pos = [p for p in AD_POSITIONS if p not in ads_code]
    if missing_pos:
        warnings.append("ad placements miss: " + ", ".join(missing_pos)
                        + " — ee slots revenue miss (anni highest-CTR slots ivvali)")
    for css_needle, why in ((".su-ad{", "ad block ki styling"),
                            ("margin", "ad spacing (policy: content nunchi gap)")):
        if css_needle not in style_code.replace(" ", ""):
            warnings.append(f"style.css: {why} ledu (.su-ad rules)")
    if "data-ad-client" not in ads_code and "adsbygoogle" not in ads_code:
        errors.append("inc/ads.php: AdSense unit code ledu (revenue path)")
    if "adsense_auto" not in texts.get("inc/options.php", ("", ""))[0]:
        warnings.append("options lo adsense_auto toggle ledu")
    if "ad_refresh" in ads_code.lower() or "setInterval" in ads_code:
        errors.append("inc/ads.php: ad refresh code — AdSense policy violation risk!")

    # ---------------------------------------------------------------- 8) MODULES / STANDARDS
    for mod in REQUIRED_MODULES:
        if not (THEME / "inc" / mod).exists():
            errors.append(f"inc/{mod} missing (module)")
        elif f"inc/{mod}" not in fn:
            errors.append(f"inc/{mod} undi kaani functions.php lo require ledu (dead module)")
    # dynamic: inc/ lo unna prathi file require avvali (kotha module marchipovadam appudu pattukuntundi)
    for path in sorted((THEME / "inc").glob("*.php")):
        rel = f"inc/{path.name}"
        if rel not in fn:
            errors.append(f"{rel} undi kaani functions.php lo require ledu (dead module)")
    if "load_theme_textdomain" not in fn:
        info.append("load_theme_textdomain ledu — strings English/POT ki map avvavu (ok for now)")
    if "add_theme_support( 'automatic-feed-links' )" not in fn:
        warnings.append("automatic-feed-links support ledu (RSS auto-discovery)")
    if "add_theme_support( 'title-tag' )" not in fn:
        errors.append("title-tag support ledu — <title> WP manage cheyyadu")
    if "add_theme_support( 'post-thumbnails' )" not in fn:
        errors.append("post-thumbnails support ledu — featured image raadu")
    if "add_theme_support( 'html5'" not in fn:
        warnings.append("html5 support ledu (search form/comment list markup)")
    if "add_theme_support( 'responsive-embeds'" not in fn:
        warnings.append("responsive-embeds support ledu (YouTube embeds mobile)")
    if "add_theme_support( 'align-wide'" not in fn:
        info.append("align-wide ledu (block editor wide images)")
    if "register_nav_menus" not in fn:
        errors.append("register_nav_menus ledu (menu locations)")
    if not js:
        warnings.append("assets/js/studentup.js ledu (progress/copy/sticky ad JS)")

    # screenshot.png — WP standard 1200x900 (theme directory lo crop avvakunda)
    shot = THEME / "screenshot.png"
    if shot.exists():
        try:
            raw = shot.read_bytes()[:33]
            if raw[:8] == b"\x89PNG\r\n\x1a\n":
                w, h = struct.unpack(">II", raw[16:24])
                if (w, h) != (1200, 900):
                    warnings.append(f"screenshot.png {w}x{h} — WordPress standard 1200x900 "
                                    f"(lekapote directory lo crop avutundi)")
            else:
                warnings.append("screenshot.png PNG format kaadu (JPG ok kaani PNG standard)")
        except Exception as exc:  # noqa: BLE001
            info.append(f"screenshot check skip ({type(exc).__name__})")

    # ---------------------------------------------------------------- 9) REVENUE KPI (BA)
    kpi = report.setdefault("kpi", {})
    kpi["ad_positions"] = len(positions)
    kpi["ad_positions_missing"] = missing_pos
    kpi["css_kb"] = round(size_kb, 1)
    kpi["php_files"] = len(texts)
    kpi["preconnect"] = preconn
    return report


def main() -> int:
    import argparse

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import theme_audit

    ap = argparse.ArgumentParser(description="StudentUp deep theme audit (v67)")
    ap.add_argument("--json", default="")
    args = ap.parse_args()
    rep = theme_audit.run()
    print("=" * 70)
    print("  🔬 DEEP THEME AUDIT (v67) — templates · security · perf · a11y · ads · standards")
    print("=" * 70)
    for row in rep["errors"]:
        print("  ❌ " + row)
    for row in rep["warnings"]:
        print("  ⚠️  " + row)
    for row in rep["info"]:
        print("  ℹ️  " + row)
    kpi = rep.get("kpi", {})
    print(f"  KPI: php {kpi.get('php_files')} · ad positions {kpi.get('ad_positions')}/6 · "
          f"css {kpi.get('css_kb')} KB · preconnect {kpi.get('preconnect')}")
    print("-" * 70)
    print(f"  errors {len(rep['errors'])} · warnings {len(rep['warnings'])}")
    if args.json:
        Path(args.json).write_text(json.dumps(rep, ensure_ascii=False, indent=2),
                                   encoding="utf-8")
    return 0 if rep["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
