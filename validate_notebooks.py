#!/usr/bin/env python3
"""
Notebook validator for the Nerdearla fine-tuning workshop
(QLoRA on a Colab T4, self-hosting, the model as an agent tool).

Implements the spec in .claude/commands/validate-notebooks.md.

Usage
-----
    .venv/bin/python3 validate_notebooks.py <notebook>.ipynb --type exercise

Exit codes
----------
    0   all checks passed
    1   one or more checks failed

Checks (from .claude/commands/validate-notebooks.md)
----------------------------------------------------
    1. Python syntax in every code cell (ast.parse with IPython lines stripped).
    2. Stack is current and T4-safe: no create_react_agent, no bf16 on a T4.
    3. Nothing blocks: no `= None  # TU CODIGO` placeholder anywhere.
    4. Cell 0 is markdown and starts with "# " (title).
    5. `!pip install` appears in the first 5 code cells.
    6. No hardcoded API keys or HF tokens; keys come from getpass, never .env.
    7. A closing section exists before the solutions section.
    8. Every EJERCICIO N has a matching solution at the end.
    9. Every <!-- DIAGRAM --> marker is followed by a mostrar_diagrama() cell.
   10. Cell order: no obvious forward reference (a variable name used in an
       earlier code cell and only *assigned* in a strictly later code cell
       is flagged as a likely forward reference).

There is deliberately NO cell-count gate. The notebook is demo-led with heavy
comments, so cell count is a poor proxy for how long the workshop runs. The real
constraint is minutes of narration, which is checked by reading it aloud.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path

# --------------------------------------------------------------------------
# Patterns
# --------------------------------------------------------------------------
# Executable-code patterns that are wrong for this workshop. Comments may mention them
# (to teach why not), so these are matched with comments stripped.
STACK_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # Deprecated in LangGraph 1.x, prints a warning on screen. Use create_agent.
    (re.compile(r"\bcreate_react_agent\b"),
     "create_react_agent is deprecated, use create_agent from langchain.agents"),
    # The free Colab T4 has no bfloat16 support. Use fp16.
    (re.compile(r"\bbf16\s*=\s*True\b"), "bf16=True does not run on a T4, use fp16"),
    (re.compile(r"torch\.bfloat16"), "torch.bfloat16 does not run on a T4, use torch.float16"),
    # Keys come from getpass, never from a .env file the attendee must upload.
    (re.compile(r"\bload_dotenv\s*\("), "keys come from getpass, not a .env file"),
]

DIAGRAM_MARKER_RE = re.compile(r"<!--\s*DIAGRAM:", re.IGNORECASE)
RENDER_CALL_RE = re.compile(r"\bmostrar_diagrama\s*\(")

YOUR_CODE_RE = re.compile(r"TU\s*CODIGO", re.IGNORECASE)
NONE_PLACEHOLDER_RE = re.compile(r"=\s*None\s*#\s*TU\s*CODIGO", re.IGNORECASE)
WRAP_TOKENS = ("cierre", "conclusion", "que aprendimos", "resumen", "para seguir")


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def cell_src(cell: dict) -> str:
    s = cell.get("source", "")
    return "".join(s) if isinstance(s, list) else s


def strip_ipython(src: str) -> str:
    """Remove IPython magics / shell lines so ast.parse works.

    Also consumes backslash line-continuations after a dropped line so that
    multi-line `!pip install ... \\` blocks don't leave orphan indented
    continuation lines behind.
    """
    out: list[str] = []
    drop_continuation = False
    for line in src.splitlines():
        if drop_continuation:
            # Continuing a previously-dropped ipython line
            drop_continuation = line.rstrip().endswith("\\")
            continue
        stripped = line.lstrip()
        if stripped.startswith(("!", "%", "?")):
            drop_continuation = line.rstrip().endswith("\\")
            continue
        out.append(line)
    return "\n".join(out)


def load_nb(path: Path) -> dict:
    with path.open() as f:
        return json.load(f)


def code_cells(nb: dict) -> list[tuple[int, dict]]:
    return [(i, c) for i, c in enumerate(nb["cells"]) if c["cell_type"] == "code"]


# --------------------------------------------------------------------------
# Individual checks
# --------------------------------------------------------------------------
def check_syntax(nb: dict) -> list[str]:
    errs: list[str] = []
    for i, c in code_cells(nb):
        src = strip_ipython(cell_src(c))
        if not src.strip():
            continue
        try:
            ast.parse(src)
        except SyntaxError as e:
            errs.append(
                f"cell {i}: SyntaxError line {e.lineno} col {e.offset}: {e.msg}"
            )
    return errs


def _strip_comments(src: str) -> str:
    """Drop whole-line and trailing `#` comments.

    The notebook deliberately NAMES the deprecated APIs in comments, to teach that
    they moved. Those mentions are the lesson, not the bug, so deprecation checks
    look at executable code only.
    """
    out = []
    for line in src.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue
        # Drop a trailing comment, but not a `#` inside a string literal.
        if "#" in line and line.count('"') % 2 == 0 and line.count("'") % 2 == 0:
            line = line.split("#", 1)[0]
        out.append(line)
    return "\n".join(out)


def check_stack_current(nb: dict) -> list[str]:
    """Flag deprecated APIs and T4-incompatible settings in executable code.

    Comments mentioning them are fine and expected: naming the trap is the lesson.
    Solution cells are checked too, since they must run on the same T4.
    """
    errs: list[str] = []
    for i, c in code_cells(nb):
        src = _strip_comments(cell_src(c))
        for pat, why in STACK_PATTERNS:
            if pat.search(src):
                errs.append(f"cell {i}: {why}")
    return errs


def check_diagram_render_cells(nb: dict) -> list[str]:
    """Colab does not render Mermaid in markdown, so every marker needs a render cell.

    The next code cell after a <!-- DIAGRAM --> marker must call mostrar_diagrama().
    """
    errs: list[str] = []
    cells = nb["cells"]
    for i, c in enumerate(cells):
        if c["cell_type"] != "markdown" or not DIAGRAM_MARKER_RE.search(cell_src(c)):
            continue
        nxt = next((j for j in range(i + 1, len(cells)) if cells[j]["cell_type"] == "code"), None)
        if nxt is None or not RENDER_CALL_RE.search(cell_src(cells[nxt])):
            errs.append(f"cell {i}: DIAGRAM marker with no mostrar_diagrama() render cell after it")
    return errs


def check_title_cell0(nb: dict) -> list[str]:
    cells = nb["cells"]
    if not cells:
        return ["notebook has zero cells"]
    first = cells[0]
    if first["cell_type"] != "markdown":
        return [f"cell 0 must be markdown (got {first['cell_type']})"]
    text = cell_src(first).lstrip()
    if not text.startswith("# "):
        return [f"cell 0 must start with '# Title' (got: {text[:60]!r})"]
    return []


def check_install_early(nb: dict) -> list[str]:
    for _, c in code_cells(nb)[:5]:
        src = cell_src(c)
        if "!pip install" in src or "%pip install" in src:
            return []
    return ["no !pip install cell in first 5 code cells"]


def check_no_hardcoded_keys(nb: dict) -> list[str]:
    """Keys come from getpass, never hardcoded.

    Guards against a real OpenAI key or HF token being pasted into a cell and then
    committed or projected on stage.
    """
    errs: list[str] = []
    hardcoded = re.compile(
        r"""(sk-[A-Za-z0-9_-]{10,}|hf_[A-Za-z0-9]{20,}|"""
        r"""(api_key|token)\s*=\s*["'][A-Za-z0-9_-]{10,}["'])"""
    )
    for i, c in code_cells(nb):
        if hardcoded.search(cell_src(c)):
            errs.append(
                f"cell {i}: looks like a hardcoded API key or token "
                f"(ask for it with getpass)"
            )
    return errs


SOLUTIONS_RE = re.compile(r"^#{1,3}\s*Soluciones", re.IGNORECASE | re.MULTILINE)


def check_wrap_up(nb: dict) -> list[str]:
    """A closing section must exist.

    The solutions section deliberately sits LAST, after the close, so the final
    cells are solution code rather than the wrap-up. So look for the closing
    section anywhere at or after the solutions heading's predecessor, not only
    in the final three cells.
    """
    cells = nb["cells"]
    split = next(
        (i for i, c in enumerate(cells)
         if c["cell_type"] == "markdown" and SOLUTIONS_RE.search(cell_src(c))),
        None,
    )
    # Search the closing region: before the solutions heading if there is one,
    # otherwise the last 3 cells as before.
    region = cells[max(0, split - 3):split] if split is not None else cells[-3:]
    tail = " ".join(cell_src(c).lower() for c in region)
    if any(tok in tail for tok in WRAP_TOKENS):
        return []
    return [f"no closing section found (expected one of {WRAP_TOKENS})"]


def check_nothing_blocks(nb: dict) -> list[str]:
    """The notebook is demo-led: every cell must run as written.

    A `x = None  # TU CODIGO` placeholder would break the notebook for everyone
    who is only watching, which is most of the room. Mini exercises are
    comment-only and additive instead.
    """
    errs: list[str] = []
    for i, c in code_cells(nb):
        if NONE_PLACEHOLDER_RE.search(cell_src(c)):
            errs.append(
                f"cell {i}: blocking placeholder '= None  # TU CODIGO'. "
                f"Nothing may block; make it a comment-only mini exercise"
            )
    return errs


def check_exercises_have_solutions(nb: dict) -> list[str]:
    """Every EJERCICIO N must have a matching entry in the solutions section."""
    ex_re = re.compile(r"EJERCICIO\s+(\d+)", re.IGNORECASE)
    sol_header = re.compile(r"^#{1,3}\s*Soluciones", re.IGNORECASE | re.MULTILINE)

    cells = nb["cells"]
    split = next(
        (i for i, c in enumerate(cells)
         if c["cell_type"] == "markdown" and sol_header.search(cell_src(c))),
        None,
    )
    if split is None:
        posed = {m for c in cells for m in ex_re.findall(cell_src(c))}
        if posed:
            return ["mini exercises exist but there is no '## Soluciones' section"]
        return []

    posed = {m for c in cells[:split] for m in ex_re.findall(cell_src(c))}
    solved = {m for c in cells[split:] for m in ex_re.findall(cell_src(c))}
    missing = sorted(posed - solved, key=int)
    if missing:
        return [f"mini exercises with no solution at the end: {', '.join(missing)}"]
    return []


def check_no_placeholders_solution(nb: dict) -> list[str]:
    errs: list[str] = []
    for i, c in code_cells(nb):
        src = cell_src(c)
        if NONE_PLACEHOLDER_RE.search(src):
            errs.append(f"cell {i}: solution still has '= None  # TU CODIGO' placeholder")
    return errs


def check_pair_structure(ex: dict, sol: dict) -> list[str]:
    errs: list[str] = []
    ex_cells, sol_cells = ex["cells"], sol["cells"]
    if len(ex_cells) != len(sol_cells):
        errs.append(
            f"pair cell-count mismatch: exercise={len(ex_cells)} vs solution={len(sol_cells)}"
        )
    # Compare cell type sequence up to the shorter length
    m = min(len(ex_cells), len(sol_cells))
    mism: list[int] = []
    for i in range(m):
        if ex_cells[i]["cell_type"] != sol_cells[i]["cell_type"]:
            mism.append(i)
    if mism:
        errs.append(
            f"pair cell-type mismatch at indices (first 5 shown): {mism[:5]}"
        )
    return errs


BUILTIN_NAMES: set[str] = set(dir(__builtins__)) if not isinstance(__builtins__, dict) else set(__builtins__.keys())


class _ModuleScopeScan(ast.NodeVisitor):
    """Collect names *used* and *assigned* at the top-level (module) scope only.

    We deliberately do NOT recurse into function bodies, class bodies, lambdas,
    or comprehensions, since names bound there are local and do not affect
    cell-to-cell dependencies.
    """

    def __init__(self) -> None:
        self.used: set[str] = set()
        self.assigned: set[str] = set()
        self.imported: set[str] = set()

    # ---- scope stoppers -------------------------------------------------
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.assigned.add(node.name)

    visit_AsyncFunctionDef = visit_FunctionDef  # type: ignore[assignment]

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.assigned.add(node.name)
        for deco in node.decorator_list:
            self.visit(deco)
        for base in node.bases:
            self.visit(base)

    def visit_Lambda(self, node: ast.Lambda) -> None:  # noqa: D401
        return None

    def visit_ListComp(self, node: ast.ListComp) -> None:  # noqa: D401
        return None

    visit_SetComp = visit_ListComp  # type: ignore[assignment]
    visit_DictComp = visit_ListComp  # type: ignore[assignment]
    visit_GeneratorExp = visit_ListComp  # type: ignore[assignment]

    # ---- collectors -----------------------------------------------------
    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Load):
            self.used.add(node.id)
        elif isinstance(node.ctx, (ast.Store, ast.Del)):
            # Simple stores at module level
            self.assigned.add(node.id)

    def visit_Assign(self, node: ast.Assign) -> None:
        for t in node.targets:
            if isinstance(t, ast.Name):
                self.assigned.add(t.id)
            elif isinstance(t, (ast.Tuple, ast.List)):
                for elt in t.elts:
                    if isinstance(elt, ast.Name):
                        self.assigned.add(elt.id)
        self.visit(node.value)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        if isinstance(node.target, ast.Name):
            self.assigned.add(node.target.id)
        self.visit(node.value)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if isinstance(node.target, ast.Name):
            self.assigned.add(node.target.id)
        if node.value is not None:
            self.visit(node.value)

    def visit_For(self, node: ast.For) -> None:
        if isinstance(node.target, ast.Name):
            self.assigned.add(node.target.id)
        elif isinstance(node.target, (ast.Tuple, ast.List)):
            for elt in node.target.elts:
                if isinstance(elt, ast.Name):
                    self.assigned.add(elt.id)
        self.visit(node.iter)
        for stmt in node.body:
            self.visit(stmt)
        for stmt in node.orelse:
            self.visit(stmt)

    def visit_With(self, node: ast.With) -> None:
        for item in node.items:
            self.visit(item.context_expr)
            if item.optional_vars is not None and isinstance(item.optional_vars, ast.Name):
                self.assigned.add(item.optional_vars.id)
        for stmt in node.body:
            self.visit(stmt)

    def visit_Import(self, node: ast.Import) -> None:
        for n in node.names:
            self.imported.add((n.asname or n.name).split(".")[0])
            self.assigned.add((n.asname or n.name).split(".")[0])

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for n in node.names:
            name = n.asname or n.name
            self.imported.add(name)
            self.assigned.add(name)


