---
description: Build the workshop notebook, 5 cells at a time with approval checkpoints
---

Build the workshop notebook. Optional argument: a beat number to build or rebuild just that
section (e.g. `3`). With no argument, build the whole notebook in agenda order.

$ARGUMENTS

## GUARD: Read Workshop Manifest First

Before doing anything else, check for `plans/DECISIONS.md`:

```bash
ls plans/DECISIONS.md 2>/dev/null
```

If the file does NOT exist, stop immediately and say:

> `plans/DECISIONS.md` not found. Run `/init-workshop` first to record the workshop decisions. Every command requires this file before proceeding.

If it exists, read the full file. It is the source of truth for the arc, the audience, the
tone, the diagrams, the stack, and every decision Axel made in the interview.

---

**CRITICAL INSTRUCTIONS - READ CAREFULLY BEFORE STARTING**

## Command Arguments

- `/build-notebook` builds the whole notebook in agenda order.
- `/build-notebook 3` builds or rebuilds only the Beat 3 section.

The environment is always **Colab with a free T4 GPU**. Do not ask.

There is ONE notebook for the whole workshop, at the repo root, named in DECISIONS.
No exercise/solution pair. Mini-exercise solutions live in a section at its end.

---

## Pre-Work: MANDATORY Reading

### Step 1: Read All Context Files (DO THIS FIRST)

1. **CLAUDE.md**: language rule, stack, agenda, notebook conventions, critical rules
2. **plans/DECISIONS.md**: the workshop manifest
3. **plans/subagents/<N>_agentdemo.md**: the cell-by-cell plan from `/research-demos`
4. If building beat N > 1: the already-built sections of the notebook. Confirm the exact
   variable names, model objects, paths and endpoints already in scope. This is ONE
   notebook, so every earlier variable is still live. Never redefine a name that already
   exists; bridge to it. Never reload a model already in GPU memory.
5. `reference/estilo_concierge.ipynb`: the previous workshop's notebook. Style reference
   only (comment density, NARRAR / PARA CASA markers, voseo). Never copy its content.

### Step 2: Show Plan Summary Before Building

**IN CHAT, SHOW ME (in English):**
1. Beat title and learning objectives
2. Concepts (2-4) with their Problem / Diagram / Demo breakdown
3. Estimated cell count, and the running total for the notebook
4. Which mini exercises this beat adds, and their numbers
5. Continuity bridges from the prior section (exact variable names carried forward)
6. Slow cells and their fallbacks (training, downloads, merge, server start)
7. The clock check: can Axel narrate these cells inside the beat's slot?

**DO NOT PROCEED until I approve this summary.**

---

## Core Teaching Principles

### 1. Four-Beat Arc for Every Concept

**Beat 1 - Problem intro (Markdown + naive/broken code)**
Show what goes wrong WITHOUT this concept. The naive code cell runs and shows the problem.

**Beat 2 - Diagram (Markdown marker + render code cell + Markdown reading)**
```
<!-- DIAGRAM: describe what this diagram should show -->
```
Then a code cell `mostrar_diagrama("<slug>")` (Colab does not render Mermaid in markdown),
then 1-2 sentences on how to read it.

**Beat 3 - Full working demo (Code)**
Complete, runnable, heavily commented. Axel narrates from these comments.

**Beat 4 - Mini exercise (optional)**
A comment-only cell, additive. Nothing downstream reads it.

### 2. Demo-Led, and NOTHING BLOCKS

Axel demos and explains the code as he goes. Attendees take the notebook home and run it
there. Some follow along live on laptops, most just watch.

**Every cell runs top to bottom exactly as written.** There are NO `None  # TU CODIGO`
placeholders in the main flow.

**Slow cells never block the talk.** Training, model downloads, merging and GGUF conversion
take minutes on a T4. Every one needs a clearly marked, non-blocking fallback from the plan
(a pre-trained adapter on the HF Hub, a smaller `max_steps`, a pre-built artifact), and Axel
needs something to say while it runs, written into the comments.

**Mini exercises are additive.** Own cells, never in the path of the next cell.

Mini exercise cell shape:

