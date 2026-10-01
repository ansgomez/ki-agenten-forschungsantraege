"""Stage 04: literature search with the Semantic Scholar Graph API.

Reads one search string per line from 03-search-queries.txt (blank lines and
lines starting with # are ignored), queries Semantic Scholar, removes
duplicates, and writes literature/search_results.json and .csv.
"""

from __future__ import annotations

import csv
import json
import time
from pathlib import Path

from .net import HttpError, fetch_json

API_BASE = "https://api.semanticscholar.org/graph/v1"
FIELDS = (
    "paperId,title,authors,year,abstract,citationCount,venue,url,"
    "externalIds,openAccessPdf"
)
CSV_FIELDS = [
    "title", "year", "authors", "venue", "citation_count", "doi",
    "url", "open_access_pdf", "search_query", "abstract",
]


def load_queries(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip() and not line.strip().startswith("#")]


def _year_range(year_from: int, year_to: int) -> str | None:
    if not year_from and not year_to:
        return None
    return f"{year_from or ''}-{year_to or ''}"


def search_query(query: str, settings: dict, api_key: str | None) -> list[dict]:
    """Run one query against Semantic Scholar and return normalised records."""
    mode = settings["mode"]
    limit = int(settings["results_per_query"])
    params = {"query": query, "fields": FIELDS}

    years = _year_range(settings["year_from"], settings["year_to"])
    if years:
        params["year"] = years
    if settings["fields_of_study"]:
        params["fieldsOfStudy"] = ",".join(settings["fields_of_study"])
    if settings["min_citation_count"]:
        params["minCitationCount"] = str(settings["min_citation_count"])
    if settings["open_access_only"]:
        params["openAccessPdf"] = ""

    if mode == "relevance":
        endpoint = f"{API_BASE}/paper/search"
        params["limit"] = str(min(limit, 100))
    elif mode == "bulk":
        endpoint = f"{API_BASE}/paper/search/bulk"
    else:
        raise ValueError(f"Unknown search mode {mode!r}; use 'relevance' or 'bulk'.")

    headers = {"x-api-key": api_key} if api_key else {}
    data = fetch_json(endpoint, params=params, headers=headers, backoff=settings["pause_seconds"])
    return [_normalise(paper, query) for paper in (data.get("data") or [])[:limit]]


def _normalise(paper: dict, query: str) -> dict:
    external_ids = paper.get("externalIds") or {}
    open_access = paper.get("openAccessPdf") or {}
    return {
        "paper_id": paper.get("paperId"),
        "title": paper.get("title"),
        "year": paper.get("year"),
        "authors": [a["name"] for a in paper.get("authors") or [] if a.get("name")],
        "abstract": paper.get("abstract"),
        "citation_count": paper.get("citationCount"),
        "venue": paper.get("venue"),
        "doi": external_ids.get("DOI"),
        "arxiv_id": external_ids.get("ArXiv"),
        "url": paper.get("url"),
        "open_access_pdf": open_access.get("url") or None,
        "search_query": query,
    }


def remove_duplicates(results: list[dict]) -> list[dict]:
    """Drop repeated hits, keyed by DOI or, failing that, by title."""
    seen = set()
    unique = []
    for paper in results:
        key = (paper.get("doi") or paper.get("title") or "").lower().strip()
        if key and key not in seen:
            seen.add(key)
            unique.append(paper)
    return unique


def save_json(results: list[dict], path: Path) -> None:
    path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")


def save_csv(results: list[dict], path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for paper in results:
            writer.writerow({**paper, "authors": "; ".join(paper.get("authors") or [])})


def run(project_dir: Path, settings: dict, api_key: str | None, queries_file: Path | None = None) -> int:
    queries_file = queries_file or project_dir / "03-search-queries.txt"
    if not queries_file.is_file():
        print(f"Query file not found: {queries_file}\nRun stage 03 (search-string-designer) first.")
        return 1

    queries = load_queries(queries_file)
    if not queries:
        print(f"{queries_file} contains no search strings.")
        return 1

    if not api_key:
        print("Note: SEMANTIC_SCHOLAR_API_KEY is not set. The shared public rate limit applies,")
        print("      so requests may fail. Run `python3 -m proposal_pipeline setup` to add a key.\n")

    print(f"Loaded search strings: {len(queries)} (mode: {settings['mode']})")
    all_results = []
    failed = 0
    for number, query in enumerate(queries, start=1):
        print(f"\nSearch {number}/{len(queries)}: {query}")
        try:
            results = search_query(query, settings, api_key)
        except HttpError as error:
            print(f"  Skipped: {error}")
            failed += 1
            results = []
        print(f"  Hits: {len(results)}")
        all_results.extend(results)
        if number < len(queries):
            time.sleep(settings["pause_seconds"])

    unique = remove_duplicates(all_results)
    out_dir = project_dir / "literature"
    out_dir.mkdir(parents=True, exist_ok=True)
    save_json(unique, out_dir / "search_results.json")
    save_csv(unique, out_dir / "search_results.csv")

    print(f"\nTotal hits: {len(all_results)}")
    print(f"After removing duplicates: {len(unique)}")
    print(f"Failed queries: {failed}")
    print(f"Written: {out_dir / 'search_results.json'} and .csv")
    return 0 if failed < len(queries) else 1
