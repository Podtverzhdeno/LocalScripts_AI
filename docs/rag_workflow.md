# RAG Workflow with Retriever and Approver Agents

## Overview

The new RAG workflow introduces two specialized agents to improve code generation quality, especially for small models (7B-11B parameters):

1. **Retriever Agent** — searches the vector database for relevant code examples
2. **Approver Agent** — evaluates whether retrieved examples are relevant enough to use as templates

This architecture prevents the generator from receiving irrelevant or misleading examples, which is critical for smaller models that are more sensitive to prompt quality.

## Architecture

```
User Task
    ↓
[Retriever Agent] ──→ Search RAG (ChromaDB)
    ↓
Retrieved Examples (top 5)
    ↓
[Approver Agent] ──→ Evaluate Relevance
    ↓
    ├─→ APPROVED ──→ [Generator] with template
    └─→ REJECTED ──→ [Generator] from scratch
```

## Why This Approach?

### Problem with Direct RAG
In the original implementation, RAG examples were directly injected into the generator's prompt without validation. For small models (7B-11B), this caused issues:

- **Irrelevant examples** confused the model
- **Low-quality matches** led to worse code than generating from scratch
- **No quality control** on what examples were used

### Solution: Two-Stage Approval
By adding a dedicated approver agent:

1. **Quality gate**: Only relevant examples reach the generator
2. **Better prompts**: Generator receives either high-quality templates or nothing
3. **Explicit decision**: Clear logging of why examples were approved/rejected
4. **Model-appropriate**: Conservative approval for small models

## Agent Responsibilities

### Retriever Agent (`agents/retriever.py`)

**Role**: Search specialist focused on finding relevant examples

**Responsibilities**:
- Analyze user task to identify key requirements
- Search vector database (ChromaDB) for similar code
- Return top-k examples with similarity scores
- Format results for approver evaluation

**Does NOT**:
- Generate code
- Make approval decisions
- Modify examples

**Configuration**:
```yaml
agents:
  retriever:
    backend: ollama
    model: qwen2.5-coder:7b  # Fast local model for search
```

### Approver Agent (`agents/approver.py`)

**Role**: Quality evaluator for retrieved examples

**Responsibilities**:
- Evaluate relevance of retrieved examples to user task
- Decide: APPROVE (use as template) or REJECT (generate from scratch)
- Select which specific examples to use (if multiple)
- Provide confidence score and reasoning

**Evaluation Criteria**:
1. **Relevance**: Do examples solve similar problems?
   - High: Same algorithm/pattern (both use memoization, both are sorting)
   - Medium: Similar domain but different approach
   - Low: Different problem domain

2. **Usefulness**: Would examples improve code quality?
   - Approve: Clear structure, edge cases, best practices
   - Reject: Too different, would require complete rewrite

3. **Confidence**: How certain is the decision?
   - High (0.8-1.0): Clear match or mismatch
   - Medium (0.5-0.8): Partial relevance
   - Low (0.0-0.5): Uncertain

**Decision Rules**:
- APPROVE if relevance is high and examples serve as good templates
- REJECT if relevance is low or examples wouldn't help
- **When in doubt, REJECT** (for small models, bad templates are worse than no templates)

**Configuration**:
```yaml
agents:
  approver:
    backend: openrouter
    model: openai/gpt-4o-mini  # Stronger model for evaluation
```

## Workflow Integration

### State Updates

The workflow adds new state fields:

```python
{
    "rag_results": List[Tuple[Document, float]],  # Retrieved examples with scores
    "rag_formatted": str,                          # Formatted for approver
    "rag_decision": Dict,                          # Approval decision
    "approved_template": str | None,               # Template for generator (if approved)
}
```

### Node Flow

```
START
  ↓
[rag_retrieve] ──→ Search knowledge base
  ↓
[rag_approve] ──→ Evaluate relevance
  ↓
[generate] ──→ Use template OR generate from scratch
  ↓
[validate] ──→ Run tests
  ↓
[review] ──→ Quality check
  ↓
END
```

### Status Transitions

- `"rag_retrieving"` → Retriever searching
- `"rag_approving"` → Approver evaluating
- `"generating"` → Generator writing code
- `"validating"` → Validator testing
- `"reviewing"` → Reviewer checking
- `"done"` → Success
- `"failed"` → Max iterations reached

## Usage

### Enable RAG Workflow

In `config/settings.yaml`:

```yaml
rag:
  enabled: true
  workflow_mode: "approve"  # "approve" | "direct" | "disabled"
  
agents:
  retriever:
    backend: ollama
    model: qwen2.5-coder:7b
  
  approver:
    backend: openrouter
    model: openai/gpt-4o-mini
  
  generator:
    backend: ollama
    model: qwen2.5-coder:7b
```

### CLI

```bash
# Use new RAG workflow (default)
python main.py --task "write fibonacci with memoization"

# Disable RAG workflow (legacy direct mode)
python main.py --task "write fibonacci" --no-rag-workflow

# Force approval (skip approver, always use retrieved examples)
python main.py --task "write fibonacci" --force-rag-approval
```

### Programmatic

```python
from graph.pipeline import run_pipeline
from rag.system import create_rag_system

# Initialize RAG
rag_system = create_rag_system()

# Run with new workflow
result = run_pipeline(
    task="write a binary search function",
    rag_system=rag_system,
    use_rag_workflow=True,  # Enable retriever + approver
)

# Check decision
if result["rag_decision"]:
    print(f"Approved: {result['rag_decision']['approved']}")
    print(f"Reason: {result['rag_decision']['reason']}")
    print(f"Confidence: {result['rag_decision']['confidence']}")
```

