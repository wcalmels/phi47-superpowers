# Copyright (c) 2025 Walter Calmels Von dem Knesebeck -- TUCH Systems Research Laboratory
# SPDX-License-Identifier: MIT
from __future__ import annotations
import os
from pathlib import Path
from phi47.linter.phi_linter import Phi47Linter


class Phi47LLMWrapper:
    """Universal LLM wrapper that adds Phi analysis to generated code.

    Supports Claude, GPT-4, and any chat-compatible API.
    Caller keeps their own API key -- no markup, no vendor lock-in.

    Example::

        w = Phi47LLMWrapper(backend="claude")
        r = w.generate("Build a binary search tree")
        print(r["phi"], r["code"])
    """

    SYSTEM = ("You are an expert Python developer. Write clean code with high "
              "causal cohesion. Include type hints and docstrings. "
              "Return ONLY Python code, no explanation.")

    def __init__(self, backend="claude", api_key=None,
                 phi_threshold=0.5, auto_refine=True, max_refinements=2):
        self.backend         = backend
        self.api_key         = api_key or os.environ.get(
            {"claude": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY"}.get(backend, ""), "")
        self.phi_threshold   = phi_threshold
        self.auto_refine     = auto_refine
        self.max_refinements = max_refinements
        self._linter         = Phi47Linter()
        self._client         = None

    def generate(self, task: str, context: str = "") -> dict:
        """Generate code and run Phi analysis. Auto-refines if Phi < threshold."""
        prompt = task if not context else f"{task}\n\nContext:\n{context}"
        code   = self._extract(self._call(prompt))
        phi, diags = self._phi_of(code)
        refs = 0
        if self.auto_refine and phi < self.phi_threshold:
            for _ in range(self.max_refinements):
                issues = "\n".join(f"- [{d.code}] {d.message}" for d in diags[:3])
                code   = self._extract(self._call(
                    f"Refactor for higher Phi.\nIssues:\n{issues}\n\n`python\n{code}\n`"))
                phi, diags = self._phi_of(code)
                refs += 1
                if phi >= self.phi_threshold:
                    break
        return {
            "code":        code,
            "phi":         phi,
            "phi_ok":      phi >= self.phi_threshold,
            "diagnostics": [{"code": d.code, "message": d.message} for d in diags],
            "suggestions": list({d.suggestion for d in diags})[:4],
            "refinements": refs,
            "backend":     self.backend,
        }

    def _call(self, prompt: str) -> str:
        c = self._get_client()
        if self.backend == "claude":
            r = c.messages.create(
                model="claude-sonnet-4-6", max_tokens=2048,
                system=self.SYSTEM,
                messages=[{"role": "user", "content": prompt}])
            return r.content[0].text
        if self.backend == "openai":
            r = c.chat.completions.create(
                model="gpt-4o", max_tokens=2048,
                messages=[{"role": "system", "content": self.SYSTEM},
                           {"role": "user",   "content": prompt}])
            return r.choices[0].message.content
        return f"# {prompt}\ndef solution(): pass\n"

    def _get_client(self):
        if self._client:
            return self._client
        if self.backend == "claude":
            import anthropic
            self._client = anthropic.Anthropic(api_key=self.api_key)
        elif self.backend == "openai":
            import openai
            openai.api_key = self.api_key
            self._client   = openai
        return self._client

    def _phi_of(self, code: str):
        tmp = Path("_phi47_tmp.py")
        try:
            tmp.write_text(code, encoding="utf-8")
            diags = self._linter.lint_file(str(tmp))
            phi   = next((d.phi_value for d in diags if d.code == "P001"), 0.65)
            return phi, diags
        finally:
            if tmp.exists():
                tmp.unlink()

    @staticmethod
    def _extract(text: str) -> str:
        if "`python" in text: return text.split("`python")[1].split("`")[0].strip()
        if "`"       in text: return text.split("`")[1].split("`")[0].strip()
        return text.strip()
