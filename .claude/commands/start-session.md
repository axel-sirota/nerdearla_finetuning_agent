---
description: Begin a work session - load context, review progress, identify next steps
---

Start a new work session for this project.

## GUARD: Read Workshop Manifest First

```bash
ls plans/DECISIONS.md 2>/dev/null
```

If the file does NOT exist, stop and say:

> `plans/DECISIONS.md` not found. Run `/init-workshop` first to record the workshop decisions. Every command requires this file before proceeding.

---

## Step 1: Load All Context

Read, one at a time: `CLAUDE.md`, `plans/DECISIONS.md`, then `progress.txt` if it exists.

## Step 2: Cross-Check Filesystem

```bash
ls -la *.ipynb plans/subagents/*.md diagrams/*.mmd 2>/dev/null
```

```bash
.venv/bin/python3 -c "
import json, glob
for path in glob.glob('*.ipynb'):
    nb = json.load(open(path))
    print(path, 'total cells:', len(nb['cells']))
    for i, c in enumerate(nb['cells']):
        src = ''.join(c['source'])
        if c['cell_type'] == 'markdown' and src.lstrip().startswith('#'):
            print(i, src.splitlines()[0][:70])
" 2>/dev/null
```

Flag anything that:
- progress.txt marks done but has no section in the notebook
- is a `<!-- DIAGRAM -->` marker with no `.mmd` file in `diagrams/`
- is a beat with cells but no plan

## Step 3: Report Status

A short table: beat, status, plan file, cell range. Plus cell count and missing diagrams.

## Step 4: Recommend Next Step

- `/research-demos N` if the beat has no plan
- `/build-notebook N` if the plan exists
- `/build-diagrams N` if the cells exist and diagrams are missing

## Step 5: Ask

"Ready to proceed with [recommended next step]? Or is there something else you want to work on?"

---

## Notebook Edit Protocol (awareness)

If this command ever edits cells, follow `~/.claude/NOTEBOOK_EDIT_PROTOCOL.md`.
