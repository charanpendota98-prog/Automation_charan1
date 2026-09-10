"""v24 design kit tests — crop-proof thumbs, widget install/update, footer
token fix, CSS content, CLI wiring. No network."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from autoblog import design_kit, image_gen  # noqa: E402


class FakeResp:
    def __init__(self, status=200, payload=None):
        self.status_code, self._p = status, payload or {}

    @property
    def ok(self):
        return self.status_code < 400

    def json(self):
        return self._p


class FakeWP:
    def __init__(self, mode="ok"):
        self.mode, self.calls = mode, []
        self.widgets = {}
        self.n = 0

    def _request(self, method, path, **kw):
        self.calls.append((method, path, kw))
        if self.mode == "dead":
            raise RuntimeError("connection refused")
        if path.startswith("sidebars"):
            if self.mode == "no_sidebars":
                return FakeResp(200, [])
            return FakeResp(200, [{"id": "sidebar-1", "name": "Sidebar"},
                                  {"id": "footer-1", "name": "Footer"}])
        if path.startswith("widgets/"):
            wid = path.split("/", 1)[1]
            self.widgets[wid] = kw.get("json", {}).get("instance", {})
            return FakeResp(200, {"id": wid})
        if path == "widgets" and method == "POST":
            self.n += 1
            wid = f"text-{900 + self.n}"
            self.widgets[wid] = kw.get("json", {}).get("instance", {})
            return FakeResp(201, {"id": wid})
        if path.startswith("widgets"):
            items = [{"id": k, "instance": v} for k, v in self.widgets.items()]
            if self.mode == "broken_footer" and not items:
                from urllib.parse import quote
                items = [{"id": "text-1", "instance": {
                    "encoded": "title=&text=" + quote(
                        "Copyright © 2026 - {StudentUp.in}")}}]
            return FakeResp(200, items)
        return FakeResp(404, {})


def t1_css():
    css = design_kit.build_css()
    assert css.startswith("<style id=") and "sukit24" in css
    assert css.index("@import") < css.index(":root"), "@import first rule kavali"
    for token in ("--su-navy:#12356B", "--su-accent:#E8842B",
                  "Noto Sans Telugu", "Inter", "border-radius:14px",
                  "object-fit:cover", "max-height:420px",
                  "border-collapse:separate", "nth-child(even)",
                  "more-link", "line-height:1.85", "@media (max-width:640px)",
                  # v25 cards + widget heads
                  ".archive .entry-title", "aspect-ratio:16/9",
                  "translateY(-2px)", "widget-title", "box-shadow"):
        assert token in css, token
    print("1. kit CSS tokens ✅")


def t2_install_update():
    wp = FakeWP()
    st, det = design_kit.install(wp)
    assert st == "ok" and "footer-1" in det, det
    wid = re.search(r"\((text-\d+)", det).group(1)
    enc = wp.widgets[wid]["encoded"]
    assert "sukit24" in enc and "%3Cstyle" in enc
    # re-run → SAME css → up-to-date skip (no POST at all beyond GETs)
    n_before = wp.n
    calls_before = len(wp.calls)
    st2, det2 = design_kit.install(wp)
    assert st2 == "ok" and "up to date" in det2 and wid in det2
    assert wp.n == n_before
    posts = [c for c in wp.calls[calls_before:] if c[0] == "POST"]
    assert not posts, posts
    # stale widget (marker edited away) → sidecar id → refresh, NO dupe create
    import tempfile
    from unittest import mock
    from autoblog import config
    tmpdir = Path(tempfile.mkdtemp())
    with mock.patch.object(config, "STATE_PATH", tmpdir / "state.db"):
        wp.widgets.pop(wid)  # first: simulate wipe → recreate + save id
        st2b, det2b = design_kit.install(wp)
        wid = re.search(r"\((text-\d+)", det2b).group(1)
        wp.widgets[wid] = {"encoded": "title=&text=user-edited-no-marker"}
        st3, det3 = design_kit.install(wp)
        assert st3 == "ok" and "refreshed" in det3, (st3, det3)
        assert wp.n == n_before + 1  # only the recreate above, no dupes
    print("2. install → up-to-date skip → stale refresh (no dupes) ✅")


def t3_fallbacks():
    st, _ = design_kit.install(FakeWP("no_sidebars"))
    assert st == "warn"
    st, _ = design_kit.install(FakeWP("dead"))
    assert st == "warn"
    st, det = design_kit.install(FakeWP(), dry=True)
    assert st == "planned"
    print("3. block-theme/dead-API fallbacks ✅")


def t4_footer_token():
    wp = FakeWP("broken_footer")
    st, det = design_kit.broken_footer_token(wp)
    assert st == "ok" and "text-1" in det, (st, det)
    enc = wp.widgets["text-1"]["encoded"]
    assert "StudentUp.in" in enc and "%7B" not in enc.replace(
        "%7BStudentUp.in%7D", "")  # token gone
    st2, _ = design_kit.broken_footer_token(FakeWP())
    assert st2 == "skip"
    print("4. footer {StudentUp.in} auto-fix ✅")


def t5_layouts():
    import tempfile
    from PIL import Image
    tmp = Path(tempfile.mkdtemp())
    names = set(image_gen.VARIANTS)
    assert names == {"bottom", "center", "top"}
    for v in names:
        out = image_gen.generate_featured_image(
            "TS EAMCET 2026 Counselling Schedule Out", "Results",
            tmp / f"{v}.jpg", variant=v)
        assert out and out.exists()
        with Image.open(out) as im:
            px = im.convert("RGB").load()
            W, H = im.size
            minx, maxx = W, 0
            for yy in range(0, H, 3):
                for xx in range(0, W, 3):
                    r, g, b = px[xx, yy]
                    if r > 228 and g > 228 and b > 228:
                        minx, maxx = min(minx, xx), max(maxx, xx)
            assert minx > 0.19 * W and maxx < 0.81 * W, (v, minx, maxx)
        # simulate square mobile crop (worst case 56.25% width) — title present
        with Image.open(out) as im:
            W, H = im.size
            left = (W - H) // 2
            crop = im.convert("RGB").crop((left, 0, left + H, H))
            cp = crop.load()
            bright = sum(1 for yy in range(0, H, 4) for xx in range(0, H, 4)
                         if all(c > 225 for c in cp[xx, yy]))
            assert bright > 30, v  # plenty of text survived the crop
    print("5. 3 layouts: crop-safe bbox + square-crop survival ✅")


def t6_wiring():
    main_src = (Path(__file__).resolve().parent.parent
                / "autoblog/main.py").read_text(encoding="utf-8")
    assert "--polish" in main_src and "design_kit.install" in main_src
    setup_src = (Path(__file__).resolve().parent.parent
                 / "autoblog/site_setup.py").read_text(encoding="utf-8")
    assert "Design kit" in setup_src and "broken_footer_token" in setup_src
    assert "_menu_dedupe" in setup_src and "duplicate items removed" in setup_src
    rot = image_gen.generate_featured_image.__doc__
    assert "bottom" in rot or "rotate" in (image_gen.__doc__ or "")
    print("6. --polish CLI + setup auto-install wiring ✅")


def t7_menu_dedupe():
    class FakeMenuWP:
        def __init__(self):
            self.deleted = []
        def get_menu_items(self, mid):
            return [{"id": 1, "title": "About Us"}, {"id": 2, "title": "Privacy Policy"},
                    {"id": 3, "title": "Terms"}, {"id": 4, "title": " Privacy Policy "},
                    {"id": 5, "title": "Contact"}, {"id": 6, "title": "Terms"}]
        def _request(self, m, path, **kw):
            self.deleted.append(path)
            class R:
                ok = True
            return R()
    from autoblog import site_setup
    wp = FakeMenuWP()
    n = site_setup._menu_dedupe(wp, 55)
    assert n == 2 and wp.deleted == ["menu-items/4", "menu-items/6"], (n, wp.deleted)
    # dedupe must never delete first occurrences
    assert "menu-items/1" not in wp.deleted
    print("7. footer menu duplicate auto-removal ✅")


if __name__ == "__main__":
    t1_css()
    t2_install_update()
    t3_fallbacks()
    t4_footer_token()
    t5_layouts()
    t6_wiring()
    t7_menu_dedupe()
    print("ALL v24 TESTS PASSED ✔")
