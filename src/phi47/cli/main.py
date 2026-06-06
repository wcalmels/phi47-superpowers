# Copyright (c) 2025 wcalmels -- TUCH Systems Research Laboratory
# SPDX-License-Identifier: MIT
from __future__ import annotations
import json
from pathlib import Path
import click
from phi47.linter.phi_linter import Phi47Linter
from phi47.wrapper.llm_wrapper import Phi47LLMWrapper

@click.group()
@click.version_option('0.1.0', prog_name='phi47')
def cli():
    '''phi47 -- structural code quality layer based on IIT 4.0.'''

@cli.command()
@click.argument('path', default='.')
@click.option('--json', 'as_json', is_flag=True)
@click.option('--quiet', is_flag=True)
def analyze(path, as_json, quiet):
    '''Analyze Phi of a file or directory.'''
    linter = Phi47Linter()
    p = Path(path)
    if p.is_file():
        diags = linter.lint_file(str(p))
        if as_json:
            click.echo(json.dumps([d.to_dict() for d in diags], indent=2))
            return
        phi = next((d.phi_value for d in diags if d.code == 'P001'), 0.65)
        icon = 'G' if phi > 0.6 else 'Y' if phi > 0.3 else 'R'
        click.echo(f'[{icon}] {p.name}  Phi={phi:.3f}  issues={len(diags)}')
        show = diags if not quiet else [d for d in diags if d.severity == 'error']
        for d in show[:10]:
            click.echo(f'  [{d.severity.upper()}] [{d.code}] L{d.line}: {d.message}')
            if not quiet:
                click.echo(f'    -> {d.suggestion}')
    else:
        import numpy as np
        all_d = linter.lint_directory(str(p))
        if as_json:
            click.echo(json.dumps({fp:[d.to_dict() for d in ds] for fp,ds in all_d.items()},indent=2))
            return
        phis = []
        for fp, ds in sorted(all_d.items()):
            phi = next((d.phi_value for d in ds if d.code == 'P001'), 0.65)
            phis.append(phi)
            e = sum(1 for d in ds if d.severity == 'error')
            w = sum(1 for d in ds if d.severity == 'warning')
            icon = 'G' if phi > 0.6 else 'Y' if phi > 0.3 else 'R'
            click.echo(f'  [{icon}] {Path(fp).name}  Phi={phi:.3f}  E={e} W={w}')
        if phis:
            click.echo(f'System Phi = {float(np.mean(phis)):.3f}  ({len(all_d)} files)')
        else:
            click.echo('No issues found.')

@cli.command()
@click.argument('task')
@click.option('--output', '-o', default=None)
@click.option('--backend', '-b', default='claude')
@click.option('--threshold', default=0.5)
def generate(task, output, backend, threshold):
    '''Generate code with Phi analysis.'''
    click.echo(f'Task: {task}  Backend: {backend}')
    w = Phi47LLMWrapper(backend=backend, phi_threshold=threshold)
    r = w.generate(task)
    ok = 'OK' if r['phi_ok'] else '!!'
    click.echo(f'[{ok}] Phi={r[chr(112)+chr(104)+chr(105)]:.3f}  refinements={r[chr(114)+chr(101)+chr(102)+chr(105)+chr(110)+chr(101)+chr(109)+chr(101)+chr(110)+chr(116)+chr(115)]}')
    if output:
        Path(output).write_text(r['code'], encoding='utf-8')
        click.echo(f'Saved: {output}')
    else:
        click.echo(r['code'])

@cli.command()
@click.argument('path', default='.')
def init(path):
    '''Initialize Phi47 in a project.'''
    import stat
    p = Path(path)
    cfg = {'version':'0.1.0','phi_threshold':0.5,'auto_refine':True,'backend':'claude'}
    (p / '.phi47.json').write_text(json.dumps(cfg, indent=2), encoding='utf-8')
    hook = p / '.git' / 'hooks' / 'pre-commit'
    if hook.parent.exists():
        hook.write_text('#!/bin/bash\nphi47 analyze . --quiet || exit 1\n', encoding='utf-8')
        import stat as s
        hook.chmod(hook.stat().st_mode | s.S_IEXEC)
        click.echo('Git hook installed.')
    click.echo('Phi47 initialized! Run: phi47 analyze .')

if __name__ == '__main__':
    cli()
