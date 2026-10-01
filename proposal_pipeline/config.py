"""Configuration loading.

Precedence, lowest to highest:
  config.toml (committed defaults)
  config.local.toml (git-ignored personal overrides)
  .env (git-ignored secrets; never overrides variables already set in the shell)
  real environment variables
  command-line flags (applied by the CLI)
"""

from __future__ import annotations

import os
import tomllib
from pathlib import Path

SECRET_KEYS = ("SEMANTIC_SCHOLAR_API_KEY", "UNPAYWALL_EMAIL")

DEFAULTS = {
    "paths": {"projects_dir": "projects"},
    "search": {
        "mode": "relevance",
        "year_from": 2015,
        "year_to": 0,
        "results_per_query": 10,
        "pause_seconds": 5.0,
        "fields_of_study": [],
        "min_citation_count": 0,
        "open_access_only": False,
    },
    "download": {
        "max_papers": 50,
        "pause_seconds": 1.0,
        "timeout_seconds": 60,
        "use_unpaywall": True,
    },
}


def find_repo_root(start: Path | None = None) -> Path:
    """Walk up from `start` (default: cwd) to the directory holding config.toml."""
    here = (start or Path.cwd()).resolve()
    for directory in (here, *here.parents):
        if (directory / "config.toml").is_file():
            return directory
    # Fall back to the checkout this package lives in.
    return Path(__file__).resolve().parent.parent


def _deep_merge(base: dict, override: dict) -> dict:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_dotenv(path: Path) -> None:
    """Minimal .env reader: KEY=VALUE lines, # comments, optional quotes."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.removeprefix("export ").strip()
        value = value.strip().strip("'\"")
        if key and value:
            os.environ.setdefault(key, value)


def load_config(root: Path | None = None) -> dict:
    root = root or find_repo_root()
    config = _deep_merge(DEFAULTS, {})
    for name in ("config.toml", "config.local.toml"):
        path = root / name
        if path.is_file():
            with path.open("rb") as file:
                config = _deep_merge(config, tomllib.load(file))

    load_dotenv(root / ".env")
    config["secrets"] = {key: os.environ.get(key) or None for key in SECRET_KEYS}
    config["root"] = root
    return config


def mask(secret: str | None) -> str:
    if not secret:
        return "not set"
    if "@" in secret:
        return "set"
    return f"set (...{secret[-4:]})"
