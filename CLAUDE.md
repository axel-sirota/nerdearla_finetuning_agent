# CLAUDE.md

Guidance for Claude Code working in this repository.

## Project Overview

Live workshop by Axel Sirota (Data Trainers LLC) for Nerdearla: **fine-tune a small LLM with
QLoRA, self-host it, and give it to an agent as a tool.** 60 minutes, demoed live, step by
step, in front of an audience.

The deliverable is **one Jupyter notebook**, which is the whole artifact. No separate
exercise/solution notebook pair.

**`plans/DECISIONS.md` is the source of truth.** It holds Axel's decisions from the
`/init-workshop` interview. Read it before any work. Where this file and that file disagree,
that file wins. If it does not exist yet, run `/init-workshop` first.

This repo was cloned in process and style from `~/repos/nerdearla_concierge_agent`.
`reference/estilo_concierge.ipynb` is that workshop's finished notebook, kept **read-only as
a style reference**: comment density, voseo, the NARRAR / PARA CASA markers, the QR and
Data Trainers cells, the mini-exercise and solutions pattern. Never copy its content.

**Central pitch** (from the talk abstract):

> Le pagas a una API gigante para una tarea chica, repetitiva y siempre igual? Hay otra
> opcion: entrenar un modelo chico, tuyo y experto en ESO, y hostearlo vos.

A specialized model, cheap and private, that the agent calls when it makes sense, instead of
sending everything out.

## Language Rule (CRITICAL)

- **Notebook content is in fully Rioplatense Spanish with voseo** ("fijate", "arma", "vos",
  "acordate"), as Axel speaks. This covers every markdown cell, every code comment, every
  printed string, every exercise instruction.
- **Code identifiers stay in English** (`base_model`, `train_dataset`, `lora_config`).
- **Conversation with Axel is in English.** Plans, chat summaries, approval questions,
  commit messages: English.
- Never mix: a markdown cell is fully Spanish, never half-translated.

## Workshop Structure

The agenda, 60 minutes total. Full detail goes in `plans/DECISIONS.md` once written.

| # | Beat | Min |
|---|---|---|
| 1 | El problema: por que no mandar TODO a una API gigante | 7 |
| 2 | Lab 1, PEFT en vivo: LoRA/QLoRA sobre un modelo chico en Colab T4 | 15 |
| 3 | Lab 2, Self-hosting: del adapter (~100 MB) al modelo servido (Ollama/vLLM) | 13 |
| 4 | Lab 3, El agente: exponemos tu modelo como herramienta y que lo use cuando conviene | 15 |
| 5 | Cuando fine-tunear vs solo promptear: costos, privacidad y template | 6 |
| 6 | Q&A | 4 |

What attendees take home:

1. A notebook that fine-tunes an LLM with QLoRA and leaves a small adapter (MB, not GB)
2. Their expert model, self-hosted and served, without depending on an external API
3. An agent that uses it as a tool, plus the judgment of when fine-tuning is worth it

Timing is tight, but **there is no cell budget**. Cell count is a poor proxy for a demo-led
notebook. The real constraint is minutes of narration: check it by reading the notebook aloud.

## Stack (NOT YET VERIFIED)

To be locked by `/init-workshop` and verified by running imports in `.venv`, exactly as the
concierge stack was. Nothing here is trusted from memory. Candidates only:

- **Fine-tuning**: `transformers`, `peft`, `trl` (`SFTTrainer`), `bitsandbytes` (4-bit), `datasets`
- **GPU**: Colab free tier, T4 (16 GB, no bf16). Every choice must fit it
- **Serving**: Ollama or vLLM. Open question: vLLM on a T4 inside Colab is doubtful; Ollama
  with a merged GGUF is the likely path. Verify before planning
- **Agent**: LangChain/LangGraph `create_agent`, with the served model wrapped as a tool.
  Reuse the concierge lessons: `tool(fn, parse_docstring=True)`, `system_prompt=`, never
  `create_react_agent`
- **Base model, task and dataset**: open, decided in `/init-workshop`

## Environment

- **Colab.** Attendees run in Google Colab, so every dependency is `!pip install -q` in the
  notebook itself. No local setup, no Docker, no cloud accounts.
- **Keys via `getpass`** in the setup cell (HF token, and an OpenAI key if the agent's
  orchestrator uses one). `getpass` masks the input, so nothing shows on Axel's screen share
  or in the saved notebook. Never `.env` in the notebook flow.
- **GPU runtime required.** The setup cell must check for a GPU and fail loudly with a clear
  Spanish message if the attendee forgot to switch the runtime to T4.

## Notebook Conventions

- **One notebook** at the repo root. It is the whole artifact. Name fixed in DECISIONS.
- **Demo-led, not lab-led.** Axel demos and explains as he goes. Attendees take it home.
- **Therefore: heavy, high-quality comments.** Axel narrates from them live, and they carry
  the notebook for whoever runs it later without him. Mark cells `(NARRAR)` or `(PARA CASA)`.
- **CRITICAL: nothing blocks.** Every cell runs top to bottom as written. There are no
  `None  # TU CODIGO` placeholders in the main flow, because a blocked cell breaks the
  notebook for everyone who is only watching.
- **Long steps need a live fallback.** Training is the slow cell. Axel must never wait on
  stage: plan a short demo run plus a pre-trained adapter to load if time is short.
- **Mini exercises are additive**, in their own clearly marked cells, never in the path of
  the next cell.
- **Solutions collected at the end**, in their own section. Not inline.
- Built with the four-beat arc per concept: problem intro, diagram, full demo, then an
  optional mini exercise.
- Diagrams: `<!-- DIAGRAM: ... -->` marker, plus a `mostrar_diagrama("<slug>")` render cell
  (Colab does not render Mermaid), sources in `diagrams/<slug>.mmd`.

## Editing Notebooks

Follow `~/.claude/NOTEBOOK_EDIT_PROTOCOL.md` before any cell edit, insert, or delete.
Normalize cell ids, locate cells by id AND asserted content, read back after every edit,
run the structural and static gates. Blind index-based bulk rewrites are forbidden.

## Python

All Python runs through the virtualenv: `.venv/bin/python3`. All pip through
`.venv/bin/python3 -m pip`. Every installed package goes into `requirements.txt`.
The venv here is only for tooling (validators, nbformat, import checks); the notebook itself
targets Colab with a T4.

## No AI Tells

Notebook markdown is student-facing copy. No em dashes, no en dashes, no bare `---`
separators inside cells, no Unicode multiplication sign. Short declarative sentences,
concrete nouns. Emojis in section headers are welcome; emoji bullets in body copy are not.

## Commands

1. `/init-workshop` interviews Axel and writes `plans/DECISIONS.md`. **Run this first.**
2. `/research-demos <N>` researches one beat and writes its cell-by-cell plan.
3. `/build-notebook <N>` builds that beat's cells, 5 at a time.
4. `/build-diagrams <N>` writes the Mermaid sources.
5. `/validate-notebooks` gates the result.

`/save-state`, `/start-session`, `/resume` and `/read` exist so a compacted context can pick
the build back up exactly where it stopped.
