---
description: Reload saved workshop state from progress.txt and orient the session to continue the build
---

# /resume

Load the saved session state from `progress.txt` and orient the current conversation so work
can continue immediately. Ask at most one clarifying question.

---

## Process

### Step 1: Check for progress.txt

```bash
ls progress.txt 2>/dev/null
```

If not found:

> `progress.txt` not found. Run `/save-state` first, or `/start-session` to load context from scratch.

### Step 2: Read progress.txt

Extract beat statuses, open issues, locked decisions, and the NEXT ACTION line.

### Step 3: Verify against the filesystem

```bash
ls -la *.ipynb plans/DECISIONS.md plans/subagents/*.md diagrams/*.mmd 2>/dev/null
```

If the filesystem contradicts progress.txt, trust the filesystem and flag the difference.
Do NOT re-run full validation.

### Step 4: Print orientation summary

```
=== RESUMED SESSION ===

Saved: <date>

NOTEBOOK
  <notebook>.ipynb - <N> cells

DONE
  Beat 1 - El problema (cells ...)

IN PROGRESS / NEXT
  Beat 2 - PEFT en vivo  [plan exists, no cells built yet]

NOT STARTED
  Beats 3-5

DIAGRAMS
  Built: <list>    Missing: <list>

OPEN ISSUES
  <list or "none">

NEXT ACTION
  /build-notebook 2
  Reason: <one sentence>

KEY DECISIONS (active)
  - Notebook in Spanish, identifiers English, chat English
  - ONE notebook, nothing blocks, solutions at the end
  - Colab free T4, keys via getpass, every slow cell has a fallback
  - Verify cell_id with the python snippet before every NotebookEdit

=== READY ===
```

### Step 5: Ask at most one clarifying question

Only if the intent is genuinely ambiguous. Never ask for what progress.txt already says.

---

## Non-Negotiables

- Read progress.txt first, verify against filesystem second
- Print the summary before asking anything
- One question max
- Do not start building or fixing anything until the user says "go" or "continue"
