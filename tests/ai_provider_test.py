"""Offline checks for the multi-provider text-generation adapter."""

import json
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from autoblog import config, gemini_client as client  # noqa: E402


class FakeResponse:
    def __init__(self, data, status_code=200):
        self._data = data
        self.status_code = status_code
        self.text = json.dumps(data)

    def json(self):
        return self._data


def main():
    old_requests = client.requests
    old = {
        "AI_PROVIDER": config.AI_PROVIDER,
        "AI_FALLBACK_PROVIDERS": config.AI_FALLBACK_PROVIDERS,
        "GROQ_API_BASE": config.GROQ_API_BASE,
        "GROQ_API_KEY": config.GROQ_API_KEY,
        "GROQ_API_KEYS": config.GROQ_API_KEYS,
        "GROQ_MODEL": config.GROQ_MODEL,
        "GROQ_FALLBACK_MODELS": config.GROQ_FALLBACK_MODELS,
    }
    try:
        captured = {}

        def post(url, headers=None, json=None, timeout=None, **kwargs):
            captured.update(url=url, headers=headers, payload=json, timeout=timeout)
            return FakeResponse({
                "choices": [{
                    "message": {"content": '{"title":"T","slug":"t"}'},
                    "finish_reason": "stop",
                }]
            })

        client.requests = types.SimpleNamespace(post=post)
        config.GROQ_API_BASE = "https://groq.test/openai/v1"
        result = client._call_model("groq::test-model", "Return JSON", "groq-secret")
        assert json.loads(result)["title"] == "T"
        assert captured["url"] == "https://groq.test/openai/v1/chat/completions"
        assert captured["headers"]["Authorization"] == "Bearer groq-secret"
        assert captured["payload"]["model"] == "test-model"
        assert captured["payload"]["response_format"] == {"type": "json_object"}
        print("  1. OpenAI-compatible request/JSON response ✔")

        config.AI_PROVIDER = "groq"
        config.AI_FALLBACK_PROVIDERS = ["gemini"]
        config.GROQ_API_KEY = "groq-secret"
        config.GROQ_API_KEYS = []
        config.GROQ_MODEL = "test-model"
        config.GROQ_FALLBACK_MODELS = ["fallback-model"]
        order = client._provider_order()
        assert order[0] == "groq"
        assert client._provider_models("groq") == ["test-model", "fallback-model"]
        assert client._provider_keys("groq") == ["groq-secret"]
        print("  2. primary provider, model fallback and key selection ✔")
    finally:
        client.requests = old_requests
        for name, value in old.items():
            setattr(config, name, value)

    print("AI PROVIDER TESTS PASSED ✔")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