```python
# EJERCICIO 1 (opcional, para despues)
# Cambia r=8 por r=16 en LoraConfig y fijate cuantos parametros entrenables quedan.
# Pista: print_trainable_parameters() te lo dice en una linea.
# Solucion al final del notebook.
```

**Solutions go in a dedicated section at the end of the notebook**, never inline.

### 3. Tone - Spanish, First Person, Friendly

**Every markdown cell, code comment and printed string is in Spanish.** Code identifiers
stay in English. Chat with Axel stays in English.

- First person plural: "Vamos a ver...", "Fijate que si no hacemos esto..."
- Fully Rioplatense register with voseo: 'fijate', 'arma', 'vos', 'acordate'
- Encouraging and warm; many attendees are fine-tuning for the first time
- Emojis welcome in markdown headers and section titles
- No jargon unless explained in the same cell. "LoRA", "QLoRA", "adapter", "cuantizacion",
  "GGUF" each get one plain-Spanish sentence the first time they appear
- Never half-translate

### 4. Heavy Comments
- Every non-obvious line has a comment explaining the WHY
- Mark cells `(NARRAR)` when Axel talks through them live, `(PARA CASA)` when they are setup
  or detail for later
- The comments ARE the script Axel reads from. Thin comments fail the beat

### 5. Environment
- **Colab, free T4.** Everything installs from the first cell, with pinned versions
- **Keys via `getpass`**, never hardcoded, never a `.env` file
- Nothing that needs a paid tier, a cloud account, or Docker

---

## Notebook Structure

### Header, built once for the whole notebook
- **Markdown**: title with emoji, the pitch quoted, what they leave with
- **Markdown + Code**: Data Trainers cell and the QR to open the notebook in Colab
  (pattern from `reference/estilo_concierge.ipynb`, the QR cell installs its own `qrcode`)
- **Markdown**: "Seccion 0: Preparamos el entorno", including how to switch to a T4 runtime
- **Code**: `!pip install -q ...` pinned from DECISIONS
- **Code**: imports, GPU check with a clear Spanish error if there is no GPU, `getpass` for
  keys, `mostrar_diagrama` helper

### Per Concept (repeat 2-4 times per beat)
1. **Markdown**: section header + problem intro (first person, what breaks without this)
2. **Code**: naive/broken demo that runs and shows the problem
3. **Markdown**: `<!-- DIAGRAM: ... -->` marker
4. **Code**: `mostrar_diagrama("<slug>")`
5. **Markdown**: how to read the diagram
6. **Code**: full working demo, heavily commented
7. **Code** (optional): mini exercise, comment block, additive only

### Closing
- **Markdown**: key takeaways, what we built
- **Markdown**: the when-to-fine-tune template they take home
- **Markdown + Code**: Data Trainers cell and QR
- **Markdown**: Q&A prompt

---

## CRITICAL: 5-Cell Approval Checkpoints - MANDATORY

**YOU MUST NEVER ADD MORE THAN 5 CELLS WITHOUT EXPLICIT USER APPROVAL**

1. Add exactly 5 cells (or fewer for the final batch)
2. STOP IMMEDIATELY
3. Run validation: `.venv/bin/python3 validate_notebooks.py <notebook> --type exercise`
4. **UNCONDITIONAL /save-state rule**: whenever the notebook cell count crosses a multiple of
   10, invoke `/save-state` immediately, including in "go until the end" mode.
5. Ask user: "I have added cells X-Y. How does it look? Should I continue?"
   If the user previously gave blanket "go until end" approval, skip this question and
   continue, but step 4 still fires unconditionally.
6. After approval (or under blanket approval): add ONLY the next 5 cells, then return to step 1.

### Forbidden:
- Adding 6+ cells in a single batch without approval
- Skipping validation between batches
- Skipping /save-state at 10-cell boundaries

### Notebook Write Pattern (CRITICAL FOR FILE SIZE):
Add cells one at a time if any single cell exceeds ~30 lines, to prevent JSON truncation.

---

## Cell Order: ALWAYS Use cell_id

