# -*- coding: utf-8 -*-
"""v66: THEME AUDIT — static checks (php-parser syntax kaadu, idi deeper).

Enduku: `php_lint.js` syntax mattrame chustundi. Kaani render time lo:
  · theme lo piliche `studentup_xxx()` function define avvakapote → **fatal error**
  · `get_option('studentup_x')` ki admin page lo field lekapote → **setting pani cheyyadu**
  · escaping lekunda echo → XSS
  · `wp_body_open()` / `wp_head()` / `wp_footer()` / `body_class()` lekapote →
    plugin/ads/theme compatibility + SEO issues
  Ee tool ivi anni static ga pattukuntundi → build + guardian lo gate.

Run: python tools/theme_audit.py [--json output/theme_audit.json]
Exit 1 = errors unnayi (build fail avvali).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THEME = ROOT / "wordpress-theme" / "studentup"

# WP core / PHP builtins / plugin functions — ee list lo unna vi theme lo undakapoyina ok
WP_CORE = {
    "get_header", "get_footer", "get_sidebar", "get_template_part", "wp_head",
    "wp_footer", "wp_body_open", "body_class", "post_class", "language_attributes",
    "bloginfo", "home_url", "site_url", "admin_url", "get_permalink", "the_permalink",
    "get_the_title", "the_title", "the_content", "the_excerpt", "get_the_excerpt",
    "esc_html", "esc_attr", "esc_url", "esc_textarea", "wp_kses_post", "wp_kses",
    "wp_json_encode", "wp_strip_all_tags", "sanitize_title", "sanitize_key",
    "sanitize_text_field", "wp_unslash", "is_email", "wp_kses_post_deep",
    "wp_get_attachment_image_url", "get_theme_mod", "has_custom_logo", "get_site_icon_url",
    "has_site_icon", "wp_count_posts", "get_category_by_slug", "get_category_link",
    "get_the_category", "get_the_date", "get_the_modified_date", "get_the_time",
    "get_the_modified_time", "get_permalink", "get_the_ID", "get_post_meta",
    "get_option", "update_option", "delete_option", "register_setting", "settings_fields",
    "settings_errors", "add_settings_error", "add_menu_page", "add_action", "add_filter",
    "register_post_meta", "register_rest_route", "apply_filters", "add_query_arg",
    "wp_enqueue_style", "wp_enqueue_script", "wp_localize_script", "wp_nav_menu",
    "has_nav_menu", "wp_list_pluck", "wp_reset_postdata", "wp_trim_words",
    "get_search_form", "get_search_query", "is_admin", "is_feed", "is_singular",
    "is_page", "is_category", "is_search", "is_404", "is_front_page", "is_home",
    "is_active_sidebar", "dynamic_sidebar", "register_sidebar", "add_theme_support",
    "load_theme_textdomain", "register_nav_menus", "add_image_size", "current_user_can",
    "is_user_logged_in", "wp_kses_data", "esc_js", "esc_url_raw", "get_bloginfo",
    "wp_get_document_title", "get_locale", "wp_link_pages", "edit_post_link",
    "paginate_links", "get_query_var", "set_query_var", "get_next_posts_link",
    "get_previous_posts_link", "the_post", "have_posts", "get_the_post_thumbnail",
    "the_post_thumbnail", "the_post_thumbnail_url", "has_post_thumbnail",
    "get_the_post_thumbnail_url", "wp_get_attachment_image_src", "wp_get_attachment_url",
    "get_post", "get_posts", "get_page_by_path", "wp_count_terms", "get_terms",
    "is_wp_error", "wp_remote_get", "wp_remote_retrieve_body", "wp_date", "human_time_diff",
    "checked", "selected", "disabled", "submit_button", "wp_nonce_field",
    "wp_verify_nonce", "sanitize_email", "wp_mail", "nocache_headers", "wp_die",
    "wp_safe_redirect", "wp_redirect", "get_the_author_meta", "get_avatar",
    "get_the_author", "the_author", "get_author_posts_url", "esc_attr__", "__",
    "esc_html__", "esc_html_e", "esc_attr_e", "wp_reset_query", "is_paged",
    "get_queried_object", "get_queried_object_id", "wp_title", "wp_get_theme",
    "get_stylesheet_uri", "get_template_directory_uri", "get_template_directory",
    "get_stylesheet_directory", "esc_html_x", "wp_doing_ajax", "wp_doing_cron",
    "is_customize_preview", "current_time", "mysql2date", "wp_parse_url",
    "wp_make_content_images_responsive", "wp_get_global_settings", "wp_theme_get_element_class_name",
}


def _php_files() -> list:
    return sorted(THEME.rglob("*.php"))


def _tpl_raw(name: str) -> str:
    """Template file raw text (lekapote '')."""
    p = THEME / name
    return p.read_text(encoding="utf-8") if p.exists() else ""


def _strip_php_comments(text: str) -> str:
    """PHP comments theeseyadam — **string-aware** (URLs lo `//` comment kaadu!).

    v67 fix: puratana version line-wise `//` cut cheyyadam valla `https://...` URLs
    comments la theesesaru → audit ki code kanipinchaledu (false negatives +
    false positives). Ippudu quote state track chestunnamu.
    """
    out = []
    i, n = 0, len(text)
    in_block, quote = False, ""
    while i < n:
        ch = text[i]
        if in_block:
            if text.startswith("*/", i):
                in_block = False
                i += 2
                continue
            i += 1
            continue
        if quote:
            out.append(ch)
            if ch == "\\":
                if i + 1 < n:
                    out.append(text[i + 1])
                    i += 2
                    continue
            elif ch == quote:
                quote = ""
            i += 1
            continue
        if text.startswith("/*", i):
            in_block = True
            i += 2
            continue
        if text.startswith("//", i):
            j = text.find("\n", i)
            i = n if j == -1 else j
            continue
        if ch in ("'", '"'):
            quote = ch
            out.append(ch)
            i += 1
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def collect(report: dict) -> dict:
    errors: list = report["errors"]
    warnings: list = report["warnings"]
    info: list = report["info"]

    defined: set = set()
    called: dict = {}
    options_read: set = set()
    options_declared: set = set()
    h1_files: list = []
    hooks: dict = {}

    for path in _php_files():
        raw = path.read_text(encoding="utf-8")
        rel = path.relative_to(THEME).as_posix()
        text = _strip_php_comments(raw)

        for m in re.finditer(r"function\s+(studentup_[a-z0-9_]+)\s*\(", text):
            defined.add(m.group(1))
        for m in re.finditer(r"\b([a-z_][a-z0-9_]*)\s*\(", text):
            name = m.group(1)
            if name.startswith("studentup_"):
                called.setdefault(name, set()).add(rel)
        for m in re.finditer(r"get_option\(\s*'(studentup_[a-z0-9_]+)'", text):
            options_read.add(m.group(1))
        for m in re.finditer(r"studentup_opt\(\s*'([a-z0-9_]+)'", text):
            options_read.add("studentup_" + m.group(1))
        for m in re.finditer(r"'(studentup_[a-z0-9_]+)'\s*=>", text):
            pass
        for m in re.finditer(r"register_setting\(\s*'[^']+',\s*'(studentup_[a-z0-9_]+)'", text):
            options_declared.add(m.group(1))
        # options.php fields array → 'key' => array(...)
        for m in re.finditer(r"'([a-z0-9_]+)'\s*=>\s*array\(\s*'[^']*',\s*'(text|check|textarea)'", text):
            options_declared.add("studentup_" + m.group(1))
        # hooks
        for m in re.finditer(r"add_action\(\s*'([a-z0-9_]+)'", text):
            hooks.setdefault(m.group(1), set()).add(rel)
        for m in re.finditer(r"add_filter\(\s*'([a-z0-9_]+)'", text):
            hooks.setdefault(m.group(1), set()).add(rel)

        # per-file checks
        if re.search(r"<\?php", raw):
            if raw.count("<h1") > 1 and rel not in ("front-page.php", "index.php"):
                warnings.append(f"{rel}: {raw.count('<h1')} <h1> tags (okka page ki okkate)")
            if re.search(r"the_content\(\)", text) and "esc_" not in text.lower():
                pass  # the_content WP-filtered — ok
            if re.search(r"<\?php\s+echo\s+\$", text):
                errors.append(f"{rel}: escape cheyyani `echo $` (XSS risk)")
            if re.search(r"echo\s+\$_(GET|POST|REQUEST)", text):
                errors.append(f"{rel}: $_GET/$_POST direct echo (XSS)")
    report["defined"] = sorted(defined)
    report["options_read"] = sorted(options_read)

    # 1) undefined function calls
    for name, files in sorted(called.items()):
        if name not in defined and name not in WP_CORE:
            errors.append(f"undefined function: {name}() — {', '.join(sorted(files))}")
    # 2) options read but not declared in the settings page
    #    (dynamic prefix reads: 'studentup_adsense_slot_' + $place → declared variants
    #     unte saripothundi)
    for opt in sorted(options_read):
        if not options_declared or opt in options_declared:
            continue
        if opt.endswith("_"):
            variants = [d for d in options_declared if d.startswith(opt)]
            if variants:
                info.append(f"dynamic option '{opt}*' — {len(variants)} variants declared")
                continue
        warnings.append(f"option '{opt}' read — admin page lo field ledu "
                        f"(StudentUp Settings lo add cheyandi)")
    # 2b) declared-but-never-read options (info) — admin lo field undi kaani code
    #     eppudu chadavadu → user set chesi "pani cheyyatledu" anukuntadu
    dyn_prefixes = [o for o in options_read if o.endswith("_")]
    for opt in sorted(options_declared - options_read):
        if opt.endswith("_") or any(opt.startswith(p) for p in dyn_prefixes):
            continue   # dynamic read (get_option( 'prefix_' . $x )) — alive
        info.append(f"option '{opt}' declared kaani eppudu read avvatledu "
                    f"(admin field dead undi)")

    # 3) unused functions (info)
    for name in sorted(defined):
        if name not in called and not name.endswith("_fallback"):
            info.append(f"unused function: {name}()")

    # 4) critical template hooks
    def _tpl(name: str) -> str:
        p = THEME / name
        return _strip_php_comments(p.read_text(encoding="utf-8")) if p.exists() else ""

    header, footer = _tpl("header.php"), _tpl("footer.php")
    for needle, why in (("wp_head()", "plugins/ads/SEO chaala pani cheyyavu"),
                        ("body_class()", "theme/plugin CSS hooks fail"),
                        ("language_attributes()", "a11y/SEO"),
                        ("wp_body_open()", "plugins (ads/analytics) inject cheyyalevu")):
        if needle not in header:
            errors.append(f"header.php: {needle} ledu — {why}")
    if "wp_footer()" not in footer:
        errors.append("footer.php: wp_footer() ledu — ads/scripts load avvavu")
    if not re.search(r"<main[^>]*id=\"main\"", _tpl("index.php") + header):
        warnings.append("`<main id=\"main\">` ledu — skip-link target missing")

    # 5) ads / monetization readiness
    ads = _tpl("inc/ads.php")
    for key in ("adsbygoogle", "reserved", "lazy", "is_page", "su-ad",
                "in_article_ad", "the_content", "max_ads"):
        if key not in ads:
            warnings.append(f"inc/ads.php: '{key}' ledu — ad revenue/CLS check cheyandi")
    if "sticky_ad" not in footer and "sticky_ad" not in _tpl("inc/options.php"):
        warnings.append("sticky/anchor ad option ledu — mobile lo highest-CTR slot miss")
    if "ads.txt" not in _tpl("inc/ads.txt.php") + _tpl("inc/ads-txt.php") + \
            "".join(p.read_text(encoding="utf-8") for p in _php_files() if "ads" in p.name):
        warnings.append("ads.txt serving ledu (direct ad demand padipothundi)")
    if "consent" not in "".join(p.read_text(encoding="utf-8").lower() for p in _php_files()):
        warnings.append("consent mode (GDPR/CMP) ledu — EEA/UK ads block avutayi")

    # 6) SEO surface
    single = _tpl("single.php")
    for needle in ("studentup_breadcrumbs", "studentup_author_box"):
        if needle not in single:
            warnings.append(f"single.php: {needle}() ledu (E-E-A-T/breadcrumb)")
    report["hooks"] = {k: sorted(v) for k, v in hooks.items()}
    return report


def run() -> dict:
    report = {"errors": [], "warnings": [], "info": [], "theme_files": len(_php_files())}
    report = collect(report)
    # v67: DEEP pass (templates · security · perf · a11y · SEO · ads · standards)
    try:
        import sys as _s

        _s.path.insert(0, str(Path(__file__).resolve().parent))
        import theme_audit_deep

        report = theme_audit_deep.deep_checks(report)
    except Exception as exc:  # noqa: BLE001 — deep pass fail aithe kuda basic audit nadavali
        report["warnings"].append(f"deep audit skip ({type(exc).__name__}: {exc})")
    report["ok"] = not report["errors"]
    return report


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="StudentUp theme static audit")
    ap.add_argument("--json", default="")
    ap.add_argument("--verbose", action="store_true",
                    help="info rows kuda chupinchu (unused fns · dead options)")
    args = ap.parse_args(argv)
    rep = run()
    print("=" * 70)
    print("  🔍 THEME AUDIT (v66) — static checks (functions · options · hooks · ads · SEO)")
    print("=" * 70)
    print(f"  files: {rep['theme_files']} · functions: {len(rep['defined'])} · "
          f"options read: {len(rep['options_read'])}")
    for row in rep["errors"]:
        print("  ❌ " + row)
    for row in rep["warnings"]:
        print("  ⚠️  " + row)
    if args.verbose:
        for row in rep.get("info", []):
            print("  ℹ️  " + row)
    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(json.dumps(rep, ensure_ascii=False, indent=2),
                                   encoding="utf-8")
        print(f"  report: {args.json}")
    print("-" * 70)
    print(f"  errors {len(rep['errors'])} · warnings {len(rep['warnings'])}"
          f" → {'✅ OK' if rep['ok'] else '⛔ FIX CHEYANDI'}")
    print("=" * 70)
    return 0 if rep["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
