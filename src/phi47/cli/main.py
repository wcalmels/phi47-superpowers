# Copyright (c) 2025 Walter Calmels Von dem Knesebeck -- TUCH Systems Research Laboratory
# SPDX-License-Identifier: MIT
from __future__ import annotations
import json
from pathlib import Path
import click
from rich.console import Console
from rich.table   import Table
from phi47.linter.phi_linter   import Phi47Linter
from phi47.wrapper.llm_wrapper import Phi47LLMWrapper

console = Console()


@click.group()
@click.version_option("0.1.0", prog_name="phi47")
def cli():
    """phi47 -- structural code quality layer based on IIT 4.0."""


@cli.command()
@click.argument("path", default=".")
@click.option("--json", "as_json", is_flag=True, help="Output JSON")
@click.option("--quiet", is_flag=True, help="Only show errors")
def analyze(path, as_json, quiet):
    """Analyze Phi of a file or directory."""
    linter = Phi47Linter()
    p = Path(path)
    if p.is_file():
        diags = linter.lint_file(str(p))
        if as_json:
            click.echo(json.dumps([d.to_dict() for d in diags], indent=2))
            return
        phi  = next((d.phi_value for d in diags if d.code == "P001"), 0.65)
        icon = "G" if phi > 0.6 else "Y" if phi > 0.3 else "R"
        console.print(f"[{icon}] {p.name}  Phi={phi:.3f}")
        show = diags if not quiet else [d for d in diags if d.severity == "error"]
        for d in show[:8]:
            c = {"error":"red","warning":"yellow","info":"blue","hint":"dim"}.get(d.severity,"white")
            console.print(f"  [{c}][{d.code}][/{c}] L{d.line}: {d.message}")
            if not quiet:
                console.print(f"    [dim]-> {d.suggestion}[/dim]")
    else:
        all_d = linter.lint_directory(str(p))
        if as_json:
            click.echo(json.dumps(
                {fp: [d.to_dict() for d in ds] for fp, ds in all_d.items()}, indent=2))
            return
        import numpy as np
        t = Table(title=f"Phi47: {p}")
        t.add_column("File", style="cyan")
        t.add_column("Phi",  justify="right")
        t.add_column("E",    justify="right", style="red")
        t.add_column("W",    justify="right", style="yellow")
        phis = []
        for fp, ds in sorted(all_d.items()):
            phi = next((d.phi_value for d in ds if d.code == "P001"), 0.65)
            phis.append(phi)
            e = sum(1 for d in ds if d.severity == "error")
            w = sum(1 for d in ds if d.severity == "warning")
            t.add_row(Path(fp).name, f"{phi:.3f}", str(e), str(w))
        console.print(t)
        if phis:
            console.print(f"System Phi = {float(np.mean(phis)):.3f}")


@cli.command()
@click.argument("task")
@click.option("--output", "-o", default=None)
@click.option("--backend", "-b", default="claude")
@click.option("--threshold", default=0.5)
def generate(task, output, backend, threshold):
    """Generate code with Phi analysis and auto-refinement."""
    console.print(f"[cyan]Task:[/cyan] {task}  [cyan]Backend:[/cyan] {backend}")
    w = Phi47LLMWrapper(backend=backend, phi_threshold=threshold)
    r = w.generate(task)
    ok = "OK" if r["phi_ok"] else "!!"
    console.print(f"[{ok}] Phi={r['phi']:.3f}  refinements={r['refinements']}")
    if output:
        Path(output).write_text(r["code"], encoding="utf-8")
        console.print(f"Saved: {output}")
    else:
        click.echo(r["code"])
    for s in r["suggestions"][:3]:
        console.print(f"  -> {s}")


@cli.command()
@click.argument("path", default=".")
def init(path):
    """Initialize Phi47 in a project."""
    p   = Path(path)
    cfg = {"version": "0.1.0", "phi_threshold": 0.5,
           "auto_refine": True, "backend": "claude"}
    (p / ".phi47.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    hook = p / ".git" / "hooks" / "pre-commit"
    if hook.parent.exists():
        hook.write_text("#!/bin/bash\nphi47 analyze . --quiet || exit 1\n", encoding="utf-8")
        import stat
        hook.chmod(hook.stat().st_mode | stat.S_IEXEC)
        console.print("[green]Git hook installed[/green]")
    console.print("[bold green]Phi47 initialized![/bold green] Run: phi47 analyze .")
