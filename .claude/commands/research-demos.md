---
description: Research one workshop demo and produce a cell-by-cell plan at plans/subagents/<N>_agentdemo.md that /build-notebook can consume directly
---

Research and plan demo: $ARGUMENTS

(Argument is a beat number, 1 to 5. See the table below.)

## GUARD: Read Workshop Manifest First

Before doing anything else, check for the workshop manifest:

```bash
ls plans/DECISIONS.md 2>/dev/null
```

If it does NOT exist, stop immediately and say:

> `plans/DECISIONS.md` not found. Run `/init-workshop` first. Every research-demos run requires it before proceeding.

If it exists, read it fully along with `CLAUDE.md` and keep both in mind throughout.

---

This command is the **natural precursor to `/build-notebook`**. Its only job is to produce a
plan file at `plans/subagents/<N>_agentdemo.md` so that `/build-notebook <N>` can build that
beat's section of the notebook cell by cell from it.

**This command does NOT create any `.ipynb` notebooks.** It produces markdown only.

**Web research is MANDATORY.**

Run the research DISCIPLINE, not a particular tool. Per cycle: state a hypothesis, gather
evidence, attack it with an antithesis, then refine. What is graded is the evidence trail,
not which tool produced it.

**Evidence ranking, strongest first:**
1. **Running the code** in `.venv/bin/python3` against the installed packages. Signatures,
   defaults and failure modes verified empirically beat any document. GPU-only steps
   (training, 4-bit loading, serving) cannot run on the Mac: verify their signatures locally
   and their behavior on a real Colab T4, or say explicitly that they are unverified.
2. Official docs and source for the exact installed version.
3. Current third-party writing, treated as a lead to verify rather than as fact.
4. Recall. **Never sufficient on its own.**

The `Skill` tool may be unavailable in a subagent context. If so, execute the discipline
directly. That is not a deviation and needs no apology; it is the intended fallback. Log each
cycle's hypothesis, evidence operations with URLs or executed snippets, antithesis and
refinement into the plan's `# RESEARCH VALIDATED` block.

## FAILURE DEFINITION

Exactly two outcomes: COMPLETE SUCCESS or COMPLETE FAILURE. No partial credit.

**COMPLETE SUCCESS** = all true:
- All 5 research cycles completed and visible in chat
- Each cycle shows a hypothesis, logged evidence, an antithesis and a refinement
- PRE-WRITE SELF-CHECK printed in chat with all YES answers
- Plan file written to `plans/subagents/<N>_agentdemo.md` with all required sections
- Every cell's Spanish content is drafted in the plan, not left as "write something here"

**COMPLETE FAILURE** = any of:
- Fewer than 5 research cycles
- Any cycle lacks logged evidence, or rests on recall alone where code could have been run
- PRE-WRITE SELF-CHECK not printed, or any field NO at Write time
- Plan file not written, or written with stub/placeholder content
- Any API surface asserted from memory instead of verified against current docs

If COMPLETE FAILURE: report what failed and restart from the beginning. Do not patch a partial result.

---

## Command Arguments

```
/research-demos <beat_number>
```

The beat number maps to the arc in `plans/DECISIONS.md`. Default mapping from the agenda:

| N | Beat | Slug | Min |
|---|---|---|---|
| 1 | El problema: por que no mandar todo a una API gigante | el-problema | 7 |
| 2 | Lab 1: PEFT en vivo, QLoRA en Colab T4 | peft | 15 |
| 3 | Lab 2: Self-hosting, del adapter al modelo servido | self-hosting | 13 |
| 4 | Lab 3: El agente usa nuestro modelo como herramienta | agente | 15 |
| 5 | Cuando fine-tunear vs promptear: costos, privacidad, template | cuando | 6 |

If `plans/DECISIONS.md` defines a different arc, DECISIONS wins.

---

## Output Contract (NON-NEGOTIABLE)

1. **One file only**: `plans/subagents/<N>_agentdemo.md`. Never write anywhere else.
2. **No `.ipynb` files.** No Write calls except to that one plan file.
3. **Plan must be directly executable by `/build-notebook`**: every cell has enough detail
   that the builder does not need to invent content. Spanish cell content is drafted here,
   not deferred to the builder.
