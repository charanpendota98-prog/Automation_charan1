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

from theme_audit import THEME, _php_files, _strip_php_comments

# top themes ki kavalsina WordPress standard files
REQUIRED_FILES = ("style.css", "index.php", "functions.php", "header.php", "footer.php",
                  "single.php", "page.php", "archive.php", "search.php", "404.php",
                  "theme.json", "screenshot.png", "author.php")
RECOMMENDED_FILES = ("comments.php", "sidebar.php", "languages/studentup.pot", "readme.txt")

# ee modules functions.php lo require avvali (module file undi kaani load avvakapote dead code)
REQUIRED_MODULES = ("options.php", "template.php", "ads.php", "breaking.php", "toc.php",
                    "schema.php", "author-box.php", "pwa.php", "seo-bridge.php",
                    "consent.php", "ads-txt.php", "perf.php", "news-sitemap.php",
                    "qual-filter.php")

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
                                 r"studentup_ad\(|studentup_ui_icon\(|studentup_social_icon\(|"
                                 r"studentup_cmdk_icon\(|implode|join|\.\s*'", line):
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

    # ---------------------------------------------------------------- 8b) STANDARDS PASS 3 (v69)
    # Version parity: style.css header (WP theme version) == STUDENTUP_VERSION (PHP constant)
    ver_css = re.search(r"^Version:\s*(\S+)", style[:2000], re.M)
    ver_php = re.search(r"STUDENTUP_VERSION',\s*'([^']+)'", fn)
    if ver_css and ver_php:
        if ver_css.group(1) != ver_php.group(1):
            errors.append(f"version mismatch: style.css '{ver_css.group(1)}' vs "
                          f"STUDENTUP_VERSION '{ver_php.group(1)}' — WP ki telisedi style.css, "
                          f"cache-busting + child themes + updates daridram")
    else:
        errors.append("version constant leda style.css 'Version:' ledu")

    # readme.txt — Stable tag == version (WP.org + update checks)
    readme = (THEME / "readme.txt")
    if readme.exists():
        rm = readme.read_text(encoding="utf-8")
        st = re.search(r"^Stable tag:\s*(\S+)", rm, re.M)
        if not st:
            warnings.append("readme.txt lo 'Stable tag' ledu")
        elif ver_php and st.group(1) != ver_php.group(1):
            warnings.append(f"readme.txt Stable tag '{st.group(1)}' ≠ version "
                            f"'{ver_php.group(1)}'")

    # Loop templates: post_class() (plugin/CSS compatibility + WP standard)
    for rel, text in texts.items():
        if rel.startswith("inc/") or rel in ("404.php",):
            continue
        if "<article class=" in text[1] and "post_class(" not in text[1]:
            warnings.append(f"{rel}: <article class=...> ki post_class() vaadandi "
                            f"(WP standard + plugin compatibility)")

    # Perf: custom WP_Query calls ki no_found_rows (extra SQL query aapadam)
    for rel, text in texts.items():
        code = text[1]
        for m in re.finditer(r"new WP_Query\(", code):
            tail = code[m.end():m.end() + 900]
            # v72.1: konni queries ki found_posts NIJAM ga kavali (counts — chips/widget/backfill).
            # Aa case lo no_found_rows=false better (count query tho ne) — warning vaddu.
            if "found_posts" in tail:
                continue
            if "'no_found_rows'" not in tail and '"no_found_rows"' not in tail:
                warnings.append(f"{rel}: custom WP_Query ki no_found_rows ledu "
                                f"(shared hosting lo extra SELECT FOUND_ROWS)")

    # Block editor parity (advanced theme standard)
    if "add_theme_support( 'editor-styles' )" not in fn:
        warnings.append("editor-styles support ledu — block editor lo front-end look raadu")
    if "add_theme_support( 'wp-block-styles' )" not in fn:
        info.append("wp-block-styles support ledu (core block default styles)")
    if "add_editor_style(" in fn:
        ed = re.search(r"add_editor_style\(\s*'([^']+)'", fn)
        if ed and not (THEME / ed.group(1)).exists():
            errors.append(f"add_editor_style('{ed.group(1)}') file ledu — editor CSS 404")

    # author archive (E-E-A-T): bio · article count · profile link
    if (THEME / "author.php").exists():
        au = texts.get("author.php", ("", ""))[1]
        for needle, why in (("get_avatar", "avatar (author photo)"),
                            ("count_user_posts", "prachurita vyasala count"),
                            ("description", "author bio"),
                            ("editorial-policy", "editorial policy link (E-E-A-T)")):
            if needle not in au:
                warnings.append(f"author.php lo '{needle}' ledu — {why}")

    # a11y: nav lo aria-current (prastuta page)
    if "aria-current" not in "".join(t[1] for t in texts.values()):
        warnings.append("aria-current ledu — nav lo prastuta page screen readers ki teliyadu")

    # Admin form security: Settings API nonce (`settings_fields`) leda manual `wp_nonce_field`
    if "register_setting(" in fn or "register_setting(" in "".join(t[0] for t in texts.values()):
        opt = texts.get("inc/options.php", ("", ""))[0]
        if opt and "settings_fields(" not in opt and "wp_nonce_field(" not in opt:
            errors.append("inc/options.php: admin form ki nonce ledu "
                          "(settings_fields() leda wp_nonce_field())")
        if opt and "sanitize_callback" not in opt:
            warnings.append("inc/options.php: register_setting ki sanitize_callback ledu")

    # ---------------------------------------------------------------- 9) REVENUE KPI (BA)
    kpi = report.setdefault("kpi", {})
    kpi["ad_positions"] = len(positions)
    kpi["ad_positions_missing"] = missing_pos
    kpi["css_kb"] = round(size_kb, 1)
    kpi["php_files"] = len(texts)
    kpi["preconnect"] = preconn
    return report



