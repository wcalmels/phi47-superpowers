"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = __importStar(require("vscode"));
const child_process_1 = require("child_process");
const path = __importStar(require("path"));
const DIAG_COLLECTION = vscode.languages.createDiagnosticCollection('phi47');
let statusBarItem;
function activate(context) {
    console.log('Phi47 extension activated');
    statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
    statusBarItem.command = 'phi47.analyzeFile';
    context.subscriptions.push(statusBarItem);
    context.subscriptions.push(vscode.commands.registerCommand('phi47.analyzeFile', () => {
        const editor = vscode.window.activeTextEditor;
        if (editor?.document.languageId === 'python') {
            analyzeFile(editor.document);
        }
        else {
            vscode.window.showWarningMessage('Phi47: Open a Python file first.');
        }
    }));
    context.subscriptions.push(vscode.commands.registerCommand('phi47.analyzeWorkspace', () => {
        analyzeWorkspace();
    }));
    context.subscriptions.push(vscode.commands.registerCommand('phi47.showReport', () => {
        showReport();
    }));
    context.subscriptions.push(vscode.commands.registerCommand('phi47.resonancePipeline', () => {
        runResonancePipeline();
    }));
    context.subscriptions.push(vscode.workspace.onDidSaveTextDocument(doc => {
        const cfg = vscode.workspace.getConfiguration('phi47');
        if (cfg.get('enableOnSave') && doc.languageId === 'python') {
            analyzeFile(doc);
        }
    }));
    if (vscode.window.activeTextEditor?.document.languageId === 'python') {
        analyzeFile(vscode.window.activeTextEditor.document);
    }
}
function getPythonPath() {
    const configured = vscode.workspace.getConfiguration('phi47').get('pythonPath');
    if (configured?.trim()) {
        return configured.trim();
    }
    return process.platform === 'win32' ? 'py -3' : 'python3';
}
function phi47Command(args) {
    const python = getPythonPath();
    if (python.includes(' ')) {
        return `${python} -m phi47 ${args}`;
    }
    return `"${python}" -m phi47 ${args}`;
}
function handleExecError(stderr, stdout) {
    const output = (stdout + stderr).toLowerCase();
    if (output.includes('modulenotfounderror') || output.includes('no module named')) {
        vscode.window.showErrorMessage('Phi47: Python package not found. Run: pip install phi47-superpowers', 'Copy install command').then(sel => {
            if (sel === 'Copy install command') {
                vscode.env.clipboard.writeText('pip install phi47-superpowers');
            }
        });
        return;
    }
    if (stderr.trim()) {
        showOutputChannel(stdout + stderr);
    }
}
function analyzeFile(doc) {
    const filePath = doc.fileName;
    const cmd = phi47Command(`analyze "${filePath}"`);
    updateStatusBar('$(loading~spin) Phi47...', '');
    (0, child_process_1.exec)(cmd, (err, stdout, stderr) => {
        if (err) {
            handleExecError(stderr, stdout);
            updateStatusBar('$(error) Phi47', 'Analysis failed — see output');
            return;
        }
        const output = stdout + stderr;
        const diagnostics = parseDiagnostics(doc, output);
        DIAG_COLLECTION.set(doc.uri, diagnostics);
        updateStatusBarFromOutput(output, filePath);
        if (diagnostics.length === 0) {
            updateStatusBar('$(check) Phi OK', 'No Phi47 issues found');
        }
    });
}
function analyzeWorkspace() {
    const folders = vscode.workspace.workspaceFolders;
    if (!folders) {
        vscode.window.showWarningMessage('Phi47: No workspace folder open.');
        return;
    }
    const wsPath = folders[0].uri.fsPath;
    const cmd = phi47Command(`analyze "${wsPath}"`);
    vscode.window.withProgress({
        location: vscode.ProgressLocation.Notification,
        title: 'Phi47: Analyzing workspace...',
        cancellable: false
    }, () => new Promise(resolve => {
        (0, child_process_1.exec)(cmd, (err, stdout, stderr) => {
            if (err) {
                handleExecError(stderr, stdout);
                resolve();
                return;
            }
            const lines = (stdout + stderr).split('\n').filter(l => l.trim());
            vscode.window.showInformationMessage(`Phi47: Workspace analysis complete. ${lines.length} line(s) in report.`, 'Show Output').then(sel => {
                if (sel === 'Show Output') {
                    showOutputChannel(stdout + stderr);
                }
            });
            resolve();
        });
    }));
}
function parseDiagnostics(doc, output) {
    const diagnostics = [];
    const pattern = /^(.+):(\d+):(\d+): (error|warning|info|hint) \[(P\d+)\] (.+)$/;
    for (const line of output.split('\n')) {
        const match = line.match(pattern);
        if (!match) {
            continue;
        }
        const [, file, lineStr, colStr, severity, code, message] = match;
        if (!doc.fileName.endsWith(path.basename(file)) &&
            !file.includes(path.basename(doc.fileName))) {
            continue;
        }
        const lineNum = Math.max(0, parseInt(lineStr, 10) - 1);
        const col = Math.max(0, parseInt(colStr, 10));
        const range = new vscode.Range(lineNum, col, lineNum, 999);
        const sev = severity === 'error' ? vscode.DiagnosticSeverity.Error
            : severity === 'warning' ? vscode.DiagnosticSeverity.Warning
                : severity === 'info' ? vscode.DiagnosticSeverity.Information
                    : vscode.DiagnosticSeverity.Hint;
        const diag = new vscode.Diagnostic(range, `[${code}] ${message}`, sev);
        diag.source = 'phi47';
        diag.code = code;
        diagnostics.push(diag);
    }
    return diagnostics;
}
function updateStatusBarFromOutput(output, filePath) {
    const phiMatch = output.match(/Phi=([0-9.]+)/);
    if (!phiMatch) {
        return;
    }
    const phi = parseFloat(phiMatch[1]);
    const cfg = vscode.workspace.getConfiguration('phi47');
    if (!cfg.get('showStatusBar')) {
        statusBarItem.hide();
        return;
    }
    const icon = phi >= 0.5 ? '$(check)' : phi >= 0.3 ? '$(warning)' : '$(error)';
    const color = phi >= 0.5 ? undefined
        : phi >= 0.3 ? new vscode.ThemeColor('statusBarItem.warningBackground')
            : new vscode.ThemeColor('statusBarItem.errorBackground');
    statusBarItem.text = `${icon} Phi=${phi.toFixed(3)}`;
    statusBarItem.tooltip = `Phi47: Phi=${phi.toFixed(3)} for ${path.basename(filePath)}`;
    statusBarItem.backgroundColor = color;
    statusBarItem.show();
}
function updateStatusBar(text, tooltip) {
    statusBarItem.text = text;
    statusBarItem.tooltip = tooltip;
    statusBarItem.show();
}
let outputChannel;
function showOutputChannel(content) {
    if (!outputChannel) {
        outputChannel = vscode.window.createOutputChannel('Phi47');
    }
    outputChannel.clear();
    outputChannel.appendLine(content);
    outputChannel.show();
}
function showReport() {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showWarningMessage('Phi47: Open a file first.');
        return;
    }
    const cmd = phi47Command(`analyze "${editor.document.fileName}" --json`);
    (0, child_process_1.exec)(cmd, (err, stdout, stderr) => {
        if (err) {
            handleExecError(stderr, stdout);
            return;
        }
        try {
            const data = JSON.parse(stdout);
            const panel = vscode.window.createWebviewPanel('phi47Report', 'Phi47 Report', vscode.ViewColumn.Beside, { enableScripts: true });
            panel.webview.html = buildReportHtml(data, editor.document.fileName);
        }
        catch {
            showOutputChannel(stdout + stderr);
        }
    });
}
function buildReportHtml(data, filePath) {
    const name = path.basename(filePath);
    const items = Array.isArray(data) ? data : [];
    const phiEntry = items.find((d) => d.code === 'P001');
    const phi = phiEntry?.phi_value ?? 'N/A';
    const rows = items.map((d) => `
        <tr class="${d.severity}">
            <td>${d.line}</td>
            <td><span class="badge">${d.code}</span></td>
            <td>${d.severity}</td>
            <td>${d.message}</td>
        </tr>`).join('');
    const phiColor = typeof phi === 'number'
        ? (phi >= 0.5 ? '#10b981' : phi >= 0.3 ? '#f59e0b' : '#ef4444')
        : '#888';
    return `<!DOCTYPE html><html><head><style>
        body { font-family: -apple-system, sans-serif; padding: 20px; background: #1e1e1e; color: #ccc; }
        h1   { color: #a78bfa; font-size: 1.4em; }
        .phi { font-size: 2.5em; font-weight: bold; color: ${phiColor}; }
        table { width: 100%; border-collapse: collapse; margin-top: 16px; }
        th    { background: #2d2d2d; padding: 8px; text-align: left; color: #a78bfa; }
        td    { padding: 6px 8px; border-bottom: 1px solid #333; font-size: 0.9em; }
        .error   td { color: #ef4444; }
        .warning td { color: #f59e0b; }
        .info    td { color: #60a5fa; }
        .hint    td { color: #9ca3af; }
        .badge { background: #374151; padding: 2px 6px; border-radius: 4px;
                 font-family: monospace; font-size: 0.85em; color: #a78bfa; }
    </style></head><body>
    <h1>Phi47 Report: ${name}</h1>
    <div class="phi">Phi = ${typeof phi === 'number' ? phi.toFixed(3) : phi}</div>
    <p>${items.length} diagnostic(s) found</p>
    <table>
        <tr><th>Line</th><th>Code</th><th>Severity</th><th>Message</th></tr>
        ${rows || '<tr><td colspan="4" style="color:#10b981">No issues found</td></tr>'}
    </table>
    </body></html>`;
}
async function runResonancePipeline() {
    const description = await vscode.window.showInputBox({
        prompt: 'Module description (Resonance generates, Phi47 validates)',
        placeHolder: 'e.g. User auth JWT — register, login, me endpoint'
    });
    if (!description)
        return;
    const folders = vscode.workspace.workspaceFolders;
    if (!folders) {
        vscode.window.showWarningMessage('Phi47: Open a workspace first.');
        return;
    }
    const slug = description.split(' ').slice(0, 3).join('_').toLowerCase();
    const outputDir = path.join(folders[0].uri.fsPath, 'output', slug);
    const threshold = vscode.workspace.getConfiguration('phi47').get('phiWarningThreshold', 0.5);
    const args = [
        'pipeline',
        `--description "${description.replace(/"/g, '\\"')}"`,
        `--output-dir "${outputDir}"`,
        `--phi-threshold ${threshold}`
    ].join(' ');
    await vscode.window.withProgress({
        location: vscode.ProgressLocation.Notification,
        title: 'Phi47 + Resonance: quality pipeline...',
        cancellable: false
    }, () => new Promise((resolve) => {
        const cmd = buildResonanceCommand(args);
        (0, child_process_1.exec)(cmd, {
            timeout: 300000,
            env: process.env,
            cwd: folders[0].uri.fsPath,
            maxBuffer: 10 * 1024 * 1024,
        }, (err, stdout, stderr) => {
            if (err) {
                const out = (stdout + stderr).toLowerCase();
                if (out.includes('modulenotfounderror') || out.includes('no module named')) {
                    vscode.window.showErrorMessage('Install: pip install resonance phi47-superpowers', 'Copy command').then(sel => {
                        if (sel === 'Copy command') {
                            vscode.env.clipboard.writeText('pip install resonance phi47-superpowers');
                        }
                    });
                }
                else {
                    vscode.window.showErrorMessage(`Pipeline failed: ${stderr || err.message}`);
                }
                resolve();
                return;
            }
            const phiMatch = stdout.match(/System Phi:\s+([0-9.]+)\s*->\s*([0-9.]+)/);
            const msg = phiMatch
                ? `Pipeline done. Phi ${phiMatch[1]} → ${phiMatch[2]}`
                : 'Pipeline complete';
            vscode.window.showInformationMessage(`${msg}. Output: ${outputDir}`, 'Analyze').then(sel => {
                if (sel === 'Analyze') {
                    (0, child_process_1.exec)(phi47Command(`analyze "${outputDir}"`), () => { });
                }
            });
            resolve();
        });
    }));
}
function buildResonanceCommand(args) {
    const python = getPythonPath();
    const body = `-m resonance ${args}`;
    return python.includes(' ') ? `${python} ${body}` : `"${python}" ${body}`;
}
function deactivate() {
    DIAG_COLLECTION.dispose();
}
//# sourceMappingURL=extension.js.map