Before EVERY NotebookEdit (replace, insert, OR delete), confirm the cell_id is at the
expected position:

```bash
.venv/bin/python3 -c "
import json
with open('PATH_TO_NOTEBOOK') as f:
    nb = json.load(f)
for i, c in enumerate(nb['cells']):
    print(i, c.get('id','?'), c['cell_type'], repr(''.join(c['source'])[:60]))
"
```

**Never assume cells append to the end automatically. Always chain cell_id.**

### Empty Notebook JSON Skeleton:
```json
{
 "nbformat": 4,
 "nbformat_minor": 5,
 "metadata": {
  "accelerator": "GPU",
  "colab": {"gpuType": "T4", "provenance": [], "toc_visible": true},
  "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
  "language_info": {"name": "python"}
 },
 "cells": []
}
```

`accelerator: GPU` and `gpuType: T4` make Colab open the notebook on a T4 runtime by default.

---

## Markdown Rendering

Markdown cells use raw strings, no escaping. Never escape markdown characters. Never
double-backslash headers.

---

## Mini Exercises and the Solutions Section

### Mini exercise cells
- Numbered sequentially across the whole notebook: EJERCICIO 1, 2, 3...
- Always says `(opcional, para despues)`
- Always ends with `Solucion al final del notebook.`
- Never assigns `None` to anything; never referenced by a later cell
- Never retrains the model or reloads the base model in the main flow (T4 memory)

### The solutions section
The last content section before the close, titled `## Soluciones de los mini ejercicios`.
One subsection per exercise, in order: the exercise in one line, a complete runnable
commented implementation, one or two sentences on why it works.

---

## Workflow Summary

1. Read all context files, starting with `plans/DECISIONS.md`
2. Show plan summary, wait for approval
3. If the notebook does not exist, create it from the skeleton with the header and one
   section markdown cell per beat plus the solutions section. Otherwise insert this beat's
   cells into its section. Never overwrite the file
4. Build the beat 5 cells at a time: validate, save-state at every 10, ask, repeat
5. Add the mini-exercise solutions to the end section
6. Final validation:
   - `.venv/bin/python3 validate_notebooks.py <notebook> --type exercise`
   - The notebook runs top to bottom on a Colab T4 with no cell requiring anyone to fill
     anything in
   - File size reasonable (under 500 KB, no saved outputs with images of weights)

---

## Checklist (complete before marking done)

- [ ] Section title has emoji, learning objectives clear
- [ ] **Everything attendee-facing in fully Rioplatense Spanish with voseo**
- [ ] Code identifiers in English, no half-translated cells
- [ ] **NOTHING BLOCKS**: every cell runs as written, no `None  # TU CODIGO`
- [ ] Every slow cell has a marked, non-blocking fallback
- [ ] Mini exercises comment-only, additive, `(opcional, para despues)`, with solutions
- [ ] Colab setup: pinned pip install, GPU check, keys via `getpass`
- [ ] Fits a free T4: no bf16, VRAM budget respected, no duplicate model loads
- [ ] Every concept has problem intro, diagram marker + render cell, full demo
- [ ] **Demo code heavily commented**, NARRAR / PARA CASA markers
- [ ] First person plural tone throughout
- [ ] Wrap-up cell connects to the next beat
- [ ] AI-tells scan passed (no em dashes, en dashes, `---` separators, Unicode multiplication)
- [ ] Validation passes

---

## Notebook Edit Protocol (MANDATORY)

Before any cell edit, insert, or delete, follow `~/.claude/NOTEBOOK_EDIT_PROTOCOL.md`:

- Normalize cell ids first (`nbformat.normalize`) so every cell has an id.
- `NotebookEdit` only if the notebook fits the Read limit (~25k tokens); otherwise a
  targeted, audited in-place JSON edit.
- Locate every cell by id AND by asserting its current content.
- Control insert position explicitly; never trust append/insert order.
- After every edit: read back from disk and assert the cell content.
- Run the structural gate (`nbformat.validate`) and the static code gate (`ast.parse` +
  `pyflakes` on all code cells concatenated in order).

Blind bulk scripts that rewrite cells by index are forbidden.
