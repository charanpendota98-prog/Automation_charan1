"""NotebookLM-ready, source-grounded research bundles.

NotebookLM is a user-authenticated product, not a public API that this bot can
silently log into. This module prepares a focused bundle of public sources and
an evidence-first prompt for the owner to import into NotebookLM. The output
asks for source mapping, conflict detection, gap analysis and citation-backed
claims before any article is drafted.

It deliberately stores public source URLs/text only. Do not put passwords,
OTPs, private documents or bank/identity data into this bundle.
"""
import logging

log = logging.getLogger("autoblog.research_brief")
import json
import re
from datetime import date
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple
from urllib.parse import urlparse

from . import config, research, sources


def _slug(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", (value or "").lower()).strip("-")
    return value[:70] or "research-topic"


def target_year_from_text(text: str) -> int | None:
    """Infer an explicitly requested 20xx target year, without guessing."""
    text = text or ""
    explicit = re.findall(
        r"(?:target|for|year|notification|exam|recruitment|admission|result)"
        r"[^0-9]{0,24}(20[2-9][0-9])",
        text, re.I,
    )
    if explicit:
        return int(explicit[0])
    years = [int(item) for item in re.findall(r"\b(20[2-9][0-9])\b", text)]
    return years[0] if len(years) == 1 else None


def _year_relevance(item: sources.SourceArticle, target_year: int | None) -> str:
    if not target_year:
        return "not-specified"
    haystack = " ".join((item.url, item.title, item.text, item.published_date,
                          item.updated_date)).lower()
    if str(target_year) in haystack:
        return f"target-{target_year}"
    other_years = re.findall(r"\b20[2-9][0-9]\b", haystack)
    if other_years:
        return "other-year/verify"
    return "evergreen/verify-current"


def _sentence_candidates(text: str, limit: int = 18) -> List[str]:
    """Keep likely fact-bearing sentences for a quick evidence index."""
    sentences = re.split(r"(?<=[.!?\u0964])\s+|\n+", text or "")
    markers = re.compile(
        r"\d|date|deadline|fee|salary|eligib|apply|vacan|selection|document|"
        r"official|last date|\u0c24\u0c47\u0c26\u0c40|\u0c2b\u0c40|\u0c05\u0c30\u0c4d\u0c39\u0c24",
        re.I,
    )
    out = []
    seen = set()
    for sentence in sentences:
        clean = " ".join(sentence.split())
        key = clean.lower()
        if len(clean) < 35 or key in seen or not markers.search(clean):
            continue
        seen.add(key)
        out.append(clean[:420])
        if len(out) >= limit:
            break
    return out


def _source_label(item: sources.SourceArticle, index: int) -> str:
    domain = urlparse(item.url).netloc.replace("www.", "") or "unknown-source"
    return f"S{index} — {item.title[:100]} — {domain}"


def _read_url_file(path: str) -> List[str]:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"research URL file not found: {path}")
    urls = []
    for raw in file_path.read_text(encoding="utf-8", errors="replace").splitlines():
        url = raw.strip()
        if url and not url.startswith("#") and sources.is_valid_source_url(url):
            if url not in urls:
                urls.append(url)
    return urls


def collect_sources(seed: str, url_file: str = "", limit: int = 6,
                    target_year: int | None = None) -> Tuple[str, List[sources.SourceArticle]]:
    """Collect a primary source plus related public sources.

    If ``seed`` is a URL it is always first. Otherwise it is used as a focused
    search query. A URL file can supply exact official sources and is useful
    when the owner has already checked the results in NotebookLM.
    """
    seed = (seed or "").strip()
    target_year = target_year or target_year_from_text(seed)
    explicit = _read_url_file(url_file) if url_file else []
    urls: List[str] = []
    if seed.startswith(("http://", "https://")) and sources.is_valid_source_url(seed):
        urls.append(seed)
    urls.extend(url for url in explicit if url not in urls)

    query = seed
    if target_year and str(target_year) not in query:
        query = f"{query} {target_year}".strip()
    # A single supplied link is the primary source, not the entire evidence
    # base. Search its title plus the requested year for independent sources.
    if urls and seed.startswith(("http://", "https://")) and not explicit:
        try:
            seed_article = sources.fetch_source(seed)
            query = f"{seed_article.title} {target_year or ''}".strip()
            results = research.search_web(query, max_results=max(8, limit * 2))
            urls.extend(r["url"] for r in results
                        if sources.is_valid_source_url(r.get("url", ""))
                        and r.get("url") not in urls)
        except Exception as exc:  # noqa: BLE001 — best-effort (silent kaadu)
            log.debug("research_brief.collect_sources skip: %s", exc)
    if not urls:
        if not query:
            raise ValueError("topic or source URL kavali")
        results = research.search_web(query, max_results=max(8, limit * 2))
        urls = [r["url"] for r in results if sources.is_valid_source_url(r.get("url", ""))]

    articles: List[sources.SourceArticle] = []
    seen_domains = set()
    for url in urls:
        if len(articles) >= max(1, limit):
            break
        try:
            item = sources.fetch_source(url)
        except Exception:
            continue
        domain = urlparse(item.url).netloc.replace("www.", "")
        # One page per domain prevents a single publisher from becoming the
        # entire evidence base. Explicit URL lists still preserve first place.
        if domain in seen_domains and url not in explicit[:1]:
            continue
        seen_domains.add(domain)
        articles.append(item)

    if not articles:
        raise RuntimeError("public sources fetch avvaledu; official URLs file tho retry cheyandi")
    return query or articles[0].title, articles


