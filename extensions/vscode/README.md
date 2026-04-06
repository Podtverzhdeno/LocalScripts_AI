# LocalScript VS Code Extension

AI-powered Lua code generation directly in your editor. Select a comment, press **Ctrl+Shift+L**, get working code.

## Features

### 🚀 Instant Code Generation

Select a comment describing what you want:
```lua
-- write a fibonacci function with memoization
```

Press **Ctrl+Shift+L** (or **Cmd+Shift+L** on Mac), and get:
```lua
local memo = {}
function fibonacci(n)
    if n <= 1 then return n end
    if memo[n] then return memo[n] end
    memo[n] = fibonacci(n-1) + fibonacci(n-2)
    return memo[n]
end
```

### 💡 Smart Completion

Type a comment and get AI suggestions:
```lua
-- parse CSV and sum column|  ← Ctrl+Space shows "Generate code from comment"
```

### ⚙️ Configurable

- **API URL**: Connect to local or remote LocalScript server
- **Max Iterations**: Control generation quality vs speed
- **Sandbox Mode**: Choose security level (lua/docker/none)
- **Timeout**: Adjust for complex tasks

## Installation

### From VSIX (Recommended)

1. Download `localscript-0.1.0.vsix` from releases
2. Open VS Code
3. Press `Ctrl+Shift+P` → "Extensions: Install from VSIX"
4. Select the downloaded file

### From Source

```bash
cd extensions/vscode
npm install
npm run compile
npm run package  # Creates .vsix file
```

## Setup

### 1. Start LocalScript API Server

```bash
cd LocalScripts_AI
python api/server.py
```

Server runs at `http://127.0.0.1:8000`

### 2. Configure Extension (Optional)

Press `Ctrl+,` → Search "LocalScript"

- **API URL**: Default `http://127.0.0.1:8000`
- **Max Iterations**: Default `3`
- **Sandbox Mode**: Default `lua` (safe)
- **Enable Completion**: Default `true`

## Usage

### Method 1: Keyboard Shortcut

1. Write a comment describing your task:
   ```lua
   -- write quicksort algorithm
   ```

2. Select the comment

3. Press **Ctrl+Shift+L** (Windows/Linux) or **Cmd+Shift+L** (Mac)

4. Wait for code generation (progress shown in notification)

5. Generated code replaces the comment

### Method 2: Command Palette

1. Select comment
2. Press `Ctrl+Shift+P`
3. Type "LocalScript: Generate Code"
4. Press Enter

### Method 3: Completion

1. Type a comment:
   ```lua
   -- calculate factorial recursively
   ```

2. Press `Ctrl+Space`

3. Select "Generate code from comment"

## Examples

### Simple Function
```lua
-- write a function to check if number is prime
```
→ Generates prime checking function

### Data Processing
```lua
-- parse JSON string and extract all email addresses
```
→ Generates JSON parser with email extraction

### Algorithm
```lua
-- implement binary search on sorted table
```
→ Generates binary search implementation

### Error Handling
```lua
-- read file with error handling and return content
```
→ Generates safe file reading code

## Configuration

### Settings

Open VS Code settings (`Ctrl+,`) and search for "LocalScript":

```json
{
  "localscript.apiUrl": "http://127.0.0.1:8000",
  "localscript.maxIterations": 3,
  "localscript.timeout": 60,
  "localscript.sandboxMode": "lua",
  "localscript.enableCompletion": true
}
```

### Keyboard Shortcut

Default: `Ctrl+Shift+L` (Windows/Linux), `Cmd+Shift+L` (Mac)

To change:
1. `Ctrl+K Ctrl+S` → Open keyboard shortcuts
2. Search "LocalScript"
3. Click pencil icon → Set new binding

## Troubleshooting

### "Cannot connect to LocalScript API"

**Solution**: Start the API server:
```bash
python api/server.py
```

### "Request timeout"

**Solution**: Increase timeout in settings:
```json
{
  "localscript.timeout": 120
}
```

### "Generation failed"

**Possible causes**:
- Task too vague → Be more specific
- API server error → Check server logs
- Network issue → Check API URL in settings

### Extension not activating

**Solution**: 
1. Open a `.lua` file
2. Extension activates automatically for Lua files

## Development

### Build from Source

```bash
cd extensions/vscode
npm install
npm run compile
```

### Watch Mode

```bash
npm run watch
```

### Package Extension

```bash
npm run package
```

Creates `localscript-0.1.0.vsix`

### Debug

1. Open `extensions/vscode` in VS Code
2. Press `F5` → Opens Extension Development Host
3. Test extension in new window

## Requirements

- VS Code 1.80.0 or higher
- LocalScript API server running
- Lua language support (recommended: [Lua extension](https://marketplace.visualstudio.com/items?itemName=sumneko.lua))

## Links

- [LocalScript GitHub](https://github.com/Podtverzhdeno/LocalScripts_AI)
- [Documentation](https://github.com/Podtverzhdeno/LocalScripts_AI/tree/main/docs)
- [Report Issues](https://github.com/Podtverzhdeno/LocalScripts_AI/issues)

## License

MIT License - see [LICENSE](../../LICENSE)

---

**Made with ⚡ by LocalScript**
