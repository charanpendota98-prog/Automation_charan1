# -*- coding: utf-8 -*-
"""v68: CODE AUDIT — bot (Python) + theme (PHP) lo **nijamaina bugs** vetike tool.

Enduku: static style audits kaadu — ivi runtime lo **crash / silent fail / revenue leak**
chese bugs. Prathi rule ki oka nijamaina failure mode undi:

ERRORS (kacchitam ga crash/fail):
  E1 `config.X` — config.py lo define avvakapote AttributeError
  E2 `<module>.<attr>` — sibling module lo aa function/constant lekapote AttributeError
  E3 bare `except:` — KeyboardInterrupt/SystemExit kuda swallow avutundi
  E4 mutable default arg (`def f(x=[])`) — state leak between calls
  E5 duplicate dict literal key — okati silent ga theesestundi
  E6 `wp.<method>()` — WordPressClient lo lekapote publish crash
  E7 PHP: `get_option('studentup_x')` ki default ledu + output lo vaadutunnaru → empty/notice

WARNINGS (silent fail / hang / revenue leak):
  W1 `except Exception: pass` publish path lo (failure kanipinchadu)
  W2 `os.environ["X"]` direct (KeyError → crash; getenv vaadandi)
  W3 `json.loads` try/except lekunda (corrupt file → crash)
  W4 text file write ki `encoding` ledu (Telugu → mojibake on Windows/hosting)
  W5 subprocess/request ki timeout ledu (bot hang avutundi)
  W6 AdSense markup: `data-ad-layout` (in-article/in-feed) · `data-full-width-responsive`
     · client/slot format · prathi unit ki `adsbygoogle.push({})` (lekapote ad fill avvadu!)
  W7 news sitemap: namespaces + `news:publication_date` format (lekapote Google News reject)

Run: python tools/code_audit.py [--json output/code_audit.json] [--verbose]
Exit 1 = errors unnayi.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOT = ROOT / "autoblog"
THEME = ROOT / "wordpress-theme" / "studentup"

PUBLISH_PATH = ("pipeline.py", "wordpress_client.py", "notifier.py", "main.py",
                "approval_bot.py", "indexing.py")


# --------------------------------------------------------------------- helpers

def _module_defs(path: Path) -> set:
    """Module-level names (functions · classes · constants · imports)."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return set()
    out: set = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.add(node.name)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    out.add(t.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            out.add(node.target.id)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for a in node.names:
                out.add(a.asname or a.name.split(".")[0])
        elif isinstance(node, ast.withitem):
            pass
    # conditional blocks lo assign/def (ast.walk tho paina vastayi, kaani Name target check)
    for node in tree.body:
        if isinstance(node, ast.If):
            for sub in ast.walk(node):
                if isinstance(sub, ast.Assign):
                    for t in sub.targets:
                        if isinstance(t, ast.Name):
                            out.add(t.id)
                elif isinstance(sub, (ast.FunctionDef, ast.ClassDef)):
                    out.add(sub.name)
    return out


def _py_files() -> list:
    files = sorted(BOT.glob("*.py")) + [ROOT / "run.py"]
    files += sorted((ROOT / "tools").glob("*.py"))
    # v74: live-exam package teesesam (cron-only bot) — adi lene file list.
    return [f for f in files if f.exists()]


def _dict_dup_keys(path: Path) -> list:
    """Same dict literal lo duplicate keys (okati silent ga theesestundi)."""
    out = []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return out
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            seen = {}
            for k in node.keys:
                if isinstance(k, ast.Constant) and isinstance(k.value, (str, int)):
                    if k.value in seen:
                        out.append(f"{path.name}:{k.lineno} duplicate dict key {k.value!r}")
                    seen[k.value] = k.lineno
    return out


def _mutable_defaults(path: Path) -> list:
    out = []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return out
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for d in list(node.args.defaults) + [d for d in node.args.kw_defaults if d]:
                if isinstance(d, (ast.List, ast.Dict, ast.Set)):
                    out.append(f"{path.name}:{node.lineno} {node.name}() mutable default arg")
    return out



def _php_arg_list(src: str, fname: str):
    """`fname(...)` arg-list text lu (quote/paren aware) — printf/sprintf placeholder check kosam."""
    out = []
    for m in re.finditer(r"(?<![A-Za-z0-9_])" + re.escape(fname) + r"\s*\(", src):
        i = m.end()
        depth, quote, esc = 1, "", False
        start = i
        while i < len(src) and depth:
            ch = src[i]
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif quote:
                if ch == quote:
                    quote = ""
            elif ch in ("'", '"'):
                quote = ch
            elif ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            i += 1
        out.append(src[start:i - 1])
    return out


def _php_split_args(args: str):
    """Top-level commas tho split."""
    parts, depth, quote, esc, cur = [], 0, "", False, []
    for ch in args:
        if esc:
            esc = False
        elif ch == "\\" and quote:
            esc = True
        elif quote:
            if ch == quote:
                quote = ""
        elif ch in ("'", '"'):
            quote = ch
        elif ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        elif ch == "," and depth == 0:
            parts.append("".join(cur))
            cur = []
            continue
        cur.append(ch)
    parts.append("".join(cur))
    return [p.strip() for p in parts if p.strip()]


def check_php_printf(path: Path, report: dict) -> None:
    """E10 — PHP printf/sprintf placeholder ↔ args mismatch (PHP warning + wrong output)."""
    src = path.read_text(encoding="utf-8")
    for fn in ("printf", "sprintf"):
        for args in _php_arg_list(src, fn):
            parts = _php_split_args(args)
            if len(parts) < 1:
                continue
            fmt_raw = parts[0]
            # WP translation wrappers (_n/__/_x/esc_html__) lo plural forms ki placeholders
            # veru ga untayi — avi skipp cheyyali (false positive ledu)
            if re.search(r"_(?:n|x)?\s*\(|esc_(?:html|attr)__", fmt_raw):
                continue
            if "'" not in fmt_raw and '"' not in fmt_raw:
                continue          # dynamic format (variable) — skip
            pieces = re.findall("'([^']*)'|\"([^\"]*)\"", fmt_raw)
            fmt = "".join(a or b for a, b in pieces)
            if not fmt:
                continue
            specs = re.findall(r"%(?:\d+\$)?[-+ 0#']*\d*(?:\.\d+)?[bcdeEfFgGosuxX%]", fmt)
            specs = [x for x in specs if not x.endswith("%")]
            n_args = len(parts) - 1
            positional = [int(x) for x in re.findall(r"%(\d+)\$", fmt)]
            if positional:
                if max(positional) != n_args:
                    report["warnings"].append(
                        f"E10 {path.name}: positional placeholders max {max(positional)} kaani "
                        f"args {n_args} (printf mismatch)")
            elif len(specs) != n_args:
                report["warnings"].append(
                    f"E10 {path.name}: {fn}() ki {len(specs)} placeholders vs {n_args} args "
                    f"({fmt[:40]!r}) — PHP warning/wrong output")


def check_py_percent_format(path: Path, tree, report: dict) -> None:
    """E11 — Python `"..." % (...)` lo placeholder ↔ arg count mismatch (TypeError)."""
    if tree is None:
        return
    for node in ast.walk(tree):
        if not (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod)):
            continue
        left, right = node.left, node.right
        if not (isinstance(left, ast.Constant) and isinstance(left.value, str)):
            continue
        if not isinstance(right, ast.Tuple):
            continue
        specs = [x for x in re.findall(r"%(?:\([^)]*\))?[-+ 0#]*\d*(?:\.\d+)?[bcdeEfFgGorsxXaiu%]",
                                       left.value) if not x.endswith("%")]
        if len(specs) != len(right.elts):
            report["warnings"].append(
                f"E11 {path.name}:{node.lineno} `%` format lo {len(specs)} placeholders vs "
                f"{len(right.elts)} args (TypeError risk)")


