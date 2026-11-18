---
description: Initialize plans/DECISIONS.md by asking questions one at a time about the workshop
---

Initialize the workshop manifest: $ARGUMENTS

This command creates `plans/DECISIONS.md`, the single source of truth that every other
command reads before doing any work. Run this once at the start, or when workshop details
change.

Read `CLAUDE.md` first. It already locks the language rule, the agenda, the Colab + T4
environment, `getpass` for keys, and the notebook conventions, so do not re-ask anything it
answers. This interview fills only what CLAUDE.md leaves open.

---

## Guard

If `plans/DECISIONS.md` already exists, read it first and show the user the current
contents, then ask: "Do you want to update specific sections, or start fresh?"
If updating: only re-ask questions for sections the user wants to change.
If starting fresh: proceed with the full interview below.

---

## Process: One Question at a Time

Ask each question individually. Wait for the answer before asking the next one.
Do NOT dump all questions at once.
After each answer, confirm you understood it before moving on.

Where a question has a technical answer (model fits a T4? Ollama runs in Colab?), propose an
answer backed by evidence: web search AND, where possible, running code in `.venv`. Never
propose from memory alone.

Keep a running draft in memory as answers come in.
After the final question, show the complete draft and ask for approval before writing the file.

---

## Questions (ask in this order)

**Block 1 - The Audience**

Q1: "Who shows up and how many? Same Nerdearla mix as the concierge talk (students, juniors), or a more ML-heavy room?"

Q2: "What do you assume they know? Have they seen transformers/HF before, or is this their first fine-tune? Do they know what an agent is, or do we explain it in two minutes?"

Q3: "Which misconception do you want to kill? Candidates: 'fine-tuning needs a cluster', 'you always need GPT-class models', 'fine-tuning teaches the model new facts'."

**Block 2 - The Case**

Q4: "What is the small, repetitive, always-the-same task the model becomes an expert in? It must be narrow, have an obvious right answer, and show a visible before/after in 15 minutes. (Examples: classify support tickets, extract fields from Argentine invoices to JSON, rewrite text to a fixed format.)"

Q5: "Which dataset? An existing HF dataset, or one we generate? How many examples? Spanish or English data?"

Q6: "Which base model? It must train with QLoRA on a free T4 inside a few minutes and serve on the same T4. Candidates to verify: Qwen2.5-0.5B/1.5B-Instruct, Llama-3.2-1B-Instruct, SmolLM2, Gemma. Gated models need an HF token."

Q7: "Training on stage: how long can the live training cell run? And do we ship a pre-trained adapter on the HF Hub as the fallback the notebook loads if time is short?"

**Block 3 - Serving and the Agent**

Q8: "Serving: Ollama (merge, convert to GGUF, serve) or vLLM (serve the LoRA adapter directly)? Both run in Colab only if verified on a T4. Which one do you want to show, and is the other a mention?"

Q9: "The agent: which model orchestrates it? The fine-tuned model as a tool, called by a bigger model (OpenAI gpt-4o-mini, on your key)? Or a fully local agent? This decides whether there is an API key at all."

Q10: "How does the agent reach the served model: a plain Python tool calling the HTTP endpoint, or MCP? (The concierge talk taught that MCP is just a tool protocol.)"

Q11: "What makes 'use it when it makes sense' visible? E.g. the agent routes the narrow task to our model and everything else to the big one, and we print which one answered."

**Block 4 - Delivery and Tone**

Q12: "Same delivery as the concierge: demo-led, heavy comments, nothing blocks, mini exercises with solutions at the end? Anything different?"

Q13: "The closing segment (when to fine-tune vs prompt): do you want a cost table with real numbers we measure, and a decision template they take home?"

Q14: "Spanish register: fully Rioplatense with voseo, as before?"

Q15: "Anything else: pacing, what makes this land vs fall flat, the one thing they must leave with?"

---

## After All Answers: Write the File

Show the complete draft in chat and ask for approval.

Once approved, write `plans/DECISIONS.md` with this structure:

```markdown
# Workshop Decisions: Fine-tuning a Small LLM as an Agent Tool
# Nerdearla - 60 minutes, live
# Last updated: <YYYY-MM-DD>
#
# Axel's decisions from the /init-workshop interview.
# Every command reads this file before any work begins.

## The Audience

- **Who attends**: <answer>
- **Expected headcount**: <answer>
- **Experience assumed**: <answer>
- **Misconception to kill**: <answer>
- **Win condition**: <answer>

## The Thesis

<what the talk kills, in order, and the organizing principle that replaces it>

## The Arc

| # | Beat | Format | The point |
|---|---|---|---|

## The Case

- **Task**: <answer>
- **Dataset**: <answer, with size and language>
- **Base model**: <answer, with VRAM and training time measured or sourced>
- **Live training budget and fallback adapter**: <answer>

## Serving and the Agent

- **Serving**: <Ollama / vLLM, and why, with evidence it runs on a T4 in Colab>
- **Orchestrator model**: <answer>
- **How the agent reaches our model**: <plain tool / MCP>
- **Routing that makes "when it makes sense" visible**: <answer>

## Environment

- Colab free tier, T4 GPU, everything installs from the first cell
- Keys via getpass: <which keys>

## Delivery

- Demo-led, heavy comments, nothing blocks, mini exercises additive, solutions at the end
- <any differences>

## Tone and Language

- <register>

## Diagrams

| # | Where | Type | Shows |
|---|---|---|---|

## Stack (verified)

| Piece | Import | Version |
|---|---|---|

## No Cell Budget

Timing is checked by reading the notebook aloud, not by counting cells.

## Open Items
```

---

## Confirm

After writing, say:

> `plans/DECISIONS.md` written.
>
> Next: `/research-demos 1` to plan the first beat.

---

## Notebook Edit Protocol (awareness)

If this skill ends up editing notebook cells (not just reading them), follow the canonical
procedure in `~/.claude/NOTEBOOK_EDIT_PROTOCOL.md`: normalize cell ids, size-gate the
mechanism, locate cells by id + content, read back and assert after every edit, and run the
structural + static code gates. Blind bulk index-based rewrites are forbidden.