## Example Output

### Approved Example

```
[RAG] Starting retrieval workflow...
[Retriever] Searching for: 'write fibonacci with memoization'
[Retriever] Found 5 examples:
[Retriever]   [1] algorithm    (score: 0.892) - Fibonacci with memoization...
[Retriever]   [2] algorithm    (score: 0.745) - Dynamic programming - longest common subsequence...
[Retriever]   [3] best-practice (score: 0.623) - Use local variables for performance...
[Retriever]   [4] pattern      (score: 0.587) - Module pattern - encapsulation and namespacing...
[Retriever]   [5] algorithm    (score: 0.534) - Binary search in sorted array...

[RAG] Evaluating retrieved examples...
[Approver] Decision: APPROVED
[Approver] Reason: Example 1 directly demonstrates fibonacci with memoization, which is exactly what the task requires
[Approver] Confidence: 0.95
[Approver] Selected examples: [1]

[RAG] ✓ APPROVED - Using 1 example(s) as template
[Generator] Using approved RAG template
[Generator] Iteration 1 — 342 chars written
```

### Rejected Example

```
[RAG] Starting retrieval workflow...
[Retriever] Searching for: 'validate email addresses'
[Retriever] Found 5 examples:
[Retriever]   [1] string       (score: 0.612) - Advanced pattern matching and capture...
[Retriever]   [2] integration  (score: 0.589) - Email validation with RFC 5322 rules...
[Retriever]   [3] string       (score: 0.543) - String substitution and replacement...
[Retriever]   [4] best-practice (score: 0.498) - Proper error handling and validation...
[Retriever]   [5] stdlib       (score: 0.467) - String operations - split, join, pattern matching...

[RAG] Evaluating retrieved examples...
[Approver] Decision: REJECTED
[Approver] Reason: While example 2 shows email validation, it's for a different context (integration patterns). The task needs a simpler standalone validator.
[Approver] Confidence: 0.72

[RAG] ✗ REJECTED - The task needs a simpler standalone validator
[RAG] Generating from scratch
[Generator] Iteration 1 — 287 chars written
```

## Benefits

### For Small Models (7B-11B)

1. **Higher success rate**: Only receive relevant examples
2. **Clearer prompts**: Template or nothing, no confusion
3. **Better quality**: Conservative approval prevents bad templates
4. **Faster iteration**: Less retry due to misleading examples

### For All Models

1. **Transparency**: Clear logging of approval decisions
2. **Debuggability**: Can see why examples were approved/rejected
3. **Flexibility**: Can tune approval threshold per model size
4. **Metrics**: Track approval rate, confidence scores

## Configuration Tips

### For 7B Models

```yaml
agents:
  approver:
    backend: openrouter
    model: openai/gpt-4o-mini  # Use stronger model for approval
    
rag:
  approval_threshold: 0.7  # Conservative (higher = stricter)
  max_examples: 3          # Fewer examples to avoid confusion
```

### For 30B+ Models

```yaml
agents:
  approver:
    backend: ollama
    model: qwen2.5-coder:32b  # Can use local model
    
rag:
  approval_threshold: 0.5  # More permissive
  max_examples: 5          # Can handle more context
```

## Monitoring

### Approval Metrics

Track these metrics to tune the system:

```python
# In your pipeline
approval_rate = approved_count / total_retrievals
avg_confidence = sum(confidences) / len(confidences)
success_rate_with_template = successes_approved / total_approved
success_rate_without_template = successes_rejected / total_rejected

# Log to file
with open("rag_metrics.json", "a") as f:
    json.dump({
        "timestamp": datetime.now().isoformat(),
        "approval_rate": approval_rate,
        "avg_confidence": avg_confidence,
        "success_with_template": success_rate_with_template,
        "success_without_template": success_rate_without_template,
    }, f)
```

### Decision Analysis

```bash
# View approval decisions
grep "Approver" workspace/*/report.md

# Count approvals vs rejections
grep -c "APPROVED" workspace/*/report.md
grep -c "REJECTED" workspace/*/report.md

# Average confidence
grep "Confidence:" workspace/*/report.md | awk '{sum+=$2; count++} END {print sum/count}'
```

## Troubleshooting

### Too Many Rejections

If approval rate is too low (<30%):

1. Lower `approval_threshold` in config
2. Expand knowledge base with more examples
3. Use stronger model for approver
4. Check retriever is finding relevant examples

### Too Many Approvals

If approval rate is too high (>80%) but quality is poor:

1. Raise `approval_threshold`
2. Use stronger model for approver
3. Review approver prompt for clarity
4. Add more evaluation criteria

### Slow Performance

If RAG workflow is too slow:

1. Use faster model for retriever (e.g., 7B local)
2. Reduce `max_examples` (fewer to evaluate)
3. Cache approval decisions for similar tasks
4. Run retriever and approver in parallel (future optimization)

## Future Enhancements

1. **Caching**: Cache approval decisions for similar tasks
2. **Learning**: Track which approvals led to success, adjust threshold
3. **Parallel execution**: Run retriever and approver concurrently
4. **Multi-stage approval**: Add second approver for borderline cases
5. **Feedback loop**: Use generation success to improve approval criteria
