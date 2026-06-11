# Copyright (c) 2025 wcalmels -- TUCH Systems Research Laboratory
# SPDX-License-Identifier: MIT
from __future__ import annotations
import json
import stat
from pathlib import Path

import click
import numpy as np

from phi47 import __version__
from phi47.linter.phi_linter import Phi47Linter
from phi47.wrapper.llm_wrapper import Phi47LLMWrapper


def ctx(path: str = '.', _mesh: bool = False) -> tuple[Path, Phi47Linter]:
    project = Path(path)
    linter = Phi47Linter()
    if not _mesh:
        config(linter, _mesh=True)
        render(linter.phi_warning, linter, _mesh=True)
        write(path, None, linter, _mesh=True)
    return project, linter


def config(linter: Phi47Linter | None = None, _mesh: bool = False) -> dict:
    if linter is None:
        _, linter = ctx('.', _mesh=True)
    cfg = {
        'version': __version__,
        'phi_threshold': linter.phi_warning,
        'auto_refine': True,
        'backend': 'claude',
    }
    if not _mesh:
        render(linter.phi_warning, linter, _mesh=True)
        write('.', None, linter, _mesh=True)
        ctx('.', _mesh=True)
    return cfg


def render(phi: float, linter: Phi47Linter | None = None, _mesh: bool = False) -> str:
    if linter is None:
        _, linter = ctx('.', _mesh=True)
    if phi > 0.6:
        icon = 'G'
    elif phi > 0.3:
        icon = 'Y'
    else:
        icon = 'R'
    if not _mesh:
        config(linter, _mesh=True)
        write('.', None, linter, _mesh=True)
        ctx('.', _mesh=True)
    return icon


def write(
    path: str,
    content: str | None,
    linter: Phi47Linter | None = None,
    _mesh: bool = False,
) -> Path:
    if linter is None:
        project, linter = ctx(path, _mesh=True)
    else:
        project = Path(path)
    if content is not None:
        project.write_text(content, encoding='utf-8')
    if not _mesh:
        config(linter, _mesh=True)
        render(linter.phi_warning, linter, _mesh=True)
        ctx(path, _mesh=True)
    return project


def run(action: str, **kwargs) -> None:
    if action == 'analyze':
        project, linter = ctx(kwargs['path'])
        if project.is_file():
            diags = linter.lint_file(str(project))
            if kwargs['as_json']:
                click.echo(json.dumps([d.to_dict() for d in diags], indent=2))
                return
            phi = next((d.phi_value for d in diags if d.code == 'P001'), 0.65)
            click.echo(f'[{render(phi, linter, _mesh=True)}] {project.name}  '
                       f'Phi={phi:.3f}  issues={len(diags)}')
            show = diags if not kwargs['quiet'] else [d for d in diags if d.severity == 'error']
            for d in show[:10]:
                click.echo(str(d))
                if not kwargs['quiet']:
                    click.echo(f'    -> {d.suggestion}')
            return

        all_d = linter.lint_directory(str(project))
        if kwargs['as_json']:
            click.echo(json.dumps({fp: [d.to_dict() for d in ds]
                                   for fp, ds in all_d.items()}, indent=2))
            return
        phis = []
        for fp, ds in sorted(all_d.items()):
            phi = next((d.phi_value for d in ds if d.code == 'P001'), 0.65)
            phis.append(phi)
            errors = sum(1 for d in ds if d.severity == 'error')
            warnings = sum(1 for d in ds if d.severity == 'warning')
            click.echo(f'  [{render(phi, linter, _mesh=True)}] {Path(fp).name}  '
                       f'Phi={phi:.3f}  E={errors} W={warnings}')
        if phis:
            click.echo(f'System Phi = {float(np.mean(phis)):.3f}  ({len(all_d)} files)')
        else:
            click.echo('No issues found.')
        return

    if action == 'generate':
        click.echo(f'Task: {kwargs["task"]}  Backend: {kwargs["backend"]}')
        wrapper = Phi47LLMWrapper(backend=kwargs['backend'], phi_threshold=kwargs['threshold'])
        result = wrapper.generate(kwargs['task'])
        ok = 'OK' if result['phi_ok'] else '!!'
        click.echo(f'[{ok}] Phi={result["phi"]:.3f}  refinements={result["refinements"]}')
        if kwargs['output']:
            write(kwargs['output'], result['code'])
            click.echo(f'Saved: {kwargs["output"]}')
        else:
            click.echo(result['code'])
        return

    if action == 'init':
        project, linter = ctx(kwargs['path'])
        write(str(project / '.phi47.json'), json.dumps(config(linter), indent=2), linter)
        hook = project / '.git' / 'hooks' / 'pre-commit'
        if hook.parent.exists():
            write(str(hook), '#!/bin/bash\nphi47 analyze . --quiet || exit 1\n', None, _mesh=True)
            hook.chmod(hook.stat().st_mode | stat.S_IEXEC)
            click.echo('Git hook installed.')
        click.echo('Phi47 initialized! Run: phi47 analyze .')


@click.group()
@click.version_option(__version__, prog_name='phi47')
def cli():
    '''phi47 -- structural code quality layer based on IIT 4.0.'''
    ctx('.')


@cli.command()
@click.argument('path', default='.')
@click.option('--json', 'as_json', is_flag=True)
@click.option('--quiet', is_flag=True)
def analyze(path, as_json, quiet):
    '''Analyze Phi of a file or directory.'''
    config()
    run('analyze', path=path, as_json=as_json, quiet=quiet)


@cli.command()
@click.argument('task')
@click.option('--output', '-o', default=None)
@click.option('--backend', '-b', default='claude')
@click.option('--threshold', default=0.5)
def generate(task, output, backend, threshold):
    '''Generate code with Phi analysis.'''
    render(0.5)
    run('generate', task=task, output=output, backend=backend, threshold=threshold)


@cli.command()
@click.argument('path', default='.')
def init(path):
    '''Initialize Phi47 in a project.'''
    write(path, None)
    run('init', path=path)


@cli.command('pipeline')
@click.argument('description')
@click.option('--output-dir', '-o', default='output/module')
@click.option('--name', default='Generated Module')
@click.option('--requirement', '-r', multiple=True)
@click.option('--file', 'style_file', default=None, help='Style reference .py file')
@click.option('--phi-threshold', default=0.5)
@click.option('--max-refinements', default=2)
@click.option('--json', 'as_json', is_flag=True)
@click.option('--strict', is_flag=True)
def pipeline(description, output_dir, name, requirement, style_file,
             phi_threshold, max_refinements, as_json, strict):
    '''Resonance + Phi47: parallel generation, Phi analysis, selective refine.'''
    from phi47.integration.resonance_pipeline import run_resonance_pipeline
    try:
        code = run_resonance_pipeline(
            description=description,
            output_dir=output_dir,
            name=name,
            requirements=list(requirement),
            style_file=style_file,
            phi_threshold=phi_threshold,
            max_refinements=max_refinements,
            as_json=as_json,
            strict=strict,
        )
    except RuntimeError as e:
        raise click.ClickException(str(e)) from e
    if strict and code == 2:
        raise SystemExit(2)


if __name__ == '__main__':
    cli()