def build_source_bundle(topic: str, articles: Sequence[sources.SourceArticle],
                        target_year: int | None = None) -> str:
    """Create a Markdown bundle that NotebookLM can ingest as one source."""
    year_note = (
        f"Target year: {target_year}. Do not substitute another year's dates, "
        "fees, vacancies or deadlines.\n"
        if target_year else
        "Target year: not explicitly specified; do not infer one from an old post.\n"
    )
    lines = [
        f"# Evidence Bundle: {topic}",
        year_note,
        "",
        "> This is a source bundle for research only. Every source is labelled. "
        "Do not publish this bundle or treat unverified claims as facts.",
        "",
        "## Source index",
        "",
        "| ID | Title | URL | Domain | Published | Updated | Year relevance | Chars |",
        "|---|---|---|---|---|---|---|---:|",
    ]
    for i, item in enumerate(articles, 1):
        domain = urlparse(item.url).netloc.replace("www.", "")
        title = item.title.replace("|", "—")[:120]
        lines.append(
            f"| S{i} | {title} | {item.url} | {domain} | "
            f"{item.published_date or 'not stated'} | {item.updated_date or 'not stated'} | "
            f"{_year_relevance(item, target_year)} | {len(item.text)} |"
        )
    lines += ["", "## Evidence excerpts", ""]
    for i, item in enumerate(articles, 1):
        lines += [
            f"## {_source_label(item, i)}",
            f"Source URL: {item.url}",
            f"Source site: {item.site_name or urlparse(item.url).netloc}",
            f"Published date: {item.published_date or 'not stated'}",
            f"Updated date: {item.updated_date or 'not stated'}",
            f"Year relevance: {_year_relevance(item, target_year)}",
            f"Source description: {item.meta_description or '(not available)'}",
            "",
            "### Extracted text",
            item.text.strip(),
            "",
            "### Fact-bearing candidate sentences (open the source before relying on them)",
        ]
        lines.extend(f"- {candidate}" for candidate in _sentence_candidates(item.text))
        lines += ["", "---", ""]
    return "\n".join(lines).strip() + "\n"


def notebooklm_prompt(topic: str, articles: Sequence[sources.SourceArticle],
                      target_year: int | None = None) -> str:
    """Prompt for a citation-backed NotebookLM research pass."""
    ids = ", ".join(f"S{i}" for i in range(1, len(articles) + 1))
    year_policy = (
        f"""\n## Zero-confusion target-year policy — {target_year}
This assignment is specifically for {target_year}. Use {target_year} information
only when the source actually supports it. A {date.today().year} or older page
cannot establish a {target_year} deadline, fee, vacancy, eligibility rule or
schedule unless the source explicitly says it continues into {target_year}.
Classify each source as target-year, other-year, or evergreen. Never silently
carry forward an old post. If a {target_year} official notification is not
released or cannot be verified, say that clearly and do not invent projected
numbers or dates. Put “as of [date]” beside time-sensitive claims.
"""
        if target_year else
        """\n## Date policy
Do not call a fact current unless its publication/update date and source context
support that wording. Old posts are leads only; verify every time-sensitive
claim against the newest primary source.
"""
    )
    return f"""# NotebookLM research protocol — {topic}

Import the accompanying evidence bundle into a focused NotebookLM notebook.
NotebookLM answers are useful only when the source passages are opened and
verified. Use the citations shown by NotebookLM; do not cite NotebookLM itself.
Selected source IDs: {ids}
{year_policy}
## Pass 1 — source map
Create a table with one row per source:
- source ID, publisher/domain, publication or update date if present
- what the source directly establishes
- authority/primary-source status and scope
- missing information and possible bias
Every row must cite the source passage. If a date is absent, write “not stated”.

## Pass 2 — fact ledger
Create a claim ledger with these columns:
1. Claim ID
2. Exact claim in your own short words
3. Source ID and exact citation
4. Claim type: date, number, eligibility, fee, process, salary, location, advice
5. Confidence: directly stated / supported inference / unresolved
6. Safe wording for a Telugu reader
Do not merge two sources into one stronger claim unless both support it.

## Pass 3 — conflict and freshness audit
List every disagreement about dates, fees, counts, eligibility, salary or process.
For each disagreement, quote the relevant citations, prefer the current official
notice only when it is actually present, and otherwise mark the claim
“verify on the official portal”. Never pick the most convenient number.

## Pass 4 — gap and user-intent brief
Answer:
- What will a student try to do after reading this?
- Which steps, documents, costs, risks and mistakes are missing?
- What can this article add that is not just a paraphrase of the sources?
- Which official links should be visible to readers?
- Which claims must be excluded because no source supports them?

## Pass 5 — article brief, not final copy
Return a Telugu + natural English outline with:
- one reader-first title idea, not keyword stuffing
- a 40–60 word direct answer supported by citations
- section headings and the unique value each section adds
- a compact facts table using only Claim IDs
- a source-linked FAQ where each answer is supported
- an editorial checklist for human review
Do not copy source wording, sentence order, headings, tables or distinctive
phrases. Do not stitch source paragraphs together. Do not invent facts to fill
gaps. Keep Claim IDs beside each draft point so an editor can verify them.

## Final human review gate
Before writing/publishing, open every citation, compare the surrounding context,
remove unsupported claims, check dates/fees/eligibility against the official
notice, rewrite in an independent Telugu voice, and confirm that the final page
would still help a reader even if Search did not exist.
"""