PAYLOAD_META_KEYS = {"ok", "sent", "updated", "reason", "dry_run", "date", "url", "title",
                     "wp_site", "message"}


def check_sync_option_keys(report: dict) -> None:
    """E12 — bot `wp_theme_sync` push keys ↔ theme registered options (typo = data site ki cherudu!).

    Example bug class: bot `breaking_feed` push cheyyadam kaani theme `breaking_json` chudatam →
    site lo update kanipinchadu ('anni aaputhunnayi' lantidi) — ee check adi pattukuntundi.
    """
    sync = BOT / "wp_theme_sync.py"
    opts = THEME / "inc" / "options.php"
    if not (sync.exists() and opts.exists()):
        return
    registered = set(re.findall(r"['\"]([a-z0-9_]+)['\"]\s*=>\s*array\(",
                               opts.read_text(encoding="utf-8")))
    if not registered:
        return
    try:
        tree = ast.parse(sync.read_text(encoding="utf-8"))
    except SyntaxError:
        return
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        keys = [k.value for k in node.keys
                if isinstance(k, ast.Constant) and isinstance(k.value, str)]
        if not keys or not (set(keys) & registered):
            continue                     # payload dict kaadu
        for k in keys:
            if k not in registered and k not in PAYLOAD_META_KEYS:
                report["warnings"].append(
                    f"E12 wp_theme_sync: '{k}' option theme lo register avvaledu — "
                    f"push chesina data site lo kanipinchadu")

