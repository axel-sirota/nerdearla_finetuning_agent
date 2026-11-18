# Fine-tuning a Small LLM as an Agent Tool

Workshop materials for Nerdearla. One Jupyter notebook, 60 minutes, demoed live.

We fine-tune a small LLM with QLoRA on a free Colab T4, self-host it, and build an agent that
calls it as a tool when that makes sense. A specialized model, cheap and private, instead of
sending everything to a large API.

## Agenda

| Beat | Min |
|---|---|
| The problem: why not send everything to a large API | 7 |
| Lab 1: PEFT live, LoRA/QLoRA on a small model on a Colab T4 | 15 |
| Lab 2: Self-hosting, from a ~100 MB adapter to a served model | 13 |
| Lab 3: The agent uses our model as a tool | 15 |
| When to fine-tune vs prompt: cost, privacy, template | 6 |
| Q&A | 4 |

## Attendees

Open the notebook in Google Colab and switch the runtime to a T4 GPU. Everything installs
from the first cell. Keys are requested with `getpass`, so nothing is stored or shown on
screen. Every cell runs as written, so you can follow along or just watch. Mini exercises
are optional; their solutions are in the last section.

## Contents

| Path | What |
|---|---|
| `CLAUDE.md` | Rules for building the notebook: language, style, conventions |
| `plans/` | Decisions, research plans (gitignored) |
| `diagrams/` | Mermaid sources, fetched by the notebook at talk time |
| `reference/estilo_concierge.ipynb` | Previous workshop's notebook, style reference only |
| `validate_notebooks.py` | Notebook gates: syntax, blocking placeholders, keys, T4 safety, diagrams |
| `.claude/commands/` | Slash commands that research, build and validate the notebook |

## Build workflow

```
/init-workshop        # one-time interview: writes plans/DECISIONS.md
/research-demos N     # 5-cycle research, writes plans/subagents/N_agentdemo.md
/build-notebook N     # adds that beat's cells, 5 at a time, with approval
/build-diagrams N     # writes the Mermaid sources
/validate-notebooks   # gates before the talk
```

## Local setup (for building the workshop, not for attendees)

```bash
python -m venv .venv
.venv/bin/python3 -m pip install -r requirements.txt
```

Python version pinned in `.tool-versions` (asdf). The local venv is for tooling and import
checks; training and serving are verified on a Colab T4.
