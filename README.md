# AI agents for research proposals

A multi-agent pipeline that develops a research proposal step by step, from a first research idea to the full proposal text. Each stage is a specialised agent with a narrow task. The researcher reviews every stage and keeps the scientific decisions.

The pipeline runs in CLI coding agents. [Claude Code](https://claude.com/claude-code) supports it natively through subagents and slash commands. Other tools (Codex, Gemini CLI, Cursor, …) can use it through [`AGENTS.md`](AGENTS.md). You can also paste each agent prompt into a chat interface by hand.

## Pipeline

| # | Stage | Agent / tool | Output |
|---|---|---|---|
| 01 | Project clarification | [`project-clarifier`](.claude/agents/project-clarifier.md) | Project profile |
| 02 | Funding format | [`funding-format-analyst`](.claude/agents/funding-format-analyst.md) | Requirements and fit analysis |
| 03 | Search strings | [`search-string-designer`](.claude/agents/search-string-designer.md) | Prioritised search queries |
| 04 | Literature search | `proposal_pipeline search` | Semantic Scholar results (JSON / CSV) |
| 05 | Full-text download | [`fulltext-downloader`](.claude/agents/fulltext-downloader.md) | Open-access PDFs and metadata |
| 06 | Paper reading | [`paper-reader`](.claude/agents/paper-reader.md) (runs in parallel) | Structured notes and literature review |
| 07 | Theory and research gaps | [`theory-gap-analyst`](.claude/agents/theory-gap-analyst.md) | Research questions, aims, hypotheses |
| 08 | Methods and analysis | [`methods-analyst`](.claude/agents/methods-analyst.md) | Study design and analysis plan |
| 09 | Work programme | [`work-programme-planner`](.claude/agents/work-programme-planner.md) | Work packages, timeline, risks |
| 10 | Proposal text | [`proposal-writer`](.claude/agents/proposal-writer.md) | Proposal in the funder's format, with gap markers |

Every stage writes to `projects/<slug>/`. The next stage reads from there. See [`AGENTS.md`](AGENTS.md) for the exact inputs and outputs.

## Setup

Requirements: Python 3.11 or later. No third-party packages are needed.

```bash
git clone git@github.com:ansgomez/ki-agenten-forschungsantraege.git
cd ki-agenten-forschungsantraege
python3 -m proposal_pipeline setup     # creates .env and config.local.toml (both git-ignored)
```

Then edit `.env`:

```bash
SEMANTIC_SCHOLAR_API_KEY=your-key      # https://www.semanticscholar.org/product/api#api-key-form
UNPAYWALL_EMAIL=you@example.org        # optional; adds Unpaywall as a full-text source
```

Search works without an API key, but then the shared public rate limit applies. Check your settings with:

```bash
python3 -m proposal_pipeline config
```

Optionally, `pip install -e .` installs the CLI as a `proposal-pipeline` command.

## Usage with Claude Code

```text
/proposal-new my-project      # creates projects/my-project/ and collects the starting information
/proposal my-project          # runs the next stage, then stops for your review
/proposal my-project 07       # (re)runs a specific stage
```

You can also just ask, e.g. "run the funding format stage for my-project". The orchestrator follows `AGENTS.md`.

## Usage without an agent CLI

```bash
python3 -m proposal_pipeline new my-project
# fill in projects/my-project/00-input.md
# paste the body of each .claude/agents/<agent>.md into your chat tool, with the files it lists
python3 -m proposal_pipeline search my-project
python3 -m proposal_pipeline download my-project
python3 -m proposal_pipeline status my-project
```

## Configuration

| File | Committed | Purpose |
|---|---|---|
| `config.toml` | yes | Defaults: search mode, year range, results per query, download limits |
| `config.local.toml` | no | Your overrides of `config.toml` |
| `.env` | no | Secrets: `SEMANTIC_SCHOLAR_API_KEY`, `UNPAYWALL_EMAIL` |
| `projects/` | no | Your proposals, drafts and PDFs |

Settings are applied in this order, later ones winning: `config.toml`, `config.local.toml`, `.env`, shell environment, CLI flags (`search --year-from 2020 --limit 20`, `download --max 30`).

## Principles

- No invented sources, findings, funding rules or budget items.
- Information from the input, findings from the literature, and the agents' own assumptions are kept apart and labelled.
- The researcher makes every scientific decision. The pipeline stops at each stage for review.
- Only legally available open-access full texts are downloaded.

## License

[CC0 1.0 Universal](LICENSE)
