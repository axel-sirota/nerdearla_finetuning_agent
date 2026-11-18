---
description: Build Mermaid diagram files one by one from a beat's research plan into diagrams/
---

Build diagrams for beat: $ARGUMENTS

(Argument is a beat number. With no argument, build every diagram the notebook references
that has no `.mmd` file yet.)

## GUARD: Read Workshop Manifest First

```bash
ls plans/DECISIONS.md 2>/dev/null
```

If the file does NOT exist, stop and say:

> `plans/DECISIONS.md` not found. Run `/init-workshop` first to record the workshop decisions. Every command requires this file before proceeding.

If it exists, read it fully. Its diagram table is the approved list.

---

This command runs AFTER `/research-demos N` produced the plan and AFTER `/build-notebook N`
built the section with its diagram markers and `mostrar_diagrama("<slug>")` render cells.

---

## Step 1: Read Context

1. `plans/subagents/<N>_agentdemo.md`: the `## Diagram Index` section
2. The notebook cells around each `<!-- DIAGRAM: ... -->` marker

## Step 2: List All Diagrams

```
Diagrams to build for Beat N:
1. <slug>.mmd - <description>
2. <slug>.mmd - <description>

I'll build them one at a time and ask for your approval before moving to the next.
```

**Ask**: "Ready to start with diagram 1? Or any specific order you want?"

## Step 3: Build Each Diagram (One at a Time, Approval Between Each)

### 3a. Design the diagram in chat first

Show the slug, description, the cell it serves, and the proposed Mermaid source.
**Wait for approval before writing the file.**

### 3b. Write the file

`diagrams/<slug>.mmd`, raw Mermaid source only, no fences.

Then render-check it locally the same way the notebook does (base64 to mermaid.ink with
`requests`, expect HTTP 200 and an image). A Mermaid syntax error renders as a broken image
on stage.

### 3c. Confirm the notebook render cell

The cell after the marker must be `mostrar_diagrama("<slug>")` with the exact slug.
Colab does not render Mermaid in markdown, so a marker without that cell shows nothing.

### 3d. Ask before the next diagram

"Diagram `<slug>.mmd` written. Ready for diagram <N+1> (`<next-slug>`)?"

**Do not proceed until the user says yes.**

---

## Diagram Design Rules

- One concept per diagram
- `graph TD` for flows and pipelines, `sequenceDiagram` for request/response,
  `flowchart LR` for decisions
- Max ~10 nodes; split if it needs more
- Node and edge labels in Spanish, short, plain ASCII, no accents that break Mermaid
- No em dashes, no special Unicode

### Good diagram types for this workshop

- API gigante vs modelo chico -> `graph LR`: every request going out to a paid API vs the
  narrow repetitive task staying home on our model
- LoRA -> `graph TD`: frozen base weights, two small matrices A and B trained beside them,
  added at the output. The "100 MB, not 15 GB" picture
- QLoRA -> `graph LR`: base cuantizado a 4 bits, adapter en fp16 encima
- Del adapter al modelo servido -> `graph LR`: adapter + base -> merge -> GGUF -> Ollama ->
  endpoint OpenAI-compatible (or vLLM serving the adapter directly)
- El agente decide -> `sequenceDiagram`: user, agent, our model as a tool, the big model;
  the narrow task routed home, the rest outside
- Cuando fine-tunear -> `flowchart LR`: a decision tree (task narrow? repetitive? data
  available? privacy? volume?) ending in prompt / RAG / fine-tune

## Step 4: Summary

List the files written and whether every render cell matches its slug. Remind that the
files must be pushed to GitHub before `mostrar_diagrama` can fetch them.

---

## Notebook Edit Protocol (MANDATORY)

Before any cell edit, follow `~/.claude/NOTEBOOK_EDIT_PROTOCOL.md`: normalize ids, locate by
id + asserted content, read back after every edit, run the structural and static gates.
Blind bulk index-based rewrites are forbidden.
