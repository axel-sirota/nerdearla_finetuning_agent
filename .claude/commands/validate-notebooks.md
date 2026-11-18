---
description: Validate the workshop notebook (syntax, blocking placeholders, solutions, Spanish, AI-tells, T4 and key hygiene)
---

# Validate Notebooks

There is ONE notebook. No exercise/solution pair.

## What This Command Checks

### Nothing blocks (the most important check)
- **No `= None  # TU CODIGO` anywhere in the main flow.** Every cell runs as written
- Mini exercises are comment-only cells, marked `(opcional, para despues)`
- No later cell reads a variable that a mini exercise was supposed to define
- Every mini exercise number has a matching entry in the end solutions section
- Every slow cell (training, download, merge, conversion, server start) has a marked fallback

### Structure
- Four-beat arc per concept: problem intro + naive code, diagram marker + render cell,
  full demo, optional mini exercise
- Every `<!-- DIAGRAM: -->` marker is followed by a `mostrar_diagrama("<slug>")` cell, and
  `diagrams/<slug>.mmd` exists
- A `## Soluciones de los mini ejercicios` section exists near the end

### Language and tone
- **All markdown, comments and printed strings in neutral Spanish with tu.** Flag voseo
  ("vos", "tenés", "fijate", "acordate", "armá") and Argentine slang ("che", "laburo", "plata")
- Code identifiers in English, no half-translated cells
- **Demo code is heavily commented**
- No AI-tells (em dash, en dash, Unicode multiplication, bare --- in markdown)

### Stack and environment
- Keys via `getpass`. **Never hardcoded, never a `.env` file**. Flag any `hf_...` or
  `sk-...` literal
- A GPU check in the setup cell, with a clear Spanish message if there is no GPU
- Nothing T4-incompatible: flag `bf16=True`, `torch.bfloat16` as compute dtype, and
  flash-attention-only settings
- Nothing requiring a paid tier, a cloud account, Docker, or a local install
- Agent code uses `create_agent` from `langchain.agents`, never `create_react_agent`
- Pinned versions in the pip cell match `plans/DECISIONS.md`

## Cell Order Verification

Before any NotebookEdit, print each cell's `id` and first line to confirm order. Never
assume an id.

## Instructions

```bash
.venv/bin/python3 validate_notebooks.py <notebook> --type exercise
```

Then check by reading what the script cannot: comment quality, fallbacks, tone.

## AI-Tells Scan (MANDATORY before marking any notebook done)

```bash
.venv/bin/python3 -c "
import json, sys
path = sys.argv[1]
with open(path) as f:
    nb = json.load(f)
hits = []
banned = [('—', 'em dash'), ('–', 'en dash'), ('×', 'unicode multiplication')]
for i, cell in enumerate(nb['cells']):
    src = ''.join(cell.get('source', []))
    for char, name in banned:
        if char in src:
            line = next((l for l in src.splitlines() if char in l), '')
            hits.append(f'Cell {i} ({cell[\"cell_type\"]}): {name} found -> {line.strip()[:80]}')
    if cell['cell_type'] == 'markdown':
        for j, line in enumerate(src.splitlines()):
            if line.strip() == '---':
                hits.append(f'Cell {i} (markdown): bare --- separator on line {j}')
if hits:
    print('AI-TELLS FOUND:')
    for h in hits: print(' ', h)
    sys.exit(1)
else:
    print('AI-tells scan: clean')
" <notebook_path>
```

Emojis and Spanish accented characters are fine and are NOT flagged.

## Pass Criteria

- No syntax errors in code cells
- **Nothing blocks**
- Every mini exercise has a matching solution
- AI-tells scan clean
- No hardcoded keys, no `.env`
- No T4-incompatible settings
- No deprecated agent builder

## When to Run

- After every 5-cell batch during /build-notebook (mandatory)
- After completing each beat
- Before the workshop, after a full top-to-bottom run on a Colab T4

---

## Notebook Edit Protocol (awareness)

If this command ends up editing cells, follow `~/.claude/NOTEBOOK_EDIT_PROTOCOL.md`.
Blind bulk index-based rewrites are forbidden.