def validate_editor_brief(brief: str, source_urls: Sequence[str],
                          target_year: int | None = None) -> dict:
    """Require a real citation-bearing NotebookLM/editor output.

    This is a structural gate, not a truth detector. The editor still has to
    open citations and verify claims. It prevents a plain uncited AI summary
    from being silently presented to the writer as verified research.
    """
    text = (brief or "").strip()
    source_ids = {f"S{i}" for i in range(1, len(source_urls) + 1)}
    cited_ids = {f"S{match}" for match in re.findall(r"\bS(\d+)\b", text, re.I)}
    has_claim_ledger = bool(re.search(r"claim\s*id|fact\s+ledger", text, re.I))
    has_conflict_check = bool(re.search(r"conflict|disagree|unresolved", text, re.I))
    usable_ids = sorted(cited_ids & source_ids)
    problems = []
    if len(text) < 400:
        problems.append("brief too short")
    if not has_claim_ledger:
        problems.append("Claim ID/fact ledger section missing")
    if not has_conflict_check:
        problems.append("conflict audit section missing")
    if len(usable_ids) < min(2, len(source_ids)):
        problems.append("fewer than two supplied source IDs cited")
    if target_year and str(target_year) not in text:
        problems.append(f"target year {target_year} is not stated in the brief")
    return {"ok": not problems, "problems": problems,
            "source_ids": usable_ids, "claims": len(re.findall(r"\bC(?:laim)?[- ]?\d+\b", text, re.I))}


def write_bundle(topic: str, articles: Sequence[sources.SourceArticle],
                output_dir: Path | None = None, target_year: int | None = None) -> dict:
    output_dir = output_dir or getattr(config, "RESEARCH_BRIEF_DIR", config.OUTPUT_DIR / "research")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{_slug(topic)}-{date.today().isoformat()}"
    bundle_path = output_dir / f"{stem}-sources.md"
    prompt_path = output_dir / f"{stem}-notebooklm-prompt.md"
    manifest_path = output_dir / f"{stem}-manifest.json"
    bundle_path.write_text(build_source_bundle(topic, articles, target_year), encoding="utf-8")
    prompt_path.write_text(notebooklm_prompt(topic, articles, target_year), encoding="utf-8")
    manifest = {
        "topic": topic,
        "target_year": target_year,
        "created": date.today().isoformat(),
        "sources": [
            {"id": f"S{i}", "url": item.url, "title": item.title,
             "domain": urlparse(item.url).netloc.replace("www.", ""),
             "published_date": item.published_date,
             "updated_date": item.updated_date,
             "year_relevance": _year_relevance(item, target_year)}
            for i, item in enumerate(articles, 1)
        ],
        "bundle": str(bundle_path),
        "prompt": str(prompt_path),
        "notebooklm_required": True,
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"bundle": bundle_path, "prompt": prompt_path, "manifest": manifest_path,
            "sources": len(articles)}


def run(seed: str, url_file: str = "", limit: int = 6,
        target_year: int | None = None) -> int:
    try:
        target_year = target_year or target_year_from_text(seed)
        topic, articles = collect_sources(
            seed, url_file=url_file, limit=limit, target_year=target_year)
        result = write_bundle(topic, articles, target_year=target_year)
    except Exception as exc:  # noqa: BLE001
        print(f"❌ NotebookLM research bundle failed: {exc}")
        return 1
    print("=" * 78)
    print(f"  NOTEBOOKLM-READY RESEARCH BUNDLE ({result['sources']} sources)")
    print("=" * 78)
    print(f"  Target year: {target_year or 'not specified'}")
    print(f"  Sources : {result['bundle']}")
    print(f"  Prompt  : {result['prompt']}")
    print(f"  Manifest: {result['manifest']}")
    print("\n  Import the sources file into NotebookLM, run the five passes, and save")
    print("  the cited brief. This bot cannot access a private NotebookLM account")
    print("  or pretend that a NotebookLM answer was independently verified.")
    print("=" * 78)
    return 0
