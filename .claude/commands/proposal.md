---
description: Run the next (or a given) stage of the research proposal pipeline
argument-hint: <project-slug> [stage-number]
---

Arguments: `$ARGUMENTS` (a project slug, optionally followed by a stage number 01–10).

Follow the orchestration rules in AGENTS.md:

1. Run `python3 -m proposal_pipeline status <slug>`.
2. Pick the requested stage, or else the first incomplete one. If an earlier stage is incomplete, say so and ask before going on.
3. Run the stage as the Pipeline table in AGENTS.md describes: spawn the named subagent with the project directory, or run the CLI command. For stage 06, spawn the paper-reader batches in parallel.
4. If the agent returns `QUESTIONS FOR THE RESEARCHER`, ask them, record the questions and answers in `00-input.md` under "Clarification log", and re-run the stage.
5. At the checkpoint, summarise the output in a few lines, list the decisions waiting for the researcher, and stop. Do not start the next stage until the researcher says so.