def check_forward_reference(nb: dict) -> list[str]:
    """Flag a NAME used at module scope in code cell i when it is only first
    assigned at module scope in a strictly later code cell j > i.

    Limits false positives by ignoring:
      * names bound inside functions, classes, lambdas, comprehensions,
      * Python builtins,
      * imported names,
      * dunder / private names.
    """
    cc = code_cells(nb)
    if len(cc) < 2:
        return []
    used_per: list[set[str]] = []
    assigned_per: list[set[str]] = []
    imported_all: set[str] = set()
    for _, c in cc:
        src = strip_ipython(cell_src(c))
        try:
            tree = ast.parse(src)
        except SyntaxError:
            used_per.append(set())
            assigned_per.append(set())
            continue
        scan = _ModuleScopeScan()
        for stmt in tree.body:
            scan.visit(stmt)
        used_per.append(scan.used)
        assigned_per.append(scan.assigned)
        imported_all |= scan.imported

    # first-assignment index for every name
    first_assign: dict[str, int] = {}
    for idx, a in enumerate(assigned_per):
        for name in a:
            first_assign.setdefault(name, idx)

    errs: list[str] = []
    seen: set[str] = set()
    for idx, used in enumerate(used_per):
        for name in used:
            if name in BUILTIN_NAMES or name in imported_all or name.startswith("_"):
                continue
            fa = first_assign.get(name)
            if fa is not None and fa > idx:
                cell_idx_of_use = cc[idx][0]
                cell_idx_of_def = cc[fa][0]
                msg = (
                    f"forward-ref: name '{name}' used in cell {cell_idx_of_use} "
                    f"but first assigned in cell {cell_idx_of_def}"
                )
                if msg not in seen:
                    seen.add(msg)
                    errs.append(msg)
    return errs[:15]


