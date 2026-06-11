# Phi47 Superpowers Layer

[![CI](https://github.com/wcalmels/phi47-superpowers/actions/workflows/ci.yml/badge.svg)](https://github.com/wcalmels/phi47-superpowers/actions)
[![PyPI](https://img.shields.io/pypi/v/phi47-superpowers)](https://pypi.org/project/phi47-superpowers/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

> Structural code quality layer based on Integrated Information Theory (IIT 4.0).
> Works on top of any editor (VS Code, Cursor, Neovim) or LLM (Claude, GPT-4, Gemini).
> No vendor lock-in. Use your own API keys.

## Install

    pip install phi47-superpowers
    pip install "phi47-superpowers[llm]"

## Quick start

    phi47 analyze mycode.py
    phi47 analyze .
    phi47 generate "Build a REST API" --output api.py
    phi47 init

## Diagnostic codes

| Code | Issue                     | Severity        |
|------|---------------------------|-----------------|
| P001 | Low system Phi            | error / warning |
| P002 | Zombie function           | warning         |
| P003 | High cyclomatic complexity| error / warning |
| P004 | Low causal density        | info            |
| P006 | Disconnected class        | hint            |
| P007 | God function              | hint            |

## Use as a library

    from phi47 import Phi47Linter
    linter = Phi47Linter()
    for d in linter.lint_file("mycode.py"):
        print(d)

## Scientific background

Phi47 applies spectral IIT 4.0 to dependency graphs:
    Phi = H(eigenvalues(C*C^T)) * (1 - e^(-k))
Runs in O(n^3) instead of exact O(2^n).

## License

MIT License -- Copyright (c) 2025 Walter Calmels Von dem Knesebeck
TUCH Systems Research Laboratory
