"""Evidence-backed official-link regression checks.

These tests deliberately use a fake resolver: the production path performs a
real GET before rendering a secondary link, while the assertions stay offline
and deterministic.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from autoblog import pipeline, sources  # noqa: E402


class _Response:
    status_code = 200
    url = "https://tspsc.gov.in/group-apply"
    headers = {"content-type": "text/html"}
    text = "<html><head><title>TSPSC Group Apply</title></head><body><h1>TSPSC Apply</h1></body></html>"


def test_anchor_record_keeps_provenance_and_type():
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(
        '<article><a href="https://tspsc.gov.in/group-apply">Apply Online</a></article>',
        "html.parser",
    )
    record = sources._page_link_records(soup.article, "https://news.example/notice")[0]
    assert record["exact_url"] == "https://tspsc.gov.in/group-apply"
    assert record["anchor_text"] == "Apply Online"
    assert record["source_url"] == "https://news.example/notice"
    assert record["link_type"] == "application"
    assert record["domain_class"] == "official_explicit"
    assert record["verification_status"] == "present_in_source_html"


def test_invented_model_url_is_not_rendered():
    source = sources.SourceArticle(
        url="https://tspsc.gov.in/notice",
        title="TSPSC Group Notification",
        text="Official notice facts",
        outbound_links=[{
            "url": "https://tspsc.gov.in/group-apply",
            "exact_url": "https://tspsc.gov.in/group-apply",
            "text": "Apply Online",
            "anchor_text": "Apply Online",
            "source_url": "https://tspsc.gov.in/notice",
            "link_type": "application",
        }],
    )
    old_get = pipeline.requests.get
    pipeline.requests.get = lambda *args, **kwargs: _Response()
    article = {
        "title": "TSPSC Group Notification",
        "_deep_sources": [source],
        "_source_urls": [source.url],
        "external_links": [
            {"text": "Apply", "url": "https://tspsc.gov.in/not-a-real-path"},
            {"text": "Apply Online", "url": "https://tspsc.gov.in/group-apply"},
        ],
        "recruitment": {"org_url": "https://tspsc.gov.in/model-guessed-org"},
    }
    try:
        pipeline._append_official_sources(article)
        urls = [item["url"] for item in article["external_links"]]
        assert "https://tspsc.gov.in/not-a-real-path" not in urls
        assert any(item["url"] == "https://tspsc.gov.in/not-a-real-path"
                   for item in article["_official_link_audit"]["rejected_model_links"])
        assert "https://tspsc.gov.in/group-apply" in urls
        assert article["application_url"] == "https://tspsc.gov.in/group-apply"
        assert article["recruitment"]["org_url"] == ""
        evidence = next(item for item in article["_official_link_audit"]["links"]
                        if item.get("exact_url") == "https://tspsc.gov.in/group-apply")
        assert evidence["source_url"] == source.url
        assert evidence["final_url"] == _Response.url
    finally:
        pipeline.requests.get = old_get


if __name__ == "__main__":
    test_anchor_record_keeps_provenance_and_type()
    test_invented_model_url_is_not_rendered()
    print("official-link evidence checks: PASS")
