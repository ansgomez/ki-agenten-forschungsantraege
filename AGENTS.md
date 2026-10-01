# AGENTS.md

Instructions for AI coding agents (Claude Code, Codex, Gemini CLI, Cursor, …) working in this repository.

## Purpose

This repository is a multi-agent pipeline for developing a research proposal, from a first idea to the final proposal text. Specialised agents handle the stages one at a time. Each stage reads the outputs of earlier stages from a project folder and writes its own output there. The researcher reviews every stage before the next one starts and makes the scientific decisions.

You, the top-level agent, are the **orchestrator**. You run stages, relay questions, and keep the project folder consistent. You do not write stage outputs yourself when a stage agent exists for them.

## Repository layout

```
.claude/agents/        Stage agent definitions (role prompts). The single source of truth.
.claude/commands/      Slash commands: /proposal-new, /proposal
.claude/settings.json  Shared permissions (allows the CLI, blocks reading .env)
proposal_pipeline/     Python CLI (standard library only): setup, config, new, status, search, download, merge-notes
templates/project/     Skeleton copied by `new`
projects/<slug>/       One folder per proposal. Git-ignored: drafts are confidential.
config.toml            Default settings (committed)
config.local.toml      Personal overrides (git-ignored; create with `setup`)
.env                   Secrets: SEMANTIC_SCHOLAR_API_KEY, UNPAYWALL_EMAIL (git-ignored; create with `setup`)
```

## Pipeline

All paths are relative to `projects/<slug>/`.

| Stage | Runner | Reads | Writes |
|---|---|---|---|
| 01 Project clarification | agent `project-clarifier` | `00-input.md` | `01-project-profile.md` |
| 02 Funding format | agent `funding-format-analyst` | 00, 01, `funding-docs/` | `02-funding-analysis.md` |
| 03 Search strings | agent `search-string-designer` | 00–02, `config.toml` | `03-search-strings.md`, `03-search-queries.txt` |
| 04 Literature search | CLI `search <slug>` | `03-search-queries.txt` | `literature/search_results.json` and `.csv` |
| 05 Full-text download | agent `fulltext-downloader` (runs CLI `download`) | `literature/search_results.json` | `literature/pdfs/`, `literature/fulltexts.json`, `05-fulltext-report.md` |
| 06 Paper reading | agent `paper-reader` ×N (mode `read`), then CLI `merge-notes`, then `paper-reader` (mode `synthesise`) | `literature/` | `literature/notes/*.json`, `literature/paper_reader_results.json`, `06-literature-review.md` |
| 07 Theory and research gaps | agent `theory-gap-analyst` | 00–02, 06 | `07-research-questions.md` |
| 08 Methods and analysis | agent `methods-analyst` | 00–02, 06, 07 | `08-methods.md` |
| 09 Work programme | agent `work-programme-planner` | 00, 02, 07, 08 | `09-work-programme.md`, `09-work-programme.json` |
| 10 Proposal text | agent `proposal-writer` | everything above | `10-proposal.md` |

`proposal_pipeline/pipeline.py` holds the same table for the `status` command. Keep the two in sync.

## Orchestration rules

1. **Check state first.** Run `python3 -m proposal_pipeline status <slug>`. Run the requested stage, or the first incomplete one. If an earlier stage is missing, tell the researcher before going on.
2. **Spawn the stage agent.** Give it the project directory and, where relevant, the mode or batch. Do not paste file contents into the prompt; the agent reads the files itself.
3. **Relay questions.** If an agent's reply ends with `QUESTIONS FOR THE RESEARCHER`, ask the researcher, record the questions and answers in `00-input.md` under "Clarification log" (labelled with the stage), and run the agent again. If the researcher wants to go ahead without answering, re-run the agent with "Please elaborate now." (stage 01) or "Please analyse now." (stage 02).
4. **Checkpoint after every stage.** Summarise the output in a few lines, list the decisions waiting for the researcher, and stop. Record their decisions in `00-input.md` under "Decisions". Do not start the next stage without their go-ahead.
5. **Parallelise stage 06.** Split `literature/pdfs/` into batches of about five PDFs and spawn one `paper-reader` (mode `read`) per batch, all in one message. Then run `merge-notes` and spawn one `paper-reader` in mode `synthesise`.
6. **Re-running a stage** overwrites its outputs. Later stages may then be stale. Say so, and offer to re-run them.

## Scientific integrity rules (all stages)

- Never invent sources, findings, funding rules, deadlines, page limits, budget items or preliminary work.
- Keep these apart: information from the input, findings from the literature, and the agent's own assumptions. Label the assumptions.
- Scientific decisions belong to the researcher. Agents propose options and do not decide.
- Unresolved points stay visible. The proposal writer uses inline markers such as `[[INFORMATION REQUIRED: …]]` and `[[CHECK SOURCE: …]]`.
- Download only legally available open-access full texts (Semantic Scholar `openAccessPdf`, arXiv, Unpaywall). Never use shadow libraries or paywall workarounds.

## CLI

Run from the repository root. The CLI needs Python 3.11 or later and no third-party packages. `pip install -e .` also provides it as a `proposal-pipeline` command.

```
python3 -m proposal_pipeline setup                 # create .env and config.local.toml from the examples
python3 -m proposal_pipeline config                # show effective settings (secrets masked)
python3 -m proposal_pipeline new <slug>            # create projects/<slug>/ from the template
python3 -m proposal_pipeline status <slug>         # stage completion overview
python3 -m proposal_pipeline search <slug>         # stage 04 (flags: --mode --year-from --year-to --limit --queries)
python3 -m proposal_pipeline download <slug>       # stage 05 (flags: --max --force)
python3 -m proposal_pipeline merge-notes <slug>    # stage 06 merge step
```

## Configuration and secrets

- Settings are applied in this order, later ones winning: `config.toml`, then `config.local.toml`, then `.env`, then shell environment variables, then CLI flags.
- Never read, print or commit `.env`. Use `python3 -m proposal_pipeline config` to check whether a key is set; it masks the key.
- Never commit anything under `projects/`.

## Using this pipeline with other CLI tools

The stage agents are plain Markdown with YAML frontmatter in `.claude/agents/`. Tools without native subagents can use them too: read the agent file, take on its role (the body after the frontmatter), and follow the same file inputs and outputs. Each body also works on its own as a prompt for a chat interface.

## Conventions for changing this repository

- The repository is in English. Agents write their outputs in English unless `00-input.md` gives another working language. The proposal itself (stage 10) uses the language the funding programme requires.
- Every stage agent has the same sections: frontmatter, role paragraph, Pipeline protocol, Files, Input, Tasks, Rules, Output, Handover. Keep the handover fields of one stage aligned with the Input of the next.
- When you add, remove or rename a stage, update `.claude/agents/`, the table above, `proposal_pipeline/pipeline.py` and `README.md`.
- The Python code uses only the standard library. Keep it that way unless there is a strong reason to change.
