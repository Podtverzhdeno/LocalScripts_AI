# VS Code Extension — Quick Test Guide

## Prerequisites

1. **Start API Server**
   ```bash
   cd C:\Users\user\IdeaProjects\Check\LocalScripts_AI
   python api/server.py
   ```
   
   Should see: `INFO: Uvicorn running on http://127.0.0.1:8000`

2. **Install Extension**
   ```bash
   cd extensions/vscode
   npm install
   npm run compile
   ```

## Test Method 1: Development Mode (Recommended)

1. Open `extensions/vscode` folder in VS Code
2. Press `F5` (starts Extension Development Host)
3. In new window, create `test.lua`
4. Test the extension (see test cases below)

## Test Method 2: Install VSIX

1. Package extension:
   ```bash
   npm run package
   ```

2. Install:
   ```bash
   code --install-extension localscript-0.1.0.vsix
   ```

3. Restart VS Code
4. Test in any Lua file

## Test Cases

### ✅ Test 1: Basic Generation

**File:** `test.lua`
```lua
-- write a function to calculate factorial
```

**Steps:**
1. Select the comment line
2. Press `Ctrl+Shift+L`
3. Wait for notification "Generating code..."
4. Code should replace comment

**Expected:**
```lua
function factorial(n)
    if n <= 1 then return 1 end
    return n * factorial(n - 1)
end
```

---

### ✅ Test 2: Multi-line Comment

```lua
-- write a calculator that:
-- - supports +, -, *, /
-- - handles division by zero
```

**Expected:** Calculator function with error handling

---

### ✅ Test 3: Algorithm

```lua
-- implement quicksort for table
```

**Expected:** Quicksort implementation

---

### ✅ Test 4: Completion

**Steps:**
1. Type: `-- write fibonacci function`
2. Press `Ctrl+Space`
3. Should see: "Generate code from comment"
4. Select it → triggers generation

---

### ✅ Test 5: Configuration

**Steps:**
1. `Ctrl+,` → Search "LocalScript"
2. Change `localscript.maxIterations` to `5`
3. Generate code
4. Should use 5 iterations max

---

### ✅ Test 6: Error Handling

**Test API not running:**
1. Stop API server
2. Try to generate code
3. Should see: "Cannot connect to LocalScript API..."

**Test invalid task:**
```lua
-- asdfghjkl
```
Should fail gracefully with error message

---

## Verification Checklist

- [ ] Extension activates on `.lua` file
- [ ] `Ctrl+Shift+L` works
- [ ] Progress notification shows
- [ ] Code replaces selection
- [ ] Success notification appears
- [ ] Completion provider works (`Ctrl+Space`)
- [ ] Settings are respected
- [ ] Error messages are clear
- [ ] Works with multi-line comments
- [ ] Handles API errors gracefully

## Debugging

### Check Extension Logs

1. `Ctrl+Shift+P` → "Developer: Show Logs"
2. Select "Extension Host"
3. Look for "LocalScript extension activated"

### Check API Logs

Terminal running `python api/server.py` should show:
```
INFO: POST /generate
INFO: 200 OK
```

### Common Issues

**Extension not activating:**
- Open a `.lua` file first
- Check "Extension Host" logs

**Command not found:**
- Press `Ctrl+Shift+P` → Type "LocalScript"
- Should see "LocalScript: Generate Code from Comment"

**No code generated:**
- Check API server is running
- Check API URL in settings: `http://127.0.0.1:8000`
- Check API logs for errors

## Performance Benchmarks

- Extension activation: < 100ms
- Simple task (factorial): 2-5s
- Complex task (algorithm): 5-10s
- Timeout default: 60s

## Next Steps After Testing

1. ✅ All tests pass → Ready for use
2. ❌ Tests fail → Check logs, fix issues
3. 🚀 Ready to publish → See `DEVELOPMENT.md`

---

**Status:** Ready for testing
**Last updated:** 2026-04-06
