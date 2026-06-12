# Phi47 Superpowers

Structural code quality linter for Python based on **Integrated Information Theory (IIT 4.0)**.

Measures **Phi (Φ)** — integrated information — on your code's dependency graph. Detects fragmented, AI-generated-style codebases: zombie functions, god functions, low causal cohesion.

Works in **VS Code** and **Cursor**. No cloud required for analysis.

## Features

- Real-time Phi analysis on file save
- Inline diagnostics (P001–P007) in the editor
- Status bar with current file Phi value
- Phi Report webview with color-coded results
- Workspace-wide analysis
- Local execution — your code stays on your machine

## Requirements

Install the Python package (one time):

```bash
pip install phi47-superpowers
```

## Usage

1. Open a `.py` file — analysis runs on save (configurable)
2. `Ctrl+Shift+P` → **Phi47: Analyze Current File**
3. `Ctrl+Shift+P` → **Phi47: Analyze Workspace**
4. `Ctrl+Shift+P` → **Phi47: Show Phi Report**

## Diagnostic codes

| Code | Issue | Severity |
|------|-------|----------|
| P001 | Low system Phi | error / warning |
| P002 | Zombie function | warning |
| P003 | High cyclomatic complexity | error / warning |
| P004 | Low causal density | info |
| P006 | Disconnected class | hint |
| P007 | God function | hint |

## Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `phi47.pythonPath` | auto | Python with `phi47-superpowers` installed |
| `phi47.enableOnSave` | `true` | Analyze on save |
| `phi47.showStatusBar` | `true` | Show Phi in status bar |

## Scientific background

Spectral approximation of IIT 4.0 — O(n³) instead of exact O(2^n).  
Paper and benchmarks: [github.com/wcalmels/phi47-superpowers](https://github.com/wcalmels/phi47-superpowers)

## Resonance integration

Install the **[Resonance](https://github.com/wcalmels/resonance)** extension and Python packages:

```bash
pip install resonance phi47-superpowers
```

**Command:** `Phi47 + Resonance: Generate Module with Quality Pipeline`

1. Resonance generates 4 files in parallel (minimal tokens)
2. Phi47 analyzes structural Phi locally
3. Resonance refines only weak files

Also available: `Ctrl+Shift+P` → **Resonance + Phi47: Generate Module with Quality Pipeline**

## License

MIT — Copyright (c) 2025 wcalmels / TUCH Systems Research Laboratory