# --------------------------------------------------------------------- checks

def audit_python(report: dict) -> dict:
    errors, warnings, info = report["errors"], report["warnings"], report["info"]
    mods = {p.stem: _module_defs(p) for p in BOT.glob("*.py")}
    cfg_defs = mods.get("config", set())

    for path in _py_files():
        src = path.read_text(encoding="utf-8")
        name = path.name
        in_publish = name in PUBLISH_PATH

        # E1 — config.<attr> (AST tho — strings/comments lo false positive ledu)
        try:
            tree = ast.parse(src)
        except SyntaxError:
            tree = None
        if tree is not None:
            for node in ast.walk(tree):
                if (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
                        and node.value.id == "config" and node.attr not in cfg_defs
                        and node.attr not in {"getattr", "setattr", "get"}):
                    errors.append(f"E1 {name}:{node.lineno} config.{node.attr} — "
                                  f"config.py lo ledu (AttributeError)")
        # E2 — sibling module attrs (AST: nijamaina `module.attr` mattrame, strings kaadu)
        if tree is not None:
            imported = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    for a in node.names:
                        imported.add(a.asname or a.name)
            for node in ast.walk(tree):
                if (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
                        and node.value.id in imported and node.value.id in mods
                        and node.value.id != path.stem and node.attr not in mods[node.value.id]):
                    info.append(f"E2 {name}:{node.lineno} {node.value.id}.{node.attr} — "
                                f"{node.value.id}.py lo kanipinchaledu (verify cheyandi)")
        # E3 — bare except
        for i, line in enumerate(src.splitlines(), 1):
            if re.match(r"\s*except\s*:\s*$", line):
                errors.append(f"E3 {name}:{i} bare `except:` — KeyboardInterrupt swallow")
        # E5 — duplicate dict keys
        errors.extend(f"E5 {d}" for d in _dict_dup_keys(path))
        # E11 — %-format arg count
        check_py_percent_format(path, tree, report)
        # E4 — mutable defaults
        errors.extend(f"E4 {d}" for d in _mutable_defaults(path))

        if in_publish:
            # W1 — silent swallow (except Exception: pass) — publish path lo dangerous
            for i, line in enumerate(src.splitlines(), 1):
                if re.match(r"\s*except\s+Exception[^:]*:\s*$", line):
                    nxt = src.splitlines()[i] if i < len(src.splitlines()) else ""
                    if re.match(r"\s*pass\s*$", nxt):
                        warnings.append(f"W1 {name}:{i} except Exception: pass — "
                                        f"failure silent ga poyindi (log cheyandi)")
            # W2 — os.environ[...]
            for m in re.finditer(r"os\.environ\[", src):
                warnings.append(f"W2 {name}: os.environ[...] direct — os.getenv vaadandi")
            # W3 — json.loads without try (same line level heuristic)
            for i, line in enumerate(src.splitlines(), 1):
                if "json.loads(" in line:
                    window = "\n".join(src.splitlines()[max(0, i - 6):i + 2])
                    if "try:" not in window:
                        warnings.append(f"W3 {name}:{i} json.loads() try/except lekunda")
        # W4 + W5 — AST tho precise checks (multi-line calls, zero false positive)
        if tree is not None:
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                fn = node.func
                kws = {k.arg for k in node.keywords if k.arg}
                # W4 — write_text(...) ki encoding
                if isinstance(fn, ast.Attribute) and fn.attr == "write_text" and "encoding" not in kws:
                    warnings.append(f"W4 {name}:{node.lineno} write_text() ki encoding ledu "
                                    f"(Telugu mojibake risk)")
                # W5 — network/subprocess ki timeout
                label = None
                if isinstance(fn, ast.Attribute):
                    if isinstance(fn.value, ast.Name) and fn.value.id == "requests" \
                            and fn.attr in {"get", "post", "put", "delete", "request"}:
                        label = f"requests.{fn.attr}()"
                    elif isinstance(fn.value, ast.Name) and fn.value.id == "subprocess" \
                            and fn.attr in {"run", "check_output", "check_call", "Popen"}:
                        label = f"subprocess.{fn.attr}()"
                elif isinstance(fn, ast.Name) and fn.id in {"urlopen"}:
                    label = "urlopen()"
                if label and "timeout" not in kws:
                    warnings.append(f"W5 {name}:{node.lineno} {label} ki timeout ledu (hang risk)")

        # W5b — wp.<method> existence (E6)
        wp_defs = mods.get("wordpress_client", set())
        for m in re.finditer(r"\bwp\.([a-z_][a-z0-9_]*)\(", src):
            meth = m.group(1)
            if wp_defs and f"_{meth}" not in wp_defs and meth not in wp_defs:
                errors.append(f"E6 {name}: wp.{meth}() — wordpress_client lo ledu "
                              f"(publish crash)")
    return report


