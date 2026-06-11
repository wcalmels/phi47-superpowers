# Copyright (c) 2025 wcalmels -- TUCH Systems Research Laboratory
# SPDX-License-Identifier: MIT
"""Delegate to Resonance pipeline when both packages are installed."""

from __future__ import annotations


def run_resonance_pipeline(
    description: str,
    output_dir: str = "output/module",
    name: str = "Generated Module",
    requirements: list[str] | None = None,
    style_file: str | None = None,
    phi_threshold: float = 0.5,
    max_refinements: int = 2,
    as_json: bool = False,
    strict: bool = False,
) -> int:
    try:
        from resonance.engine import ProjectSpec
        from resonance.phi47_bridge import print_pipeline_report, run_pipeline
    except ImportError as exc:
        raise RuntimeError(
            "Resonance not installed. Run: pip install -e /path/to/resonance/packages/core"
        ) from exc

    import asyncio
    import json

    spec = ProjectSpec(
        name=name,
        description=description,
        requirements=requirements or [],
        output_dir=output_dir,
    )
    report = asyncio.run(
        run_pipeline(
            spec,
            phi_threshold=phi_threshold,
            max_refinements=max_refinements,
            style_file=style_file,
        )
    )
    if as_json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print_pipeline_report(report)

    if report.system_phi_after < phi_threshold:
        return 2 if strict else 0
    return 0