4. **Structure** (every section required):
   - `# Beat <N> - <Title> - Cell-by-Cell Plan`
   - `## Context` (what attendees arrive with, by exact variable name, since this is ONE
     notebook and every earlier variable is still in scope; the key insight they leave with)
   - `## Through-Line` (how this beat advances the thesis in DECISIONS)
   - `## STAR Story` (Situation / Task / Action / Result for this beat's scenario)
   - `## Deliverables` (the cells added to the notebook, plus the mini exercises proposed)
   - `## Session Timing (<N> min)` table, matching the agenda slot exactly
   - `## Live Risk and Fallback` (what can be slow or fail on a T4 on stage, and the cell
     that rescues it without blocking anyone)
   - `# CELL-BY-CELL CONTENT (Target: <N> cells)`
   - Each cell: `## Cell N - Markdown/Code: Description` with full Spanish content in a
     fenced block
   - `## Diagram Index` (slug, path `diagrams/<slug>.mmd`, description per diagram)
   - `# VERIFICATION CHECKLIST`
   - `# RESEARCH VALIDATED (Month Year)`

### Contract rule (if plans/CONTRACT.md exists, read it FIRST)

If `plans/CONTRACT.md` exists it is FROZEN. Every class name, function signature, variable
name and return shape is fixed there. Research subagents may run in parallel and cannot see
each other's output, so they MUST conform to it verbatim. If a plan genuinely cannot be
written within the contract, add a `## CONTRACT CONFLICT` section describing the conflict,
then continue with the contract as written. Do not edit the contract.

### Continuity rule (this is ONE notebook)

Open any already-built sections of the notebook and list the exact variables, model objects,
paths and endpoints already in scope. For every planned cell that reuses one, add a line:

- `Reuses: <exact variable name> from Cell <M>`

Never redefine a name that already exists. Never re-teach a concept already covered. Never
reload a model that is already in GPU memory: on a T4 that is an out-of-memory error.

### Writing the Plan File in Batches

If the plan will exceed ~150 lines, write the header + timing first, then append
cell-by-cell content in ~50-line chunks with Edit, then append the checklist + research block.

---

## Pre-Work: MANDATORY Reading

1. `CLAUDE.md`
2. `plans/DECISIONS.md`
3. `plans/OUTLINE.md` and `plans/CONTRACT.md`, if they exist
4. `.claude/commands/build-notebook.md`, the consumer of your plan
5. `plans/subagents/<N-1>_agentdemo.md`, the previous beat's plan, for the bridge
6. The already-built sections of the notebook
7. `reference/estilo_concierge.ipynb`, skimmed for comment density and tone only

---

## MANDATORY CYCLE TRACKER

Post this at the start of research and update after each cycle. Do NOT write the plan file
until all 5 boxes are `[x]` AND all show `evidence logged: YES`.

```
CYCLE TRACKER
[_] Cycle 1 - Agenda Alignment and Notebook Continuity          evidence logged: NO
[_] Cycle 2 - API Surface, Dependencies and the T4 Budget        evidence logged: NO
[_] Cycle 3 - Pedagogical Structure (Problem -> Diagram -> Demo) evidence logged: NO
[_] Cycle 4 - Comment Quality, the Clock and Live Fallbacks     evidence logged: NO
[_] Cycle 5 - Through-Line, Timing, Take-Homes                   evidence logged: NO
```

---

## Process: 5 TDD-Style Research Cycles

### Cycle 1 - Arc Alignment and Notebook Continuity
- Confirm this beat's scope against the arc in `plans/DECISIONS.md`.
- **Invoke `/research`**: current best practice for this beat's core concept as of today.
- **Refutation**: variable-name collision with earlier sections? Re-teaching something
  already covered? Does this beat need its full slot, or is it padded?

### Cycle 2 - API Surface, Dependencies and the T4 Budget
- Lock the `!pip install -q` line, pinned to versions verified together.
- **Verify every import path and signature against current docs and the installed package.
  This stack drifts fast.** Specifically, as relevant to the beat:
  - `BitsAndBytesConfig` 4-bit NF4 settings, and the compute dtype on a T4 (no bf16: fp16)
  - `LoraConfig` fields and `target_modules` for the chosen base model
  - `prepare_model_for_kbit_training`, `get_peft_model`, `print_trainable_parameters`
  - `SFTTrainer` / `SFTConfig` from `trl` for the pinned version (arguments move between
    releases), and the chat template / formatting function
  - Adapter save size on disk, and `merge_and_unload` for serving
  - Serving: the exact commands to run Ollama or vLLM inside Colab, start in the
    background, and hit its OpenAI-compatible endpoint
  - Agent: `create_agent` from `langchain.agents`, `tool(fn, parse_docstring=True)`
- **VRAM and wall-clock budget**: base model in 4-bit + LoRA + batch + seq length must fit
  15 GB, and the live training cell must finish inside the slot. Cite measurements.
- **Refutation**: deprecated argument? Version conflict between transformers / peft / trl /
  bitsandbytes and Colab's preinstalled torch? Does it actually run on a T4?

### Cycle 3 - Pedagogical Structure (Problem -> Diagram -> Demo)
- For EACH concept (2-4 per beat), plan cells following the four-beat arc:
  - **Problem** markdown + naive code that runs and shows the problem
  - **Diagram**: `<!-- DIAGRAM: ... -->` marker, then a `mostrar_diagrama("<slug>")` cell
  - **Demo** code: complete, runnable, **heavily commented** in Rioplatense Spanish
  - **Mini exercise** (optional): a comment-only cell, additive, nothing downstream reads it
- **NOTHING BLOCKS.** No `None  # TU CODIGO` in the main flow.
- Never chain more than 3 markdown cells without a code cell.
- **Invoke `/research`**: common gotchas when doing this demo with these libraries on Colab.
- **Refutation**: would any cell fail for someone who skipped every mini exercise? Is the
  naive cell genuinely broken, or theatrically so?

### Cycle 4 - Comment Quality, the Clock and Live Fallbacks
- **The comments are the script.** Every non-obvious line gets a comment saying WHY.
- Check the beat fits its slot when narrated, not when silently executed. Count the wall
  clock of every slow cell (pip, model download, training, merge, GGUF conversion, server
  start) and plan what Axel says while it runs.
- Plan the fallback for every slow cell (pre-trained adapter on the Hub, pre-built GGUF,
  shorter `max_steps`), clearly marked, never blocking.
- Plan the mini exercises: additive, optional, each with a solution for the end section.
- **Invoke `/research`**: the edge cases that most often eat workshop time for this topic.
- **Refutation**: what is the single most likely thing to go wrong live, and does the plan
  handle it?

### Cycle 5 - Through-Line, Timing, Take-Homes
- State how this beat advances the thesis. Name the one-line bridge into the next beat.
- Verify the timing table sums to this beat's agenda slot.
- Produce the RESEARCH VALIDATED block: every source URL + the specific fact extracted.
- Produce the VERIFICATION CHECKLIST.
- **Refutation**: any unsourced claim? Any signature asserted from memory?

---

## HARD GATE: Pre-Write Self-Check (MANDATORY before any Write call)

```
PRE-WRITE SELF-CHECK
--------------------
Cycle tracker all 5 checked [x]:               YES / NO
All 5 cycles have logged evidence:             YES / NO
Plan path is plans/subagents/<N>_agentdemo.md: YES / NO
No .ipynb files created:                       YES / NO
STAR story section present:                    YES / NO
Through-line section present:                  YES / NO
Live risk and fallback section present:        YES / NO
Continuity: reused variables named per cell:   YES / NO / N-A
Diagram index present with slugs and paths:    YES / NO
Every cell's Spanish content drafted in full:  YES / NO
Every import/signature verified, not recalled: YES / NO
Fits a free Colab T4 (VRAM and time):          YES / NO / N-A
Beat fits its slot when narrated aloud:        YES / NO
Nothing blocks; mini exercises are additive:   YES / NO
RESEARCH VALIDATED block has URLs:             YES / NO
VERIFICATION CHECKLIST present:                YES / NO
AI-tells scan passed (no em/en dashes):        YES / NO
```

---

## Non-Negotiables (Violating Any = Complete Failure, Start Over)

1. Path is always `plans/subagents/<N>_agentdemo.md`.
2. No `.ipynb` files created.
3. All notebook-facing content drafted in Spanish; code identifiers in English.
4. NOTHING BLOCKS: no `None  # TU CODIGO` in the main flow. Mini exercises are additive.
5. Every concept has a Problem cell, a Diagram, and a Demo cell; max 3 markdown cells
   without a code cell.
6. Every import path and signature verified against current docs, not memory.
7. Everything fits a free Colab T4. Nothing needs a paid tier, a cloud account, or Docker.
8. Every slow cell has a non-blocking fallback.
9. Continuity confirmed by opening the actual built notebook sections. This is ONE notebook.
10. STAR story, through-line and live-risk sections all present.
11. All 5 cycles visible, all `[x]`, all `evidence logged: YES` before any Write.
12. PRE-WRITE SELF-CHECK printed with all YES (or N-A where noted) before Write.
13. The beat fits its agenda slot. Cut scope rather than extend the slot.
14. ZERO AI-TELLS in the plan file: no em dashes, no en dashes, no Unicode multiplication.

---

## Workshop Stack Defaults (this repo)

`plans/DECISIONS.md` is authoritative once written. Until then, see CLAUDE.md. Summary:

- **Environment**: Google Colab, free T4, pip install in-notebook, keys via `getpass`.
- **Fine-tuning**: QLoRA with `transformers` + `peft` + `trl` + `bitsandbytes`.
- **Serving**: Ollama or vLLM, decided in DECISIONS, verified on a T4.
- **Agent**: `create_agent` from `langchain.agents`, tools wrapped with
  `tool(fn, parse_docstring=True)`, `system_prompt=` param.
- **Diagrams**: rendered by `mostrar_diagrama(slug)` from `diagrams/<slug>.mmd` on GitHub.
- **Placeholders**: none in the main flow. Mini exercises are comment-only.

---

## Handoff

Once the plan file is written, end with:

> Plan written to `plans/subagents/<N>_agentdemo.md`.
>
> Next step: run `/build-notebook <N>` to add this beat's section to the notebook,
> 5 cells at a time with approval between batches.

Do not offer to run `/build-notebook` yourself.

---

## Notebook Edit Protocol (awareness)

This command writes markdown only. If it ever edits notebook cells, follow
`~/.claude/NOTEBOOK_EDIT_PROTOCOL.md`: normalize cell ids, locate cells by id + content, read
back and assert after each edit. Blind bulk index-based rewrites are forbidden.