# --------------------------------------------------------------------------
# High-level validators
# --------------------------------------------------------------------------
def validate_notebook(path: Path, kind: str = "exercise") -> list[str]:
    """Validate the workshop notebook.

    `kind` is accepted for CLI compatibility but no longer branches: there is one
    notebook, not an exercise/solution pair.
    """
    nb = load_nb(path)
    errs: list[str] = []
    errs += check_title_cell0(nb)
    errs += check_stack_current(nb)
    errs += check_diagram_render_cells(nb)
    errs += check_syntax(nb)
    errs += check_install_early(nb)
    errs += check_no_hardcoded_keys(nb)
    errs += check_wrap_up(nb)
    errs += check_nothing_blocks(nb)
    errs += check_exercises_have_solutions(nb)
    errs += check_forward_reference(nb)
    return errs


def validate_pair(ex_path: Path, sol_path: Path) -> tuple[list[str], list[str], list[str]]:
    ex_errs = validate_notebook(ex_path, "exercise")
    sol_errs = validate_notebook(sol_path, "solution")
    ex_nb, sol_nb = load_nb(ex_path), load_nb(sol_path)
    pair_errs = check_pair_structure(ex_nb, sol_nb)
    return ex_errs, sol_errs, pair_errs


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def _print_result(label: str, path: Path, errs: list[str]) -> None:
    nb = load_nb(path)
    n = len(nb["cells"])
    size_kb = round(path.stat().st_size / 1024, 1)
    status = "PASS" if not errs else "FAIL"
    print(f"\n[{label}] {path}")
    print(f"  cells={n}  size={size_kb} KB  status={status}")
    for e in errs:
        print(f"    - {e}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate course notebooks.")
    ap.add_argument("notebook", nargs="?", help="Path to a single notebook.")
    ap.add_argument(
        "--type",
        choices=("exercise", "solution"),
        help="Kind of notebook when validating a single file.",
    )
    ap.add_argument(
        "--pair",
        nargs=2,
        metavar=("EXERCISE", "SOLUTION"),
        help="Validate an exercise+solution pair together.",
    )
    args = ap.parse_args()

    any_fail = False

    if args.pair:
        ex_path = Path(args.pair[0])
        sol_path = Path(args.pair[1])
        for p in (ex_path, sol_path):
            if not p.exists():
                print(f"MISSING FILE: {p}")
                return 1
        ex_errs, sol_errs, pair_errs = validate_pair(ex_path, sol_path)
        _print_result("EXERCISE", ex_path, ex_errs)
        _print_result("SOLUTION", sol_path, sol_errs)
        if pair_errs:
            print("\n[PAIR] structural consistency  status=FAIL")
            for e in pair_errs:
                print(f"    - {e}")
        else:
            print("\n[PAIR] structural consistency  status=PASS")
        any_fail = bool(ex_errs or sol_errs or pair_errs)
        return 1 if any_fail else 0

    if not args.notebook or not args.type:
        ap.error("provide NOTEBOOK and --type, or use --pair EX SOL")

    path = Path(args.notebook)
    if not path.exists():
        print(f"MISSING FILE: {path}")
        return 1
    errs = validate_notebook(path, args.type)
    _print_result(args.type.upper(), path, errs)
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
