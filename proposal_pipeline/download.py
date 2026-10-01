"""Stage 05: download legally available open-access full texts.

Sources, in order: the Semantic Scholar openAccessPdf link, arXiv, and
Unpaywall (only when UNPAYWALL_EMAIL is set). No other sources are used.
"""

from __future__ import annotations

import json
import re
import time
import unicodedata
import urllib.parse
from pathlib import Path

from .net import HttpError, fetch, fetch_json

STOPWORDS = {"a", "an", "the", "of", "for", "and", "in", "on", "to", "with", "by", "from", "at"}


def _ascii(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()


def pdf_filename(paper: dict) -> str:
    """FirstAuthor_Year_ShortTitle.pdf"""
    authors = paper.get("authors") or []
    last_name = _ascii(authors[0].split()[-1]) if authors else "Unknown"
    words = re.findall(r"[A-Za-z0-9]+", _ascii(paper.get("title") or "untitled"))
    short = "".join(w.capitalize() for w in words if w.lower() not in STOPWORDS)[:40]
    name = f"{last_name}_{paper.get('year') or 'nd'}_{short or 'Untitled'}"
    return re.sub(r"[^A-Za-z0-9_-]", "", name) + ".pdf"


def candidate_urls(paper: dict, settings: dict, email: str | None) -> list[str]:
    urls = []
    if paper.get("open_access_pdf"):
        urls.append(paper["open_access_pdf"])
    if paper.get("arxiv_id"):
        urls.append(f"https://arxiv.org/pdf/{paper['arxiv_id']}")
    if settings["use_unpaywall"] and email and paper.get("doi"):
        doi = urllib.parse.quote(paper["doi"])
        try:
            record = fetch_json(f"https://api.unpaywall.org/v2/{doi}", params={"email": email}, retries=1)
        except HttpError:
            record = {}
        locations = [record.get("best_oa_location")] + (record.get("oa_locations") or [])
        urls += [loc["url_for_pdf"] for loc in locations if loc and loc.get("url_for_pdf")]
    return list(dict.fromkeys(urls))  # de-duplicate, keep order


def run(project_dir: Path, settings: dict, email: str | None, max_papers: int | None = None, force: bool = False) -> int:
    results_file = project_dir / "literature" / "search_results.json"
    if not results_file.is_file():
        print(f"Not found: {results_file}\nRun stage 04 (`search`) first.")
        return 1

    papers = json.loads(results_file.read_text(encoding="utf-8"))
    limit = max_papers or settings["max_papers"]
    papers = papers[:limit]
    pdf_dir = project_dir / "literature" / "pdfs"
    pdf_dir.mkdir(parents=True, exist_ok=True)

    if settings["use_unpaywall"] and not email:
        print("Note: UNPAYWALL_EMAIL is not set; Unpaywall lookups are skipped.\n")

    records = []
    for number, paper in enumerate(papers, start=1):
        filename = pdf_filename(paper)
        target = pdf_dir / filename
        print(f"[{number}/{len(papers)}] {paper.get('title')}")
        status, source = "no_open_access_source", None

        if target.exists() and not force:
            status = "already_present"
        else:
            for url in candidate_urls(paper, settings, email):
                try:
                    body, _ = fetch(url, timeout=settings["timeout_seconds"], retries=1)
                except HttpError as error:
                    status = f"failed: {error}"
                    continue
                if not body.startswith(b"%PDF"):
                    status = "failed: source did not return a PDF"
                    continue
                target.write_bytes(body)
                status, source = "downloaded", url
                break
            time.sleep(settings["pause_seconds"])

        print(f"  {status}")
        has_pdf = status in ("downloaded", "already_present")
        records.append({
            "title": paper.get("title"),
            "authors": paper.get("authors"),
            "year": paper.get("year"),
            "doi": paper.get("doi"),
            "abstract": paper.get("abstract"),
            "pdf_file": filename if has_pdf else None,
            "download_status": status,
            "source_url": source,
        })

    out_file = project_dir / "literature" / "fulltexts.json"
    out_file.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")

    downloaded = sum(1 for r in records if r["pdf_file"])
    print(f"\nPublications checked:   {len(records)}")
    print(f"Full texts available:   {downloaded}")
    print(f"Full texts unavailable: {len(records) - downloaded}")
    print(f"Written: {out_file}")
    return 0
