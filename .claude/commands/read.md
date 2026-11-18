---
description: Read all project context files before starting any work
---

Read the following files to load full project context:

1. `CLAUDE.md`: language rule, stack, agenda, notebook conventions, critical rules
2. `plans/DECISIONS.md`: the workshop manifest (if missing, say so and suggest `/init-workshop`)
3. `plans/OUTLINE.md` and `plans/CONTRACT.md`, if they exist
4. `progress.txt`, if it exists

Then report back, as a short table:
- Which beats have plans in `plans/subagents/*_agentdemo.md`
- Which beat sections are already built in the notebook (cell ranges)
- Which diagrams exist in `diagrams/` vs which markers have no `.mmd` yet
- The next beat to work on

Read only. Do not plan or fix anything unless asked.

---

## Notebook Edit Protocol (awareness)

If this command ever edits cells, follow `~/.claude/NOTEBOOK_EDIT_PROTOCOL.md`.
Blind bulk index-based rewrites are forbidden.
