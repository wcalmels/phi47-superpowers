# Copyright (c) 2025 wcalmels -- TUCH Systems Research Laboratory
# SPDX-License-Identifier: MIT
from __future__ import annotations
import ast, json
from dataclasses import dataclass, asdict
from pathlib import Path
import numpy as np
from phi47.core.phi_calculator import PhiCalculator


@dataclass(frozen=True)
class Diagnostic:
    file:       str
    line:       int
    col:        int
    severity:   str
    code:       str
    message:    str
    phi_value:  float
    suggestion: str

    def to_dict(self): return asdict(self)
    def __str__(self):
        return f"{self.file}:{self.line}:{self.col}: {self.severity} [{self.code}] {self.message}"


class Phi47Linter:
    """Phi-based linter compatible with any LSP editor.

    Example::

        linter = Phi47Linter()
        for d in linter.lint_file("mycode.py"):
            print(d)
    """

    def __init__(self, phi_error=0.3, phi_warning=0.5,
                 complexity_error=15, complexity_warning=10, max_lines=80):
        self.phi_error          = phi_error
        self.phi_warning        = phi_warning
        self.complexity_error   = complexity_error
        self.complexity_warning = complexity_warning
        self.max_lines          = max_lines
        self._calc              = PhiCalculator()

    def lint_file(self, filepath: str) -> list:
        p = Path(filepath)
        try:
            tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
        except SyntaxError as e:
            return [Diagnostic(str(p), e.lineno or 1, 0, "error", "P000",
                                f"Syntax: {e.msg}", 0.0, "Fix syntax first.")]
        except OSError as e:
            return [Diagnostic(str(p), 1, 0, "error", "P000",
                                f"IO: {e}", 0.0, "Check permissions.")]
        funcs  = _extract_functions(tree)
        clss   = _extract_classes(tree)
        matrix = _build_dep_matrix(funcs)
        diags  = []
        diags += self._check_phi(str(p), matrix)
        diags += self._check_funcs(str(p), funcs)
        diags += self._check_cd(str(p), matrix)
        diags += self._check_classes(str(p), clss)
        return sorted(diags, key=lambda d: (d.line, d.code))

    def lint_directory(self, directory: str) -> dict:
        skip = {".venv", "venv", "__pycache__", ".git", "dist", "build"}
        out  = {}
        for f in Path(directory).rglob("*.py"):
            if any(p in skip for p in f.parts): continue
            d = self.lint_file(str(f))
            if d: out[str(f)] = d
        return out

    def lint_to_json(self, path: str) -> str:
        if Path(path).is_dir():
            data = {fp: [d.to_dict() for d in ds]
                    for fp, ds in self.lint_directory(path).items()}
        else:
            data = {path: [d.to_dict() for d in self.lint_file(path)]}
        return json.dumps(data, indent=2)

    def _check_phi(self, fp, matrix):
        if matrix.shape[0] < 2: return []
        phi, _ = self._calc.calculate(matrix)
        if phi < self.phi_error:
            return [Diagnostic(fp, 1, 0, "error", "P001",
                f"System Phi={phi:.3f} critically low (threshold {self.phi_error})",
                phi, "Add connections between functions.")]
        if phi < self.phi_warning:
            return [Diagnostic(fp, 1, 0, "warning", "P001",
                f"System Phi={phi:.3f} below recommended (threshold {self.phi_warning})",
                phi, "Consider increasing causal connections.")]
        return []

    def _check_funcs(self, fp, funcs):
        diags = []
        for name, data in funcs.items():
            calls   = set(data["calls"])
            callers = {n for n, d in funcs.items() if name in d["calls"]}
            cx, ln, lines = data["complexity"], data["lineno"], data["lines"]
            if not calls and not callers and name not in {"main","__init__","__new__"}:
                diags.append(Diagnostic(fp, ln, 0, "warning", "P002",
                    f"Zombie function: '{name}' has no callers and no callees",
                    0.0, f"Connect or remove '{name}'."))
            if cx > self.complexity_error:
                diags.append(Diagnostic(fp, ln, 0, "error", "P003",
                    f"'{name}' complexity={cx} > {self.complexity_error}",
                    0.0, "Decompose into smaller functions."))
            elif cx > self.complexity_warning:
                diags.append(Diagnostic(fp, ln, 0, "warning", "P003",
                    f"'{name}' complexity={cx}", 0.0, "Consider splitting."))
            if lines > self.max_lines:
                diags.append(Diagnostic(fp, ln, 0, "hint", "P007",
                    f"'{name}' is {lines} lines (limit {self.max_lines})",
                    0.0, "Functions over 80 lines often have multiple responsibilities."))
        return diags

    def _check_cd(self, fp, matrix):
        n = matrix.shape[0]
        if n < 3: return []
        cd = float(np.sum(matrix > 0) / (n * (n - 1) + 1e-10))
        if cd < 0.05:
            return [Diagnostic(fp, 1, 0, "info", "P004",
                f"Low causal density={cd:.3f}: modules mostly isolated",
                cd, "Consider a shared utility module.")]
        return []

    def _check_classes(self, fp, classes):
        diags = []
        for name, data in classes.items():
            if not data["bases"] and not data["methods"]:
                diags.append(Diagnostic(fp, data["lineno"], 0, "hint", "P006",
                    f"Class '{name}' has no base class and no methods",
                    0.0, "Consider @dataclass or adding methods."))
        return diags


def _extract_functions(tree):
    funcs = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            calls = []
            for c in ast.walk(node):
                if isinstance(c, ast.Call):
                    if isinstance(c.func, ast.Name): calls.append(c.func.id)
                    elif isinstance(c.func, ast.Attribute): calls.append(c.func.attr)
            cx  = 1 + sum(1 for n in ast.walk(node)
                          if isinstance(n, (ast.If, ast.For, ast.While,
                                            ast.Try, ast.ExceptHandler)))
            end = getattr(node, "end_lineno", node.lineno)
            funcs[node.name] = {"calls": list(set(calls)), "complexity": cx,
                                 "lineno": node.lineno, "lines": end - node.lineno}
    return funcs


def _extract_classes(tree):
    out = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            bases   = [b.id if isinstance(b, ast.Name) else "?" for b in node.bases]
            methods = [n.name for n in ast.walk(node) if isinstance(n, ast.FunctionDef)]
            out[node.name] = {"bases": bases, "methods": methods, "lineno": node.lineno}
    return out


def _build_dep_matrix(funcs):
    names  = list(funcs.keys())
    n      = len(names)
    if n < 2: return np.zeros((2, 2))
    idx    = {name: i for i, name in enumerate(names)}
    matrix = np.zeros((n, n), dtype=float)
    for name, data in funcs.items():
        i = idx[name]
        for c in data["calls"]:
            if c in idx: matrix[i, idx[c]] = 1.0
    return matrix
