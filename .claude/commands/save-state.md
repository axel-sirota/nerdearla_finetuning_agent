---
description: Snapshot workshop state to progress.txt so a new session can resume exactly where the build stopped
---

# /save-state

Snapshot the current session into `progress.txt` so a brand-new conversation can resume
with zero context loss.

## What This Produces

A single file: `progress.txt` (repo root, gitignored). `/resume` reads it and immediately
knows what was built, what was decided, and the exact next command.

---

## Process

### Step 1: Read all state sources (one at a time, never batched)

- `plans/DECISIONS.md`: locked decisions
- `plans/CONTRACT.md` and `plans/OUTLINE.md`, if they exist
- `TODOS.md`, if it exists

Also run:
```bash
ls plans/subagents/*.md diagrams/*.mmd *.ipynb 2>/dev/null
```

And capture the notebook's section map and cell count:
```bash
.venv/bin/python3 -c "
import json, glob
path = [p for p in glob.glob('*.ipynb')][0]
nb = json.load(open(path))
print(path, 'total cells:', len(nb['cells']))
for i, c in enumerate(nb['cells']):
    src = ''.join(c['source'])
    if c['cell_type'] == 'markdown' and src.lstrip().startswith('#'):
        print(i, c.get('id'), src.splitlines()[0][:70])
" 2>/dev/null
```

### Step 2: Derive status for every beat

| Signal | Status label |
|--------|-------------|
| No plan, no cells | `not_started` |
| Plan exists, no cells built | `plan_only` |
| Cells built, validator passes | `done` |
| Cells built, validator fails or open TODOs | `needs_fix` |

```bash
.venv/bin/python3 validate_notebooks.py <notebook> --type exercise
```

### Step 3: Identify the single next action

| Status | Next action |
|--------|-------------|
| no DECISIONS.md | `/init-workshop` |
| `not_started` | `/research-demos N` |
| `plan_only` | `/build-notebook N` |
| `needs_fix` | the specific fix |

If all beats are `done`: `/build-diagrams` for any missing diagram, then a full top-to-bottom
run on a Colab T4.

### Step 4: Write progress.txt

```
WORKSHOP: Fine-tuning a small LLM as an agent tool - Nerdearla
SAVED: <YYYY-MM-DD HH:MM>
REPO: /Users/axelsirota/repos/nerdearla_finetuning_agent

==============================================================================
NOTEBOOK
==============================================================================

<notebook>.ipynb            <N> cells   validator <PASS/FAIL>

==============================================================================
BEAT STATUS
==============================================================================

[done]         Beat 1 - El problema
               cells:    <range or ids>
               plan:     plans/subagents/1_agentdemo.md
               verified: <what was actually run, where: local / Colab T4>

[plan_only]    Beat 2 - PEFT en vivo
               next:     /build-notebook 2

... (one entry per beat)

==============================================================================
KNOWN ISSUES / OPEN TODOS
==============================================================================

==============================================================================
LOCKED DECISIONS (do not re-litigate without Axel)
==============================================================================

- Notebook in Rioplatense Spanish with voseo. Identifiers English. Chat English.
- ONE notebook. Mini-exercise solutions in the end section. NOTHING BLOCKS.
- Colab free T4. Keys via getpass, never .env. No bf16.
- Every slow cell has a non-blocking fallback.
- <base model, task, dataset, serving, orchestrator, from DECISIONS>
- Always verify cell_id with the python snippet before every NotebookEdit.

==============================================================================
KEY FILES
==============================================================================

CLAUDE.md                          language rule, stack, agenda
plans/DECISIONS.md                 source of truth
plans/subagents/N_agentdemo.md     cell-by-cell plans
validate_notebooks.py              gates
reference/estilo_concierge.ipynb   style reference, read-only

==============================================================================
NEXT ACTION
==============================================================================

<ONE specific command>
Reason: <one sentence>

==============================================================================
HOW TO RESUME
==============================================================================

1. Open this repo: /Users/axelsirota/repos/nerdearla_finetuning_agent
2. Run: /resume
```

### Step 5: Confirm

Print a 5-line summary: cell count, done / plan_only / not_started beats, next action.

---

## Non-Negotiables

- Real file paths only, no placeholders
- NEXT ACTION is a single runnable command
- Every beat listed, even if not_started
- Always record the cell count
- Plain text, no markdown formatting, no emoji

---

## Notebook Edit Protocol (awareness)

This command does not edit cells. If it ever does, follow `~/.claude/NOTEBOOK_EDIT_PROTOCOL.md`.
