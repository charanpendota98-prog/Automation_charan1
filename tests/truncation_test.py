"""v17.1 truncation fix tests: maxOutputTokens config, thinkingConfig off
for 2.5 models, finishReason MAX_TOKENS detection, adaptive LENGTH OVERRIDE
retry on truncated JSON.

Live bug (09-09-2026): Telugu article JSON at char 16800 — "Unterminated
string" — because 8192 token cap + 2.5-flash thinking ate the output budget.
All retries re-sent the same prompt → same cut. Fixed: 32k tokens (2.5),
thinking OFF, MAX_TOKENS detect, crisp retry with LENGTH OVERRIDE.
"""

import json
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from autoblog import config, gemini_client as gc  # noqa: E402

GOOD = {
    "title": "NLC Apprentice Recruitment 2026 – Apply Online Telugu lo",
    "slug": "nlc-apprentice-2026",
    "meta_description": "NLC Apprentice 2026 notification complete details, "
                        "eligibility, salary — Telugu lo.",
    "content_html": "<h2>Overview</h2><p>NLC India apprentice 2026 details...</p>",
    "tags": ["NLC", "Apprentice", "2026"],
    "category": "Central Govt Jobs",
    "focus_keyword": "NLC Apprentice 2026",
}
GOOD_TEXT = json.dumps(GOOD)


class FakeResp:
    def __init__(self, data, code=200):
        self._data = data
        self.status_code = code
        self.text = json.dumps(data)

    def json(self):
        return self._data


def _resp(text, finish="STOP"):
    return FakeResp({"candidates": [
        {"content": {"parts": [{"text": text}]}, "finishReason": finish}]})


def main():
    print("v17.1 TRUNCATION FIX TESTS:")

    # ---- 1. payload: 32k tokens + thinkingConfig 2.5 ki matrame ----
    captured = {}
    real_requests = gc.requests

    def fake_post(url, params=None, json=None, timeout=None, **kw):
        captured["payload"] = json
        captured["url"] = url
        return _resp(GOOD_TEXT)

    def fake_get(url, params=None, timeout=None, **kw):
        raise AssertionError("only post expected")

    gc.requests = types.SimpleNamespace(post=fake_post, get=fake_get)
    try:
        out = gc._call_model("gemini-2.5-flash", "test prompt")
        assert json.loads(out)["title"] == GOOD["title"]
        g = captured["payload"]["generationConfig"]
        assert g["maxOutputTokens"] == 32768, g
        assert g["thinkingConfig"] == {"thinkingBudget": 0}, g
        assert captured["url"].endswith("gemini-2.5-flash:generateContent")
        # fallback model (2.0): no thinking field + 8192 clamp (400 kaavudu)
        gc._call_model("gemini-2.0-flash", "p")
        g2 = captured["payload"]["generationConfig"]
        assert "thinkingConfig" not in g2, g2
        assert g2["maxOutputTokens"] == 8192, g2
        print("  1. payload (32k + thinking OFF for 2.5; 2.0 clamped 8192) ✔")

        # ---- 2. finishReason MAX_TOKENS -> TRUNCATED detect ----
        def post_max(url, params=None, json=None, timeout=None, **kw):
            return _resp('{"title": "cut', finish="MAX_TOKENS")

        gc.requests = types.SimpleNamespace(post=post_max, get=fake_get)
        try:
            gc._call_model("gemini-2.5-flash", "p")
            raise AssertionError("TRUNCATED error raise avvali")
        except gc.GeminiError as e:
            assert str(e).startswith("TRUNCATED"), e
        print("  2. MAX_TOKENS finishReason -> TRUNCATED detect ✔")
    finally:
        gc.requests = real_requests

    # ---- 3. adaptive retry: truncate -> LENGTH OVERRIDE -> success ----
    calls = []
    real_call, real_models, real_time = gc._call_model, gc._models, gc.time

    def fake_call(model, prompt, key=None):
        calls.append(prompt)
        if len(calls) == 1:
            return '{"title": "NLC Apprentice 2026 – Telugu article cut at cha'
        return GOOD_TEXT

    gc._call_model = fake_call
    gc._models = lambda: ["gemini-2.5-flash"]
    gc.time = types.SimpleNamespace(sleep=lambda s: None)
    try:
        art = gc._generate_with_retries("write article",
                                       category="Central Govt Jobs")
        assert art["title"] == GOOD["title"]
        assert len(calls) == 2, len(calls)
        assert "LENGTH OVERRIDE" in calls[1], "retry prompt lo override ledu"
        assert "LENGTH OVERRIDE" not in calls[0]
        print("  3. adaptive retry (truncate -> override -> success) ✔")

        # ---- 4. TRUNCATED error path kuda override trigger ----
        calls.clear()

        def fake_call2(model, prompt, key=None):
            calls.append(prompt)
            if len(calls) == 1:
                raise gc.GeminiError("TRUNCATED:MAX_TOKENS (output cut)")
            return GOOD_TEXT

        gc._call_model = fake_call2
        art2 = gc._generate_with_retries("write article 2", category="")
        assert art2["title"] == GOOD["title"] and len(calls) == 2
        assert "LENGTH OVERRIDE" in calls[1]
        print("  4. TRUNCATED error -> override retry ✔")

        # ---- 5. trend/topic flow (generate_article) kuda fix aundi ----
        calls.clear()
        gc._call_model = fake_call
        orig_key = config.GEMINI_API_KEY
        config.GEMINI_API_KEY = "test-key"
        try:
            art3 = gc.generate_article("Central Govt Jobs", [], 2026)
        finally:
            config.GEMINI_API_KEY = orig_key
        assert art3["title"] == GOOD["title"]
        assert "LENGTH OVERRIDE" in calls[1], "generate_article retry prompt"
        print("  5. generate_article flow (override retry) ✔")
    finally:
        gc._call_model = real_call
        gc._models = real_models
        gc.time = real_time

    print("ALL v17.1 TRUNCATION TESTS PASSED ✔")
    return 0


if __name__ == "__main__":
    sys.exit(main())
