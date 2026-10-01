---
description: Start a new research proposal project and collect the starting information
argument-hint: <project-slug>
---

Start a new proposal project with the slug `$ARGUMENTS`. If no slug was given, ask for a short one (lowercase, hyphens, e.g. `dfg-sachbeihilfe-2027`).

1. Run `python3 -m proposal_pipeline new <slug>`.
2. Run `python3 -m proposal_pipeline config`. If `SEMANTIC_SCHOLAR_API_KEY` is not set, tell the researcher that stage 04 works best with a key, and that `python3 -m proposal_pipeline setup` creates the git-ignored `.env` to put it in. Do not ask for the key in chat.
3. Ask the researcher for the starting information in `projects/<slug>/00-input.md`: research idea, discipline, target group, funder / programme, preliminary work and resources, and special conditions. Record what they give and leave the rest as `TBD`.
4. Ask them to put the official funding documents (call text, guidelines, proposal template) into `projects/<slug>/funding-docs/`.
5. Then run stage 01 as described in AGENTS.md ("Orchestration rules").
