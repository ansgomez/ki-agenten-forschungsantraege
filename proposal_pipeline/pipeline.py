"""Stage definitions. Keep in sync with the pipeline table in AGENTS.md."""

from __future__ import annotations

from pathlib import Path

# (stage id, title, runner, output paths relative to the project directory)
STAGES = [
    ("01", "Project clarification", "agent: project-clarifier", ["01-project-profile.md"]),
    ("02", "Funding format analysis", "agent: funding-format-analyst", ["02-funding-analysis.md"]),
    ("03", "Search strings", "agent: search-string-designer", ["03-search-strings.md", "03-search-queries.txt"]),
    ("04", "Literature search", "cli: search", ["literature/search_results.json"]),
    ("05", "Full-text download", "agent: fulltext-downloader", ["literature/fulltexts.json", "05-fulltext-report.md"]),
    ("06", "Paper reading", "agent: paper-reader (read, merge-notes, synthesise)", ["literature/paper_reader_results.json", "06-literature-review.md"]),
    ("07", "Theory and research gaps", "agent: theory-gap-analyst", ["07-research-questions.md"]),
    ("08", "Methods and analysis", "agent: methods-analyst", ["08-methods.md"]),
    ("09", "Work programme", "agent: work-programme-planner", ["09-work-programme.md", "09-work-programme.json"]),
    ("10", "Proposal text", "agent: proposal-writer", ["10-proposal.md"]),
]


def stage_status(project_dir: Path) -> list[tuple[str, str, str, bool, list[str]]]:
    rows = []
    for stage_id, title, runner, outputs in STAGES:
        missing = [o for o in outputs if not (project_dir / o).exists()]
        rows.append((stage_id, title, runner, not missing, missing))
    return rows
