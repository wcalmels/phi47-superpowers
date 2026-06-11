# Publishing to VS Code Marketplace

## Prerequisites

1. **Publisher account**: https://marketplace.visualstudio.com/manage  
   Create publisher `wcalmels` if it does not exist.

2. **Personal Access Token** (Azure DevOps):
   - https://dev.azure.com → User settings → Personal access tokens
   - Scope: **Marketplace** → **Manage**

3. **Node.js** installed locally.

## Build and test

```bash
cd vscode-extension
npm install
npm run compile
npx @vscode/vsce package
```

Install the `.vsix` locally: VS Code → Extensions → `...` → Install from VSIX.

## Publish

```bash
npx @vscode/vsce publish -p <YOUR_PAT>
```

Or login once:

```bash
npx @vscode/vsce login wcalmels
npx @vscode/vsce publish
```

## Open VSX (optional, for VSCodium)

```bash
npx ovsx publish -p <OPEN_VSX_TOKEN>
```

## Checklist before each release

- [ ] `npm run compile` succeeds
- [ ] `npx @vscode/vsce package` produces `.vsix` without errors
- [ ] `CHANGELOG.md` and `package.json` version bumped
- [ ] Test with `pip install phi47-superpowers` on a clean machine
- [ ] Icon displays correctly in Extensions panel
