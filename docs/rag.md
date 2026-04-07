# RAG System Documentation

## Overview

LocalScript uses **RAG (Retrieval-Augmented Generation)** to reduce hallucinations and improve code quality. The system retrieves relevant Lua code examples before generation, providing the LLM with concrete patterns to follow.

## Architecture

```
┌─────────────┐
│   Task      │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│  RAG System         │
│  - Semantic Search  │
│  - ChromaDB         │
│  - Embeddings       │
└──────┬──────────────┘
       │ (relevant examples)
       ▼
┌─────────────────────┐
│  Generator Agent    │
│  + Context          │
└──────┬──────────────┘
       │
       ▼
┌─────────────┐
│  Lua Code   │
└─────────────┘
```

## Components

### 1. Vector Database (ChromaDB)
- **Local, no server needed** - runs in-process
- **Persistent** - stores embeddings on disk (`.veai/chroma/`)
- **Fast** - optimized for similarity search

### 2. Embeddings (sentence-transformers)
- **Model**: `all-MiniLM-L6-v2` (384 dimensions)
- **Fast**: ~1000 docs/sec on CPU
- **Small**: 80MB model size
- **Local**: no API calls needed

### 3. Knowledge Base
Contains curated Lua examples:
- **Standard Library** - table, string, math operations
- **Algorithms** - fibonacci, binary search, quicksort
- **Design Patterns** - module, factory, iterator
- **Data Structures** - stack, queue
- **Best Practices** - local variables, error handling

## Configuration

Edit `config/settings.yaml`:

```yaml
rag:
  enabled: true                          # Enable/disable RAG
  persist_directory: .veai/chroma        # Vector DB location
  embedding_model: all-MiniLM-L6-v2      # Embedding model
  collection_name: lua_knowledge         # Collection name
  retrieval_k: 3                         # Number of examples
  max_context_length: 1500               # Max context chars
```

## Usage

### Quick Mode (CLI)

RAG is automatically enabled if `rag.enabled: true` in settings:

```bash
python main.py --task "write fibonacci with memoization"
```

Output:
```
[RAG] Enabled with 15 documents
[Generator] Iteration 1 — 342 chars written
```

### Project Mode

RAG works automatically in project mode:

```bash
python main.py --mode project --task "create calculator" --evolutions 0
```

### Disable RAG

Set in `config/settings.yaml`:
```yaml
rag:
  enabled: false
```

Or via environment variable:
```bash
RAG_ENABLED=false python main.py --task "..."
```

## CLI Management

### Initialize Knowledge Base

```bash
python -m rag.cli init
```

Output:
```
Initializing RAG knowledge base...
✓ Knowledge base initialized
  Documents: 15
  Model: all-MiniLM-L6-v2
  Location: .veai/chroma
```

### Show Statistics

```bash
python -m rag.cli stats
```

### Search Examples

```bash
python -m rag.cli search "fibonacci memoization"
```

Output:
```
[1] Score: 0.856
Category: algorithm
Tags: fibonacci,memoization,recursion
------------------------------------------------------------
Fibonacci with memoization

```lua
local memo = {}
local function fibonacci(n)
    if n <= 1 then return n end
    if memo[n] then return memo[n] end
    memo[n] = fibonacci(n-1) + fibonacci(n-2)
    return memo[n]
end
```
```

### Add Custom Example

```bash
python -m rag.cli add-example
```

### Clear Knowledge Base

```bash
python -m rag.cli clear --force
```

## How It Works

### 1. Retrieval Phase

When Generator receives a task:
1. Task is embedded using sentence-transformers
2. ChromaDB finds top-k similar examples (default: 3)
3. Examples are formatted as context

### 2. Generation Phase

Generator receives:
```
Task: write fibonacci with memoization

Relevant examples from knowledge base:

Example 1:
Fibonacci with memoization

```lua
local memo = {}
...
```

Write the Lua code now:
```

### 3. Benefits

- **Reduced hallucinations** - LLM sees concrete examples
- **Better patterns** - follows established idioms
- **Faster generation** - less trial-and-error
- **Consistent style** - matches knowledge base

## Performance

### Speed Comparison

| Mode | Time (first run) | Time (cached) |
|------|------------------|---------------|
| Without RAG | 2.3s | 2.3s |
| With RAG | 3.1s | 2.5s |

**First run**: +0.8s for embedding model load
**Cached**: +0.2s for retrieval (negligible)

### Memory Usage

- **Embedding model**: ~200MB RAM
- **Vector DB**: ~10MB for 100 documents
- **Total overhead**: ~210MB

## Customization

### Change Embedding Model

For better quality (slower):
```yaml
rag:
  embedding_model: all-mpnet-base-v2  # 768 dim, more accurate
```

For faster speed (lower quality):
```yaml
rag:
  embedding_model: all-MiniLM-L12-v2  # 384 dim, faster
```

### Adjust Retrieval

More examples (more context, slower):
```yaml
rag:
  retrieval_k: 5
  max_context_length: 2500
```

Fewer examples (less context, faster):
```yaml
rag:
  retrieval_k: 2
  max_context_length: 1000
```

### Add Domain-Specific Examples

```python
from rag import create_rag_system

rag = create_rag_system()

rag.add_code_example(
    code="""
    local function custom_logic()
        -- your code
    end
    """,
    description="Custom domain logic",
    category="domain-specific"
)
```

## Troubleshooting

### RAG not initializing

**Error**: `ModuleNotFoundError: No module named 'chromadb'`

**Solution**:
```bash
pip install -r requirements.txt
```

### Slow first run

**Cause**: Downloading embedding model (~80MB)

**Solution**: Wait for first run, subsequent runs are fast

### Out of memory

**Cause**: Large embedding model

**Solution**: Use smaller model:
```yaml
rag:
  embedding_model: all-MiniLM-L6-v2  # smallest
```

### No relevant examples found

**Cause**: Knowledge base doesn't have similar examples

**Solution**: Add custom examples:
```bash
python -m rag.cli add-example
```

## API Integration

### FastAPI Server

RAG is automatically used in API mode:

```bash
python api/server.py
```

POST to `/api/run-task`:
```json
{
  "task": "write fibonacci",
  "use_rag": true
}
```

### Programmatic Usage

```python
from rag import create_rag_system, initialize_rag_with_examples
from agents.generator import GeneratorAgent
from llm.factory import get_llm

# Initialize RAG
rag = create_rag_system()
initialize_rag_with_examples(rag)

# Create generator with RAG
llm = get_llm("generator")
generator = GeneratorAgent(llm, rag_system=rag)

# Generate code
code = generator.generate(task="write fibonacci")
```

## Best Practices

1. **Keep knowledge base focused** - quality over quantity
2. **Use specific categories** - helps filtering
3. **Add tags** - improves search relevance
4. **Test retrieval** - use `rag.cli search` to verify
5. **Monitor performance** - check if RAG helps your use case

## Future Improvements

- [ ] Automatic example extraction from successful generations
- [ ] User feedback loop (thumbs up/down on examples)
- [ ] Multi-language support (Python, JavaScript, etc.)
- [ ] Cloud vector DB option (Pinecone, Weaviate)
- [ ] Hybrid search (keyword + semantic)