# ===========================================================================
# v185 PASS 4 — WEB-QUALITY MATRIX (27 deterministic checks)
# ===========================================================================
# Prathi check okka "world-class website" requirement ni verify chestundi:
# accessibility (WCAG basics) · Core Web Vitals attrs · mobile · print ·
# dark mode (no flash) · SEO/schema hooks · PWA. Static analysis mattrame —
# live PageSpeed numbers ki `tools/cwv_audit.py` + real site kavali.

def _php_plain(text: str) -> str:
    """PHP blocks ni sentinel tho replace — <img> tag regex ki `?>` aapakunda."""
    return re.sub(r"<\?php.*?\?>", " PHP ", text, flags=re.S)


VIEW_TEMPLATES = ("front-page.php", "single.php", "index.php", "page.php",
                  "archive.php", "search.php", "404.php")


def web_quality_checks(report: dict) -> dict:
    """Pass 4: returns KPI dict; appends to report['errors'] / ['warnings']."""
    errors = report.setdefault("errors", [])
    warnings = report.setdefault("warnings", [])
    results: list[tuple[str, str, str]] = []   # (level, name, note)

    def check(name: str, ok: bool, note: str = "") -> bool:
        if ok:
            results.append(("pass", name, note))
        else:
            results.append(("fail", name, note))
            errors.append(f"v185 [{name}] {note or 'fail'}")
        return ok

    def warn(name: str, ok: bool, note: str = "") -> bool:
        if not ok:
            results.append(("warn", name, note))
            warnings.append(f"v185 [{name}] {note}")
        else:
            results.append(("pass", name, note))
        return ok

    def read(rel: str) -> str:
        f = THEME / rel
        return f.read_text(encoding="utf-8") if f.exists() else ""

    css = read("style.css")
    min_css = read("style.min.css")
    header = read("header.php")
    index = read("index.php")

    # ---- 1. single H1 per view template (SEO + screen reader outline) ----
    bad_h1 = []
    for name in VIEW_TEMPLATES:
        text = read(name)
        if not text:
            continue
        if text.count("<h1") != 1:
            bad_h1.append(f"{name}={text.count('<h1')}")
    check("single-h1-per-view", not bad_h1, " · ".join(bad_h1))

    # ---- 2. skip link (keyboard users) ----
    check("skip-link", "skip-link" in header and 'href="#main"' in header,
          "header.php lo skip-link → #main ledu")

    # ---- 3. landmarks (semantic header/main/footer) ----
    landmarks = all(x in header for x in ("<header",))
    landmarks = landmarks and all(f"<main id=\"main\">" in read(n)
                                  for n in ("front-page.php", "single.php", "index.php"))
    landmarks = landmarks and "<footer" in read("footer.php")
    check("landmarks", landmarks, "semantic header/main/footer kaaliga ledu")

    # ---- 4. lang attribute ----
    check("language-attributes", "language_attributes()" in header,
          "html tag ki language_attributes() ledu")

    # ---- 5. color-scheme (native controls follow theme) ----
    check("color-scheme-meta", 'name="color-scheme"' in header,
          "color-scheme meta ledu (scrollbar/form controls light ga untayi)")
    check("color-scheme-css", "color-scheme:light" in css and "color-scheme:dark" in css,
          "style.css lo color-scheme tokens ledu")

    # ---- 6. NO-FLASH dark mode: pre-paint inline script ----
    body_at = header.find("<body")
    script_at = header.find("data-su-theme", body_at)
    header_markup_at = header.find("<header class=")
    noflash = body_at != -1 and script_at != -1 and script_at < header_markup_at
    check("no-flash-dark-mode", noflash,
          "dark readers ki flash — pre-paint theme script body taruvata, header mundu ledu")
    check("theme-pref-key", 'localStorage.getItem("su_theme")' in header,
          "saved preference key (su_theme) inline script lo ledu")

    # ---- 7. reduced motion (vestibular safety) ----
    check("prefers-reduced-motion", "prefers-reduced-motion" in css,
          "reduced-motion block ledu")

    # ---- 8. visible focus ----
    check("focus-visible", ":focus-visible" in css, ":focus-visible styles ledu")

    # ---- 9. outline not globally killed ----
    killed = css.count("outline:none") + css.count("outline: none")
    has_restore = ":focus-visible{outline" in css.replace(" ", "") or \
        "focus-visible" in css
    warn("outline-safety", killed == 0 or has_restore,
         f"outline:none {killed} chotla — focus-visible restore ledu")

    # ---- 10. ARIA live + expanded ----
    check("aria-live", "aria-live" in css or "aria-live" in header
          or "aria-live" in read("footer.php") or "aria-live" in read("inc/smart.php")
          or "aria-live" in "".join(read(f"inc/{n}") for n in ("engage.php", "searchindex.php",
                                                             "quicksummary.php")),
          "aria-live region ledu")
    jss = "".join(read(f"assets/js/{n}") for n in ("studentup.js", "studentup-cmdk.js"))
    check("aria-expanded-toggles", 'aria-expanded' in read("header.php") or
          "aria-expanded" in jss, "toggles ki aria-expanded ledu")

    # ---- 11. target=_blank ⇒ rel noopener ----
    unsafe = 0
    for f in _php_files():
        text = f.read_text(encoding="utf-8")
        for m in re.finditer(r'<a[^>]*target="_blank"[^>]*>', text):
            if "noopener" not in m.group(0):
                unsafe += 1
    check("noopener-external", unsafe == 0, f"{unsafe} blank link(s) ki noopener ledu")

    # ---- 12. images: alt + dimensions on raw <img> ----
    missing_alt, missing_dim = [], []
    for f in _php_files():
        plain = _php_plain(f.read_text(encoding="utf-8"))
        for m in re.finditer(r"<img\b[^>]*>", plain):
            tag, at = m.group(0), m.start()
            if "alt=" not in tag:
                missing_alt.append(f.name)
            if "width=" not in tag or "height=" not in tag:
                ctx = plain[max(0, at - 500):at]
                # Reserved container (min-height / data-su-height) = CLS already
                # handled — ad slot laantivi honest exception.
                if "data-su-height" not in ctx and "min-height" not in ctx:
                    missing_dim.append(f.name)
    check("img-alt", not missing_alt, f"alt ledu: {sorted(set(missing_alt))}")
    warn("img-dimensions", not missing_dim, f"width/height ledu: {sorted(set(missing_dim))}")

    # ---- 13. lazy loading + LCP eager/fetchpriority ----
    tpl = read("inc/template.php")
    check("lazy-images", 'loading="lazy"' in read("inc/engage.php") or
          'loading="lazy"' in read("inc/ads.php"), "lazy loading use ledu")
    lcp_ok = ("fetchpriority" in tpl and "'high'" in tpl) or 'fetchpriority="high"' in tpl
    check("lcp-eager", lcp_ok, "first card ki fetchpriority=high ledu")

    # ---- 14. responsive images via core (srcset auto) ----
    check("responsive-images", "the_post_thumbnail(" in tpl and
          "the_post_thumbnail(" in read("single.php"),
          "card/single lo the_post_thumbnail() ledu (srcset raadu)")

    # ---- 15. LCP preload in head ----
    perf = read("inc/perf.php")
    check("lcp-preload", 'rel="preload" as="image"' in perf and "fetchpriority" in perf,
          "featured image preload ledu")

    # ---- 16. containment / content-visibility (long pages) ----
    contain_hits = len(re.findall(r"contain:\s*(?:content|layout|paint|strict)", css))
    check("css-containment", contain_hits >= 2, f"contain rules {contain_hits} (>=2 kavali)")
    check("content-visibility", "content-visibility" in css,
          "content-visibility ledu (below-fold rendering)")

    # ---- 17. print stylesheet ----
    check("print-styles", "@media print" in css, "@media print ledu")

    # ---- 18. mobile safety: overflow guard + 44px touch targets ----
    check("overflow-guard", "overflow-x" in css, "overflow-x guard ledu")
    check("touch-targets", "44px" in css or "min-height:48px" in css or
          "min-height: 48px" in css, "touch target size token ledu")

    # ---- 19. CSS budget + minified build ----
    raw_kb = len(css.encode("utf-8")) / 1024
    min_kb = len(min_css.encode("utf-8")) / 1024
    check("css-budget", raw_kb <= 135, f"style.css {raw_kb:.1f} KB (>135)")
    check("css-minified-fresh", bool(min_css) and min_kb < raw_kb,
          f"min.css {min_kb:.1f} KB vs {raw_kb:.1f} KB — minify build run cheyyandi")

    # ---- 20. system fonts (no webfont request = fast LCP) ----
    webfont = "@font-face" in css
    warn("system-fonts", not webfont,
         "webfont unte font-display:swap + preload kavali")

    # ---- 21. PWA surfaces ----
    check("pwa-manifest", "manifest" in read("inc/pwa.php"),
          "manifest hook ledu")
    pwa_js = read("assets/js/studentup-pwa.js") + read("inc/webpush.php")
    check("service-worker", "serviceWorker" in pwa_js and "register" in pwa_js,
          "service worker registration ledu")

    # ---- 22. schema hooks (rich results) ----
    schema = read("inc/schema.php") + read("inc/faqschema.php")
    schema_ok = all(k in schema for k in ("JobPosting",)) and "FAQPage" in schema
    check("schema-rich-results", schema_ok, "JobPosting/FAQPage schema ledu")

    report["web_quality"] = {
        "checks": [{"level": lv, "name": n, "note": nt} for lv, n, nt in results],
        "passes": sum(1 for lv, _, _ in results if lv == "pass"),
        "warns": sum(1 for lv, _, _ in results if lv == "warn"),
        "fails": sum(1 for lv, _, _ in results if lv == "fail"),
    }
    return report


