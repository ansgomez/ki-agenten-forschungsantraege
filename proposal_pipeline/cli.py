"""Command-line interface: `python3 -m proposal_pipeline <command>`."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from . import download, search
from .config import find_repo_root, load_config, mask
from .pipeline import stage_status


def resolve_project(config: dict, project: str) -> Path:
    """Accept either a slug (looked up in projects_dir) or a path to a project directory."""
    as_path = Path(project)
    if as_path.is_dir():
        return as_path.resolve()
    return config["root"] / config["paths"]["projects_dir"] / project


def cmd_setup(config: dict, args) -> int:
    root = config["root"]
    for example, target in ((".env.example", ".env"), ("config.local.toml.example", "config.local.toml")):
        if (root / target).exists():
            print(f"exists:  {target} (left unchanged)")
        else:
            shutil.copy(root / example, root / target)
            print(f"created: {target}")
    (root / ".env").chmod(0o600)
    print("\nNext: put your API key into .env and adjust config.local.toml if needed.")
    print("Both files are git-ignored. Check with `python3 -m proposal_pipeline config`.")
    return 0


def cmd_config(config: dict, args) -> int:
    print(f"Repository root: {config['root']}")
    for section in ("paths", "search", "download"):
        print(f"\n[{section}]")
        for key, value in config[section].items():
            print(f"{key} = {json.dumps(value)}")
    print("\n[secrets]  (from environment or .env)")
    for key, value in config["secrets"].items():
        print(f"{key}: {mask(value)}")
    return 0


def cmd_new(config: dict, args) -> int:
    target = resolve_project(config, args.project)
    if target.exists():
        print(f"Project already exists: {target}")
        return 1
    shutil.copytree(config["root"] / "templates" / "project", target)
    print(f"Created {target}")
    print(f"Next: fill in {target / '00-input.md'} and put official funding documents in {target / 'funding-docs'}/.")
    return 0


def cmd_status(config: dict, args) -> int:
    project_dir = resolve_project(config, args.project)
    if not project_dir.is_dir():
        print(f"No such project: {project_dir}")
        return 1
    print(f"Project: {project_dir}\n")
    next_stage = None
    for stage_id, title, runner, done, missing in stage_status(project_dir):
        mark = "x" if done else " "
        print(f"[{mark}] {stage_id} {title:<26} {runner}")
        if not done and next_stage is None:
            next_stage = stage_id
    print(f"\nNext stage: {next_stage or 'none, all stages complete'}")
    return 0


def cmd_search(config: dict, args) -> int:
    settings = dict(config["search"])
    for key in ("mode", "year_from", "year_to", "results_per_query"):
        if getattr(args, key) is not None:
            settings[key] = getattr(args, key)
    project_dir = resolve_project(config, args.project)
    return search.run(project_dir, settings, config["secrets"]["SEMANTIC_SCHOLAR_API_KEY"], args.queries)


def cmd_download(config: dict, args) -> int:
    project_dir = resolve_project(config, args.project)
    return download.run(project_dir, config["download"], config["secrets"]["UNPAYWALL_EMAIL"], args.max, args.force)


def cmd_merge_notes(config: dict, args) -> int:
    project_dir = resolve_project(config, args.project)
    notes_dir = project_dir / "literature" / "notes"
    merged = []
    for path in sorted(notes_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        merged.extend(data if isinstance(data, list) else [data])
    out_file = project_dir / "literature" / "paper_reader_results.json"
    out_file.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Merged {len(merged)} paper notes into {out_file}")
    return 0 if merged else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="proposal-pipeline",
        description="Helper commands for the multi-agent research proposal pipeline (see AGENTS.md).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("setup", help="create .env and config.local.toml from their examples").set_defaults(func=cmd_setup)
    sub.add_parser("config", help="show the effective configuration (secrets masked)").set_defaults(func=cmd_config)

    p = sub.add_parser("new", help="create a project folder from the template")
    p.add_argument("project", help="project slug, e.g. dfg-sachbeihilfe-2027")
    p.set_defaults(func=cmd_new)

    p = sub.add_parser("status", help="show which pipeline stages are complete")
    p.add_argument("project", help="project slug or path")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("search", help="stage 04: query Semantic Scholar with 03-search-queries.txt")
    p.add_argument("project", help="project slug or path")
    p.add_argument("--queries", type=Path, help="alternative query file")
    p.add_argument("--mode", choices=["relevance", "bulk"])
    p.add_argument("--year-from", dest="year_from", type=int)
    p.add_argument("--year-to", dest="year_to", type=int)
    p.add_argument("--limit", dest="results_per_query", type=int, help="results per query")
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("download", help="stage 05: download open-access PDFs for the search results")
    p.add_argument("project", help="project slug or path")
    p.add_argument("--max", type=int, help="maximum number of papers to process")
    p.add_argument("--force", action="store_true", help="re-download PDFs that already exist")
    p.set_defaults(func=cmd_download)

    p = sub.add_parser("merge-notes", help="stage 06: merge literature/notes/*.json into paper_reader_results.json")
    p.add_argument("project", help="project slug or path")
    p.set_defaults(func=cmd_merge_notes)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = load_config(find_repo_root())
    return args.func(config, args)


if __name__ == "__main__":
    sys.exit(main())