def audit_php(report: dict) -> dict:
    errors, warnings, info = report["errors"], report["warnings"], report["info"]
    for php in sorted(THEME.rglob("*.php")):
        check_php_printf(php, report)
    ads = (THEME / "inc" / "ads.php")
    if ads.exists():
        # comments theesesi chudali (lekapote mana comment text loney rules fire avutayi)
        try:
            import sys as _s

            _s.path.insert(0, str(Path(__file__).resolve().parent))
            from theme_audit import _strip_php_comments

            src = _strip_php_comments(ads.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            src = ads.read_text(encoding="utf-8")
        # W6 — AdSense markup correctness (lekapote fill avvadu / policy issue)
        if "adsbygoogle" in src:
            units = len(re.findall(r"class=\"adsbygoogle\"", src)) or len(
                re.findall(r"data-ad-slot", src))
            pushes = len(re.findall(r"(?:adsbygoogle|\)|\])\.push\(\{\}\)", src))
            if units and pushes < units:
                warnings.append(f"W6 ads.php: AdSense units {units} kaani `adsbygoogle.push()` "
                                f"{pushes} mattrame — push lekunda ad fill avvadu!")
            if "data-full-width-responsive" not in src:
                warnings.append("W6 ads.php: `data-full-width-responsive=\"true\"` ledu — "
                                "mobile lo ad full width avvadu (revenue miss)")
            if "in-article" in src and "data-ad-layout" not in src:
                warnings.append("W6 ads.php: in-article slot undi kaani `data-ad-layout` ledu — "
                                "AdSense in-article layout apply avvadu (RPM miss)")
            if 'data-ad-format="in-article"' in src or "data-ad-format=\"in-article\"" in src:
                errors.append("E8 ads.php: `data-ad-format=\"in-article\"` INVALID — AdSense ki "
                              "`data-ad-format=\"fluid\" data-ad-layout=\"in-article\"` kaavali "
                              "(lekapote generic display ga render avutundi)")
            theme_all = "".join(p.read_text(encoding="utf-8") for p in THEME.rglob("*.php"))
            if "crossorigin" not in theme_all:
                warnings.append("W6 ads.php: AdSense loader script ki crossorigin ledu")
            if "ca-pub-" not in src and "data-ad-client" not in src:
                errors.append("E7 ads.php: AdSense client handling ledu")
            for m in re.finditer(r"data-ad-slot=\"<\?php[^>]*?;?\s*\?>\s*([^<\"]*)", src):
                chunk = m.group(1).strip()
                if chunk and not re.match(r"^[0-9]", chunk):
                    info.append(f"W6 ads.php: slot value numeric avvali — '{chunk[:20]}'")
    ns = (THEME / "inc" / "news-sitemap.php")
    if ns.exists():
        src = ns.read_text(encoding="utf-8")
        for needle, why in (("xmlns:news", "news namespace"), ("xmlns:image", "image namespace"),
                            ("news:publication_date", "publication date (48h window)"),
                            ("news:language", "language tag"), ("news:title", "title tag"),
                            ("<lastmod>", "lastmod")):
            if needle not in src:
                warnings.append(f"W7 news-sitemap.php: {needle} ledu — {why} (Google News reject)")
    return report


# --------------------------------------------------------------------- main

def run(verbose: bool = False) -> dict:
    report = {"errors": [], "warnings": [], "info": [],
              "files": len(_py_files())}
    report = audit_python(report)
    report = audit_php(report)
    check_sync_option_keys(report)
    # E9 — .env.example drift (config key ledu → user ki teliyadu / set cheyaledu)
    envf = ROOT / ".env.example"
    cfgf = BOT / "config.py"
    if envf.exists() and cfgf.exists():
        env_src = envf.read_text(encoding="utf-8")
        cfg_src = cfgf.read_text(encoding="utf-8")
        keys = set(re.findall(r'_get\(\s*"([A-Z0-9_]+)"', cfg_src))
        keys |= set(re.findall(r'getenv\(\s*"([A-Z0-9_]+)"', cfg_src))
        for p_ in list(BOT.glob("*.py")) + [ROOT / "run.py"]:
            keys |= set(re.findall(r'os\.getenv\(\s*"([A-Z0-9_]+)"', p_.read_text(encoding="utf-8")))
        for k in sorted(keys):
            if k not in env_src:
                report["warnings"].append(f"E9 .env.example: `{k}` ledu — config lo vaadutunnaru "
                                          f"kaani user ki kanipinchadu (onboarding miss)")

    report["ok"] = not report["errors"]
    report["counts"] = {"errors": len(report["errors"]),
                        "warnings": len(report["warnings"]),
                        "info": len(report["info"])}
    return report


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="StudentUp code audit (bot + theme)")
    ap.add_argument("--json", default="")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args(argv)
    rep = run(args.verbose)
    print("=" * 74)
    print("  🧪 CODE AUDIT (v68) — bot (Python) + theme (PHP) runtime bugs")
    print("=" * 74)
    print(f"  files: {rep['files']} · errors {len(rep['errors'])} · "
          f"warnings {len(rep['warnings'])} · info {len(rep['info'])}")
    for row in rep["errors"]:
        print("  ❌ " + row)
    for row in rep["warnings"]:
        print("  ⚠️  " + row)
    if args.verbose:
        for row in rep["info"]:
            print("  ℹ️  " + row)
    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(json.dumps(rep, ensure_ascii=False, indent=2),
                                   encoding="utf-8")
        print(f"  report: {args.json}")
    print("-" * 74)
    print(f"  {'✅ CLEAN' if rep['ok'] else '⛔ FIX CHEYANDI'} · errors {len(rep['errors'])} · "
          f"warnings {len(rep['warnings'])}")
    print("=" * 74)
    return 0 if rep["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
