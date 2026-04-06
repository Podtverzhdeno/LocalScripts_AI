# Interactive Graph Visualization

## Overview

LocalScript now includes a real-time interactive graph visualization powered by d3.js that shows the execution flow of the multi-agent pipeline.

## Features

### Real-Time Updates
- **Live node tracking** — see which agent (Generator, Validator, Reviewer) is currently executing
- **Iteration counter** — displays current iteration number
- **WebSocket-powered** — updates happen instantly as the pipeline progresses

### Interactive Elements
- **Clickable nodes** — click on any agent node to view related logs and code
- **Visual feedback** — active nodes glow and pulse
- **Edge animations** — edges light up to show execution flow
- **Status indicators** — color-coded dots show node completion status

### Visual Design
- **Node types**:
  - `START` — entry point (gray circle)
  - `Generator` ⚡ — code generation agent (large circle with lightning icon)
  - `Validator` ✓ — validation agent (large circle with checkmark icon)
  - `Reviewer` 👁 — review agent (large circle with eye icon)
  - `FAIL` — failure terminal (gray circle)
  - `END` — success terminal (gray circle)

- **Edge types**:
  - Solid arrows — forward flow
  - Curved arrows — feedback loops (errors, improvements)
  - Dashed arrows — failure path

- **Colors**:
  - Emerald green (#10b981) — active/success
  - Red (#ef4444) — errors/failure
  - Gray — inactive/neutral

## Architecture

### Frontend Components

**`frontend/graph.js`** — PipelineGraph class
- D3.js-based visualization
- Node and edge rendering
- Animation system
- Event handling

**`frontend/session.html`** — Integration
- Graph container
- WebSocket event handling
- Node click handlers

### Backend Integration

**`graph/nodes.py`** — Node callbacks
- Each node (generate, validate, review, fail) calls `node_callback` when it starts
- Callback receives node name and current state

**`graph/pipeline.py`** — Callback propagation
- `run_pipeline()` accepts `node_callback` parameter
- Passes callback to `build_pipeline()` and `make_nodes()`

**`api/routes.py`** — WebSocket events
- `_run_pipeline_async()` creates callback that broadcasts to WebSocket clients
- New event type: `node_enter` with fields:
  - `event`: "node_enter"
  - `node`: node name (generate/validate/review/fail)
  - `iteration`: current iteration number
  - `status`: current pipeline status

## WebSocket Events

### Existing Events
- `started` — pipeline started
- `progress` — iteration progress update
- `completed` — pipeline finished
- `error` — pipeline error
- `status` — current status snapshot

### New Events
- `node_enter` — agent node execution started
  ```json
  {
    "event": "node_enter",
    "node": "generate",
    "iteration": 1,
    "status": "generating"
  }
  ```

## Usage

### Viewing the Graph

1. Start the API server:
   ```bash
   python api/server.py
   ```

2. Run a task:
   ```bash
   python main.py --task "write fibonacci function"
   ```

3. Open the session page in browser:
   ```
   http://127.0.0.1:8000/session/session_TIMESTAMP
   ```

4. Watch the graph update in real-time as agents execute

### Interacting with the Graph

- **Click on agent nodes** — view related files and logs
- **Click "Reset" button** — clear graph state and start fresh
- **Hover over nodes** — see tooltips (future enhancement)

## Implementation Details

### Graph Layout

Nodes are positioned using fixed coordinates for a clean left-to-right flow:

```
START → Generator → Validator → Reviewer → END
              ↑         ↓           ↓
              └─────────┴───────────┘
                   (feedback loops)
                        ↓
                      FAIL → END
```

### Animation System

- **Node activation**: 300ms pulse animation + glow filter
- **Edge highlighting**: 500ms color transition
- **Status indicators**: Fade in/out with 500ms duration

### Performance

- Minimal overhead: callbacks execute in <1ms
- WebSocket broadcasts are non-blocking
- D3.js handles rendering efficiently
- No polling required — pure event-driven updates

## Future Enhancements

- [ ] Node tooltips with execution time
- [ ] Execution history timeline
- [ ] Zoom and pan controls
- [ ] Export graph as SVG/PNG
- [ ] Replay mode for completed sessions
- [ ] Multi-session comparison view
- [ ] Custom node colors per agent type
- [ ] Edge labels showing transition reasons

## Troubleshooting

**Graph not updating:**
- Check browser console for WebSocket errors
- Verify API server is running
- Check that session_id is valid

**Nodes not clickable:**
- Ensure graph.js is loaded (check Network tab)
- Verify d3.js CDN is accessible

**Layout issues:**
- Clear browser cache
- Check viewport size (graph requires min 800px width)

## API Reference

### PipelineGraph Class

```javascript
// Initialize
const graph = new PipelineGraph('containerId');

// Set active node
graph.setActiveNode('generate', iteration);

// Mark node complete
graph.markNodeComplete('generate');

// Mark node error
graph.markNodeError('validate');

// Reset graph
graph.reset();

// Get execution history
const history = graph.getHistory();
```

### Events

```javascript
// Listen for node clicks
container.addEventListener('nodeClick', (e) => {
  const { nodeId, agent } = e.detail;
  // Handle click
});
```