def print_web_quality(rep: dict) -> None:
    wq = rep.get("web_quality") or {}
    rows = wq.get("checks") or []
    if not rows:
        return
    icons = {"pass": "✅", "warn": "⚠️ ", "fail": "❌"}
    print("")
    print("  ── PASS 4 · WEB-QUALITY MATRIX (v185 · world-class checklist) ──")
    for row in rows:
        note = f" — {row['note']}" if row["note"] and row["level"] != "pass" else ""
        print(f"   {icons[row['level']]} {row['name']}{note}")
    print(f"   → {wq.get('passes')} pass · {wq.get('warns')} warn · {wq.get('fails')} fail")


def main() -> int:
    import argparse

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import theme_audit

    ap = argparse.ArgumentParser(description="StudentUp deep theme audit (v67)")
    ap.add_argument("--json", default="")
    args = ap.parse_args()
    rep = theme_audit.run()
    web_quality_checks(rep)
    print("=" * 70)
    print("  🔬 DEEP THEME AUDIT (v67+v185) — templates · security · perf · a11y · ads · "
          "standards · web-quality")
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
    print_web_quality(rep)
    print("-" * 70)
    print(f"  errors {len(rep['errors'])} · warnings {len(rep['warnings'])}")
    if args.json:
        Path(args.json).write_text(json.dumps(rep, ensure_ascii=False, indent=2),
                                   encoding="utf-8")
    return 0 if rep["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
