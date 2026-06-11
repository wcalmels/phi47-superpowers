# Phi47 Superpowers — VS Code Extension

Structural code quality linter based on **Integrated Information Theory (IIT 4.0)**.
Detects zombie functions, low Phi, fragmented codebases, and more.

## Features

- **Real-time Phi analysis** on every file save
- **Status bar** showing current file Phi value
- **Inline diagnostics** (P001-P007) in the editor
- **Phi Report** webview with color-coded results
- **Works with any Python** (your own API keys, no vendor lock-in)

## Requirements

```bash
pip install phi47-superpowers
```

## Usage

- Open a `.py` file — analysis runs automatically on save
- **Ctrl+Shift+P** → `Phi47: Analyze Current File`
- **Ctrl+Shift+P** → `Phi47: Analyze Workspace`
- **Ctrl+Shift+P** → `Phi47: Show Phi Report`

## Diagnostic Codes

| Code | Issue | Severity |
|------|-------|----------|
| P001 | Low system Phi | error/warning |
| P002 | Zombie function | warning |
| P003 | High cyclomatic complexity | error/warning |
| P004 | Low causal density | info |
| P006 | Disconnected class | hint |
| P007 | God function | hint |

## Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `phi47.pythonPath` | `python` | Path to Python executable |
| `phi47.enableOnSave` | `true` | Analyze on save |
| `phi47.phiErrorThreshold` | `0.3` | Error threshold |
| `phi47.phiWarningThreshold` | `0.5` | Warning threshold |
| `phi47.showStatusBar` | `true` | Show Phi in status bar |

## License

MIT — Copyright (c) 2025 wcalmels / TUCH Systems Research Laboratory