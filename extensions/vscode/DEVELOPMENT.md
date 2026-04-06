# VS Code Extension — Development Guide

## Quick Start

### 1. Install Dependencies

```bash
cd extensions/vscode
npm install
```

### 2. Compile TypeScript

```bash
npm run compile
```

### 3. Test in Development Mode

Press `F5` in VS Code (opens Extension Development Host)

### 4. Package Extension

```bash
npm run package
```

Creates `localscript-0.1.0.vsix`

## Installation

### Install VSIX

```bash
code --install-extension localscript-0.1.0.vsix
```

Or via VS Code UI:
1. `Ctrl+Shift+P` → "Extensions: Install from VSIX"
2. Select `localscript-0.1.0.vsix`

## Testing

### Manual Testing

1. Start LocalScript API:
   ```bash
   cd ../..
   python api/server.py
   ```

2. Open VS Code with extension installed

3. Create test file `test.lua`:
   ```lua
   -- write fibonacci function
   ```

4. Select the comment

5. Press `Ctrl+Shift+L`

6. Verify code is generated

### Test Cases

**Test 1: Simple function**
```lua
-- write a function to calculate factorial
```
Expected: Factorial function generated

**Test 2: Algorithm**
```lua
-- implement bubble sort for table
```
Expected: Bubble sort implementation

**Test 3: Error handling**
```lua
-- read file with error handling
```
Expected: Safe file reading code

**Test 4: Multi-line comment**
```lua
-- write a calculator that:
-- - supports +, -, *, /
-- - handles division by zero
```
Expected: Calculator with error handling

**Test 5: Completion**
1. Type: `-- write quicksort`
2. Press `Ctrl+Space`
3. Expected: Completion suggestion appears

## Configuration Testing

### Test API URL

```json
{
  "localscript.apiUrl": "http://localhost:8000"
}
```

### Test Sandbox Modes

```json
{
  "localscript.sandboxMode": "docker"
}
```

### Test Timeout

```json
{
  "localscript.timeout": 30
}
```

## Debugging

### Enable Extension Logs

1. `Ctrl+Shift+P` → "Developer: Show Logs"
2. Select "Extension Host"
3. Check for LocalScript logs

### Debug TypeScript

1. Open `extensions/vscode` in VS Code
2. Set breakpoints in `src/extension.ts`
3. Press `F5`
4. Trigger command in Extension Development Host
5. Breakpoint hits in main VS Code window

## Common Issues

### "Cannot find module 'axios'"

```bash
npm install
```

### "Command not found"

Extension not activated. Open a `.lua` file first.

### "Cannot connect to API"

Start API server:
```bash
python api/server.py
```

### TypeScript errors

```bash
npm run compile
```

## Publishing (Future)

### Prerequisites

```bash
npm install -g @vscode/vsce
```

### Create Publisher Account

1. Go to https://marketplace.visualstudio.com/manage
2. Create publisher ID
3. Generate Personal Access Token

### Publish

```bash
vsce login <publisher-name>
vsce publish
```

## File Structure

```
extensions/vscode/
├── package.json          # Extension manifest
├── tsconfig.json         # TypeScript config
├── .eslintrc.js          # Linting rules
├── src/
│   └── extension.ts      # Main extension code
├── out/                  # Compiled JS (generated)
│   └── extension.js
└── README.md             # User documentation
```

## Code Overview

### Main Components

**1. Command Registration**
```typescript
vscode.commands.registerCommand('localscript.generateCode', ...)
```

**2. API Client**
```typescript
axios.post(`${apiUrl}/generate`, { task, ... })
```

**3. Code Insertion**
```typescript
editor.edit(editBuilder => {
    editBuilder.replace(selection, code);
})
```

**4. Completion Provider**
```typescript
vscode.languages.registerCompletionItemProvider('lua', ...)
```

## Performance

- Extension activation: ~50ms
- API request: 2-10s (depends on task complexity)
- Code insertion: <10ms

## Security

- No code execution in extension
- All generation happens on API server
- HTTPS support for remote API

## Next Steps

1. Add WebSocket support for real-time progress
2. Add code preview before insertion
3. Add history of generated code
4. Add inline suggestions (like Copilot)
5. Add multi-language support (Python, JavaScript, etc.)

---

**Status:** ✅ Ready for testing
