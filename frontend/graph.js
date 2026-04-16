/**
 * Interactive LangGraph visualization with d3.js
 * Enhanced version with detailed node info, execution timeline, and clickable nodes
 */

class PipelineGraph {
    constructor(containerId, mode = 'quick') {
        this.container = d3.select(`#${containerId}`);
        this.width = 1200; // Increased from 1000 to show all nodes
        this.height = 500;
        this.currentNode = null;
        this.history = [];
        this.nodeStats = {}; // Track execution count and timing per node
        this.mode = mode;

        // Quick mode: START → Clarifier → RAG Retrieve → RAG Approve → Generator → Validator → Checkpoint → Reviewer
        // Увеличены расстояния между узлами для лучшей читаемости
        this.quickNodes = [
            { id: 'start', label: 'START', x: 60, y: 250, type: 'start' },
            { id: 'clarify', label: 'Clarifier', x: 180, y: 250, type: 'agent', agent: 'clarifier', desc: 'Analyzes task ambiguity', color: '#f59e0b' },
            { id: 'rag_retrieve', label: 'Retriever', x: 300, y: 250, type: 'agent', agent: 'retriever', desc: 'Searches knowledge base', color: '#06b6d4' },
            { id: 'rag_approve', label: 'Approver', x: 420, y: 250, type: 'agent', agent: 'approver', desc: 'Evaluates relevance', color: '#ec4899' },
            { id: 'generate', label: 'Generator', x: 540, y: 250, type: 'agent', agent: 'generator', desc: 'Writes Lua code', color: '#10b981' },
            { id: 'validate', label: 'Validator', x: 660, y: 250, type: 'agent', agent: 'validator', desc: 'Compiles & runs code', color: '#3b82f6' },
            { id: 'checkpoint', label: 'Checkpoint', x: 780, y: 250, type: 'agent', agent: 'checkpoint', desc: 'User approval', color: '#a855f7' },
            { id: 'review', label: 'Reviewer', x: 900, y: 250, type: 'agent', agent: 'reviewer', desc: 'Quality check', color: '#8b5cf6' },
            { id: 'clarify_errors', label: 'Error Clarifier', x: 660, y: 130, type: 'agent', agent: 'clarifier', desc: 'Clarifies after errors', color: '#f97316' },
            { id: 'fail', label: 'FAIL', x: 660, y: 400, type: 'end', color: '#ef4444' },
            { id: 'end', label: 'SUCCESS', x: 1020, y: 250, type: 'end', color: '#10b981' }
        ];

        this.quickEdges = [
            { from: 'start', to: 'clarify', label: '' },
            { from: 'clarify', to: 'rag_retrieve', label: '' },
            { from: 'clarify', to: 'clarify', label: '', curve: true, type: 'wait' },
            { from: 'rag_retrieve', to: 'rag_approve', label: '' },
            { from: 'rag_approve', to: 'generate', label: '' },
            { from: 'generate', to: 'validate', label: '' },
            { from: 'validate', to: 'checkpoint', label: '' },
            { from: 'validate', to: 'clarify_errors', label: '', type: 'error' },
            { from: 'validate', to: 'generate', label: '', curve: true, type: 'retry' },
            { from: 'validate', to: 'fail', label: '', type: 'fail' },
            { from: 'clarify_errors', to: 'generate', label: '' },
            { from: 'checkpoint', to: 'review', label: '' },
            { from: 'checkpoint', to: 'generate', label: '', curve: true, type: 'retry' },
            { from: 'checkpoint', to: 'checkpoint', label: '', curve: true, type: 'wait' },
            { from: 'review', to: 'end', label: '' },
            { from: 'review', to: 'generate', label: '', curve: true, type: 'retry' }
        ];

        // Project mode: Architect → Specification → Generator → Validator → Reviewer → Integrator → Decomposer → Evolver
        this.projectNodes = [
            { id: 'start', label: 'START', x: 60, y: 250, type: 'start' },
            { id: 'architect', label: 'Architect', x: 180, y: 250, type: 'agent', agent: 'architect', desc: 'Plans project structure', color: '#06b6d4' },
            { id: 'specification', label: 'Specification', x: 320, y: 250, type: 'agent', agent: 'specification', desc: 'Creates detailed specs', color: '#ec4899' },
            { id: 'generate', label: 'Generator', x: 460, y: 250, type: 'agent', agent: 'generator', desc: 'Writes Lua code', color: '#10b981' },
            { id: 'validate', label: 'Validator', x: 600, y: 250, type: 'agent', agent: 'validator', desc: 'Compiles & runs code', color: '#3b82f6' },
            { id: 'review', label: 'Reviewer', x: 740, y: 250, type: 'agent', agent: 'reviewer', desc: 'Quality check', color: '#8b5cf6' },
            { id: 'integrator', label: 'Integrator', x: 880, y: 250, type: 'agent', agent: 'integrator', desc: 'Tests integration', color: '#f97316' },
            { id: 'decomposer', label: 'Decomposer', x: 1020, y: 150, type: 'agent', agent: 'decomposer', desc: 'Analyzes code', color: '#a855f7' },
            { id: 'evolver', label: 'Evolver', x: 1020, y: 350, type: 'agent', agent: 'evolver', desc: 'Optimizes & refines', color: '#f59e0b' },
            { id: 'fail', label: 'FAIL', x: 600, y: 420, type: 'end', color: '#ef4444' },
            { id: 'end', label: 'SUCCESS', x: 1140, y: 250, type: 'end', color: '#10b981' }
        ];

        this.projectEdges = [
            { from: 'start', to: 'architect', label: '' },
            { from: 'architect', to: 'specification', label: '' },
            { from: 'specification', to: 'generate', label: '' },
            { from: 'generate', to: 'validate', label: '' },
            { from: 'validate', to: 'review', label: '' },
            { from: 'validate', to: 'generate', label: '', curve: true, type: 'retry' },
            { from: 'validate', to: 'fail', label: '', type: 'fail' },
            { from: 'review', to: 'integrator', label: '' },
            { from: 'review', to: 'generate', label: '', curve: true, type: 'retry' },
            { from: 'integrator', to: 'decomposer', label: '' },
            { from: 'integrator', to: 'evolver', label: '' },
            { from: 'decomposer', to: 'end', label: '' },
            { from: 'evolver', to: 'end', label: '' }
        ];

        this.nodes = this.mode === 'project' ? this.projectNodes : this.quickNodes;
        this.edges = this.mode === 'project' ? this.projectEdges : this.quickEdges;

        this.init();
    }

    init() {
        // SVG container
        this.svg = this.container.append('svg')
            .attr('width', '100%')
            .attr('height', this.height)
            .attr('viewBox', `0 0 ${this.width} ${this.height}`)
            .attr('preserveAspectRatio', 'xMidYMid meet');

        // Background grid
        const gridGroup = this.svg.append('g').attr('class', 'grid');
        for (let i = 0; i < this.width; i += 40) {
            gridGroup.append('line')
                .attr('x1', i).attr('y1', 0)
                .attr('x2', i).attr('y2', this.height)
                .attr('stroke', 'rgba(255,255,255,0.02)')
                .attr('stroke-width', 1);
        }
        for (let i = 0; i < this.height; i += 40) {
            gridGroup.append('line')
                .attr('x1', 0).attr('y1', i)
                .attr('x2', this.width).attr('y2', i)
                .attr('stroke', 'rgba(255,255,255,0.02)')
                .attr('stroke-width', 1);
        }

        // Defs for arrows and glows
        const defs = this.svg.append('defs');

        // Arrow markers
        ['arrow', 'arrow-active', 'arrow-retry', 'arrow-fail'].forEach((id, idx) => {
            const colors = ['rgba(255,255,255,0.3)', '#10b981', '#eab308', '#ef4444'];
            defs.append('marker')
                .attr('id', id)
                .attr('viewBox', '0 0 10 10')
                .attr('refX', 8)
                .attr('refY', 5)
                .attr('markerWidth', 6)
                .attr('markerHeight', 6)
                .attr('orient', 'auto')
                .append('path')
                .attr('d', 'M 0 0 L 10 5 L 0 10 z')
                .attr('fill', colors[idx]);
        });

        // Glow filters
        ['glow-green', 'glow-yellow', 'glow-red'].forEach((id, idx) => {
            const colors = ['#10b981', '#eab308', '#ef4444'];
            const filter = defs.append('filter')
                .attr('id', id)
                .attr('x', '-50%')
                .attr('y', '-50%')
                .attr('width', '200%')
                .attr('height', '200%');

            filter.append('feGaussianBlur')
                .attr('stdDeviation', '5')
                .attr('result', 'coloredBlur');

            filter.append('feFlood')
                .attr('flood-color', colors[idx])
                .attr('flood-opacity', '0.6')
                .attr('result', 'flood');

            filter.append('feComposite')
                .attr('in', 'flood')
                .attr('in2', 'coloredBlur')
                .attr('operator', 'in')
                .attr('result', 'coloredBlur');

            const feMerge = filter.append('feMerge');
            feMerge.append('feMergeNode').attr('in', 'coloredBlur');
            feMerge.append('feMergeNode').attr('in', 'SourceGraphic');
        });

        // Draw edges
        this.edgeGroup = this.svg.append('g').attr('class', 'edges');
        this.drawEdges();

        // Draw nodes
        this.nodeGroup = this.svg.append('g').attr('class', 'nodes');
        this.drawNodes();

        // Info panel (top left instead of top right)
        this.infoPanel = this.svg.append('g')
            .attr('class', 'info-panel')
            .attr('transform', `translate(20, 20)`);

        this.infoPanel.append('rect')
            .attr('width', 160)
            .attr('height', 100)
            .attr('rx', 8)
            .attr('fill', 'rgba(15, 23, 42, 0.9)')
            .attr('stroke', 'rgba(255,255,255,0.1)')
            .attr('stroke-width', 1);

        this.iterationText = this.infoPanel.append('text')
            .attr('x', 15)
            .attr('y', 25)
            .style('font-family', 'JetBrains Mono, monospace')
            .style('font-size', '13px')
            .style('font-weight', '600')
            .style('fill', '#10b981')
            .text('Iteration: 0');

        this.statusText = this.infoPanel.append('text')
            .attr('x', 15)
            .attr('y', 50)
            .style('font-family', 'Inter, sans-serif')
            .style('font-size', '11px')
            .style('fill', '#9ca3af')
            .text('Status: Idle');

        this.timeText = this.infoPanel.append('text')
            .attr('x', 15)
            .attr('y', 70)
            .style('font-family', 'JetBrains Mono, monospace')
            .style('font-size', '10px')
            .style('fill', '#6b7280')
            .text('Time: 0s');

        // Tooltip
        this.tooltip = this.container.append('div')
            .attr('class', 'graph-tooltip')
            .style('position', 'absolute')
            .style('visibility', 'hidden')
            .style('background', 'rgba(15, 23, 42, 0.95)')
            .style('color', '#fff')
            .style('padding', '12px 16px')
            .style('border-radius', '8px')
            .style('border', '1px solid rgba(16, 185, 129, 0.3)')
            .style('font-size', '12px')
            .style('font-family', 'Inter, sans-serif')
            .style('pointer-events', 'none')
            .style('z-index', '1000')
            .style('box-shadow', '0 4px 20px rgba(0,0,0,0.5)');

        this.startTime = null;
        this.updateTimer();
    }

    updateTimer() {
        if (this.startTime) {
            const elapsed = Math.floor((Date.now() - this.startTime) / 1000);
            this.timeText.text(`Time: ${elapsed}s`);
        }
        requestAnimationFrame(() => this.updateTimer());
    }

    drawEdges() {
        const self = this;

        this.edgeGroup.selectAll('path')
            .data(this.edges)
            .enter()
            .append('path')
            .attr('class', d => `edge edge-${d.from}-${d.to}`)
            .attr('d', d => this.getEdgePath(d))
            .attr('fill', 'none')
            .attr('stroke', d => {
                if (d.type === 'retry') return 'rgba(234, 179, 8, 0.3)';
                if (d.type === 'fail') return 'rgba(239, 68, 68, 0.3)';
                return 'rgba(255,255,255,0.2)';
            })
            .attr('stroke-width', 3)
            .attr('marker-end', 'url(#arrow)');

        // Edge labels
        this.edgeGroup.selectAll('text')
            .data(this.edges.filter(d => d.label))
            .enter()
            .append('text')
            .attr('class', 'edge-label')
            .attr('x', d => this.getEdgeLabelPos(d).x)
            .attr('y', d => this.getEdgeLabelPos(d).y)
            .attr('text-anchor', 'middle')
            .style('font-size', '11px')
            .style('font-weight', '600')
            .style('fill', '#9ca3af')
            .style('pointer-events', 'none')
            .text(d => d.label);
    }

    getEdgePath(edge) {
        const from = this.nodes.find(n => n.id === edge.from);
        const to = this.nodes.find(n => n.id === edge.to);

        if (!from || !to) return '';

        // Card dimensions: width=140, height=70, so half-width=70, half-height=35
        const cardHalfWidth = 70;
        const circleRadius = 24;

        const fromRadius = (from.type === 'start' || from.type === 'end') ? circleRadius : cardHalfWidth;
        const toRadius = (to.type === 'start' || to.type === 'end') ? circleRadius : cardHalfWidth;

        if (edge.curve) {
            // Curved path for feedback loops
            const midX = (from.x + to.x) / 2;
            const midY = from.y + 130;
            return `M ${from.x + fromRadius} ${from.y} Q ${midX} ${midY} ${to.x - toRadius} ${to.y}`;
        }

        if (edge.from === 'validate' && edge.to === 'fail') {
            // Downward path
            return `M ${from.x} ${from.y + 35} L ${to.x} ${to.y - circleRadius}`;
        }

        // For project mode: handle architect to specification
        if (edge.from === 'architect' && edge.to === 'specification') {
            return `M ${from.x + fromRadius} ${from.y} L ${to.x - toRadius} ${to.y}`;
        }

        // For project mode: handle specification to generator
        if (edge.from === 'specification' && edge.to === 'generate') {
            return `M ${from.x + fromRadius} ${from.y} L ${to.x - toRadius} ${to.y}`;
        }

        // For project mode: handle review to integrator
        if (edge.from === 'review' && edge.to === 'integrator') {
            return `M ${from.x + fromRadius} ${from.y} L ${to.x - toRadius} ${to.y}`;
        }

        // For project mode: handle integrator to decomposer
        if (edge.from === 'integrator' && edge.to === 'decomposer') {
            return `M ${from.x + fromRadius/2} ${from.y - 35} L ${to.x - toRadius/2} ${to.y + 35}`;
        }

        // For project mode: handle integrator to evolver
        if (edge.from === 'integrator' && edge.to === 'evolver') {
            return `M ${from.x + fromRadius/2} ${from.y + 35} L ${to.x - toRadius/2} ${to.y - 35}`;
        }

        // For project mode: handle decomposer to end
        if (edge.from === 'decomposer' && edge.to === 'end') {
            return `M ${from.x + fromRadius/2} ${from.y + 35} L ${to.x - circleRadius} ${to.y - 50}`;
        }

        // For project mode: handle evolver to end
        if (edge.from === 'evolver' && edge.to === 'end') {
            return `M ${from.x + fromRadius/2} ${from.y - 35} L ${to.x - circleRadius} ${to.y + 50}`;
        }

        return `M ${from.x + fromRadius} ${from.y} L ${to.x - toRadius} ${to.y}`;
    }

    getEdgeLabelPos(edge) {
        const from = this.nodes.find(n => n.id === edge.from);
        const to = this.nodes.find(n => n.id === edge.to);

        if (edge.curve) {
            const midX = (from.x + to.x) / 2;
            const midY = from.y + 120;
            return { x: midX, y: midY + 5 };
        }

        if (edge.from === 'validate' && edge.to === 'fail') {
            return { x: from.x + 30, y: (from.y + to.y) / 2 };
        }

        // For diagonal edges in project mode
        if ((edge.from === 'architect' || edge.from === 'decomposer') && edge.to === 'generate') {
            return { x: (from.x + to.x) / 2, y: (from.y + to.y) / 2 - 10 };
        }

        if (edge.from === 'review' && edge.to === 'evolver') {
            return { x: (from.x + to.x) / 2, y: (from.y + to.y) / 2 - 10 };
        }

        // New agents in project mode
        if (edge.from === 'integrator' && (edge.to === 'decomposer' || edge.to === 'evolver')) {
            return { x: (from.x + to.x) / 2, y: (from.y + to.y) / 2 };
        }
        if ((edge.from === 'decomposer' || edge.from === 'evolver') && edge.to === 'end') {
            return { x: (from.x + to.x) / 2, y: (from.y + to.y) / 2 };
        }

        return {
            x: (from.x + to.x) / 2,
            y: from.y - 12
        };
    }

    drawNodes() {
        const self = this;

        const nodeEnter = this.nodeGroup.selectAll('g')
            .data(this.nodes)
            .enter()
            .append('g')
            .attr('class', d => `node node-${d.id}`)
            .attr('transform', d => `translate(${d.x}, ${d.y})`)
            .style('cursor', d => d.type === 'agent' ? 'pointer' : 'default')
            .on('click', function(event, d) {
                if (d.type === 'agent') {
                    self.onNodeClick(d);
                }
            })
            .on('mouseenter', function(event, d) {
                // Tooltip disabled
            })
            .on('mousemove', function(event, d) {
                // Tooltip disabled
            })
            .on('mouseleave', function() {
                // Tooltip disabled
            });

        // Draw agent nodes as rounded rectangles (cards) - larger, more prominent
        nodeEnter.filter(d => d.type === 'agent')
            .append('rect')
            .attr('class', 'node-card')
            .attr('x', -70)
            .attr('y', -35)
            .attr('width', 140)
            .attr('height', 70)
            .attr('rx', 8)
            .attr('ry', 8)
            .attr('fill', 'rgba(15, 23, 42, 0.95)')
            .attr('stroke', d => d.color)
            .attr('stroke-width', 2)
            .style('filter', 'drop-shadow(0 4px 12px rgba(0, 0, 0, 0.3))');

        // Agent icon circle background
        nodeEnter.filter(d => d.type === 'agent')
            .append('circle')
            .attr('cx', -45)
            .attr('cy', 0)
            .attr('r', 18)
            .attr('fill', d => d.color)
            .attr('opacity', 0.2);

        // Agent icon text
        nodeEnter.filter(d => d.type === 'agent')
            .append('text')
            .attr('x', -45)
            .attr('y', 0)
            .attr('text-anchor', 'middle')
            .attr('dy', 5)
            .style('font-size', '16px')
            .style('font-weight', '700')
            .style('fill', d => d.color)
            .style('pointer-events', 'none')
            .text(d => this.getAgentIcon(d.agent));

        // Agent labels
        nodeEnter.filter(d => d.type === 'agent')
            .append('text')
            .attr('x', -15)
            .attr('y', 0)
            .attr('text-anchor', 'start')
            .attr('dy', 5)
            .style('font-size', '14px')
            .style('font-weight', '600')
            .style('fill', '#fff')
            .style('pointer-events', 'none')
            .text(d => d.label);

        // Start/End nodes as circles
        nodeEnter.filter(d => d.type === 'start' || d.type === 'end')
            .append('circle')
            .attr('r', 24)
            .attr('class', 'node-circle')
            .attr('fill', d => d.color ? `${d.color}20` : 'rgba(107, 114, 128, 0.3)')
            .attr('stroke', d => d.color || 'rgba(255,255,255,0.3)')
            .attr('stroke-width', 2);

        // Start/End labels
        nodeEnter.filter(d => d.type === 'start' || d.type === 'end')
            .append('text')
            .attr('text-anchor', 'middle')
            .attr('dy', 5)
            .style('font-size', '11px')
            .style('font-weight', '700')
            .style('fill', '#fff')
            .style('pointer-events', 'none')
            .text(d => d.label);

        // Execution count badge
        nodeEnter.filter(d => d.type === 'agent')
            .append('g')
            .attr('class', 'exec-count')
            .attr('transform', 'translate(60, -25)')
            .style('opacity', 0)
            .call(g => {
                g.append('circle')
                    .attr('r', 12)
                    .attr('fill', '#10b981')
                    .attr('stroke', 'rgba(15, 23, 42, 0.9)')
                    .attr('stroke-width', 2);
                g.append('text')
                    .attr('text-anchor', 'middle')
                    .attr('dy', 4)
                    .style('font-size', '10px')
                    .style('font-weight', '700')
                    .style('fill', '#fff')
                    .style('pointer-events', 'none')
                    .text('0');
            });

        // Status indicator (pulsing dot)
        nodeEnter.append('circle')
            .attr('class', 'status-indicator')
            .attr('r', 0)
            .attr('cx', -60)
            .attr('cy', -25)
            .attr('fill', '#10b981')
            .style('opacity', 0);
    }

    getNodeColor(node) {
        if (node.color) return node.color + '33'; // Add transparency
        const colors = {
            start: 'rgba(107, 114, 128, 0.3)',
            end: 'rgba(107, 114, 128, 0.3)',
            agent: 'rgba(15, 23, 42, 0.8)'
        };
        return colors[node.type] || colors.agent;
    }

    getAgentIcon(agent) {
        const icons = {
            architect: 'A',
            specification: 'S',
            decomposer: 'D',
            generator: 'G',
            validator: 'V',
            reviewer: 'R',
            integrator: 'I',
            evolver: 'E',
            retriever: '🔍',
            approver: '✓'
        };
        return icons[agent] || '●';
    }

    showTooltip(event, node) {
        const stats = this.nodeStats[node.id] || { count: 0, lastTime: null };
        let html = `<div style="font-weight: 600; margin-bottom: 6px; color: #10b981;">${node.label}</div>`;
        html += `<div style="font-size: 11px; color: #9ca3af; margin-bottom: 8px;">${node.desc || ''}</div>`;
        html += `<div style="font-size: 10px; color: #6b7280;">Executions: <span style="color: #fff; font-weight: 600;">${stats.count}</span></div>`;
        if (stats.lastTime) {
            html += `<div style="font-size: 10px; color: #6b7280; margin-top: 4px;">Last: ${stats.lastTime}</div>`;
        }
        html += `<div style="font-size: 9px; color: #4b5563; margin-top: 8px; padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.1);">Click to view logs</div>`;

        this.tooltip.html(html).style('visibility', 'visible');
        this.moveTooltip(event);
    }

    moveTooltip(event) {
        const containerRect = this.container.node().getBoundingClientRect();
        this.tooltip
            .style('left', (event.clientX - containerRect.left + 15) + 'px')
            .style('top', (event.clientY - containerRect.top - 10) + 'px');
    }

    hideTooltip() {
        this.tooltip.style('visibility', 'hidden');
    }

    // Public API

    setActiveNode(nodeId, iteration = null) {
        this.currentNode = nodeId;
        const timestamp = new Date().toLocaleTimeString();
        this.history.push({ node: nodeId, iteration, timestamp: Date.now() });

        // Check if node exists in current mode
        const nodeData = this.nodes.find(n => n.id === nodeId);
        if (!nodeData) {
            console.warn(`Node ${nodeId} not found in ${this.mode} mode graph`);
            return;
        }

        // Update stats
        if (!this.nodeStats[nodeId]) {
            this.nodeStats[nodeId] = { count: 0, lastTime: null };
        }
        this.nodeStats[nodeId].count++;
        this.nodeStats[nodeId].lastTime = timestamp;

        // Start timer on first node
        if (!this.startTime && nodeId !== 'start') {
            this.startTime = Date.now();
        }

        // Update iteration counter
        if (iteration !== null) {
            this.iterationText.text(`Iteration: ${iteration}`);
        }

        // Update status
        const statusMap = {
            'start': 'Starting...',
            'architect': 'Planning architecture',
            'specification': 'Creating specifications',
            'decomposer': 'Analyzing code',
            'rag_retrieve': 'Searching knowledge base',
            'rag_approve': 'Evaluating examples',
            'generate': 'Generating code',
            'validate': 'Validating code',
            'review': 'Reviewing quality',
            'integrator': 'Testing integration',
            'evolver': 'Optimizing code',
            'end': 'Completed ✓',
            'fail': 'Failed ✗'
        };
        this.statusText.text(`Status: ${statusMap[nodeId] || 'Running'}`);

        // Reset all nodes
        this.nodeGroup.selectAll('.node-card')
            .attr('stroke', d => d.color)
            .attr('stroke-width', 2)
            .style('filter', 'none');

        this.nodeGroup.selectAll('.node-circle')
            .attr('stroke', d => d.color || 'rgba(255,255,255,0.3)')
            .attr('stroke-width', 2)
            .style('filter', 'none');

        this.nodeGroup.selectAll('.status-indicator')
            .style('opacity', 0)
            .attr('r', 0);

        // Update execution count badges
        this.nodes.forEach(node => {
            if (node.type === 'agent') {
                const stats = this.nodeStats[node.id] || { count: 0 };
                const badge = this.nodeGroup.select(`.node-${node.id} .exec-count`);
                if (stats.count > 0) {
                    badge.style('opacity', 1);
                    badge.select('text').text(stats.count);
                }
            }
        });

        // Highlight active node
        if (nodeId) {
            const nodeData = this.nodes.find(n => n.id === nodeId);
            const isEndNode = nodeData && nodeData.type === 'end';
            const glowFilter = nodeId === 'fail' ? 'url(#glow-red)' : 'url(#glow-green)';

            if (nodeData && nodeData.type === 'agent') {
                // Highlight card with glow
                this.nodeGroup.select(`.node-${nodeId} .node-card`)
                    .attr('stroke', nodeData.color)
                    .attr('stroke-width', 3)
                    .style('filter', 'drop-shadow(0 0 20px ' + nodeData.color + ')')
                    .transition()
                    .duration(200)
                    .attr('stroke-width', 4)
                    .transition()
                    .duration(200)
                    .attr('stroke-width', 3);
            } else if (nodeData) {
                // Highlight circle (start/end)
                this.nodeGroup.select(`.node-${nodeId} .node-circle`)
                    .attr('stroke', nodeId === 'fail' ? '#ef4444' : '#10b981')
                    .attr('stroke-width', 3)
                    .style('filter', isEndNode ? glowFilter : 'url(#glow-green)')
                    .transition()
                    .duration(300)
                    .attr('r', 27)
                    .transition()
                    .duration(300)
                    .attr('r', 24);
            }

            // Pulsing indicator
            this.nodeGroup.select(`.node-${nodeId} .status-indicator`)
                .style('opacity', 1)
                .attr('fill', nodeId === 'fail' ? '#ef4444' : '#10b981')
                .transition()
                .duration(500)
                .attr('r', 8)
                .transition()
                .duration(500)
                .attr('r', 6)
                .on('end', function repeat() {
                    if (nodeId === self.currentNode && !isEndNode) {
                        d3.select(this)
                            .transition()
                            .duration(500)
                            .attr('r', 8)
                            .transition()
                            .duration(500)
                            .attr('r', 6)
                            .on('end', repeat);
                    }
                });
        }

        // Animate edges
        this.animateEdges(nodeId);
    }

    animateEdges(activeNode) {
        const self = this;

        // Reset all edges
        this.edgeGroup.selectAll('path')
            .attr('stroke', d => {
                if (d.type === 'retry') return 'rgba(234, 179, 8, 0.15)';
                if (d.type === 'fail') return 'rgba(239, 68, 68, 0.15)';
                return 'rgba(255,255,255,0.1)';
            })
            .attr('stroke-width', 2)
            .attr('marker-end', 'url(#arrow)');

        // Highlight incoming edges
        this.edges.forEach(edge => {
            if (edge.to === activeNode) {
                const color = edge.type === 'retry' ? '#eab308' :
                             edge.type === 'fail' ? '#ef4444' : '#10b981';
                const marker = edge.type === 'retry' ? 'url(#arrow-retry)' :
                              edge.type === 'fail' ? 'url(#arrow-fail)' : 'url(#arrow-active)';

                this.edgeGroup.select(`.edge-${edge.from}-${edge.to}`)
                    .attr('stroke', color)
                    .attr('marker-end', marker)
                    .transition()
                    .duration(500)
                    .attr('stroke-width', 3)
                    .transition()
                    .duration(500)
                    .attr('stroke-width', 2);
            }
        });
    }

    reset() {
        this.currentNode = null;
        this.history = [];
        this.nodeStats = {};
        this.startTime = null;
        this.iterationText.text('Iteration: 0');
        this.statusText.text('Status: Idle');
        this.timeText.text('Time: 0s');

        this.nodeGroup.selectAll('.node-card')
            .attr('stroke', d => d.color)
            .attr('stroke-width', 2)
            .style('filter', 'drop-shadow(0 4px 12px rgba(0, 0, 0, 0.3))');

        this.nodeGroup.selectAll('.node-circle')
            .attr('stroke', d => d.color || 'rgba(255,255,255,0.3)')
            .attr('stroke-width', 2)
            .style('filter', 'none');

        this.nodeGroup.selectAll('.status-indicator')
            .style('opacity', 0)
            .attr('r', 0);

        this.nodeGroup.selectAll('.exec-count')
            .style('opacity', 0)
            .select('text')
            .text('0');

        this.edgeGroup.selectAll('path')
            .attr('stroke', d => {
                if (d.type === 'retry') return 'rgba(234, 179, 8, 0.3)';
                if (d.type === 'fail') return 'rgba(239, 68, 68, 0.3)';
                return 'rgba(255,255,255,0.2)';
            })
            .attr('stroke-width', 3)
            .attr('marker-end', 'url(#arrow)');
    }

    onNodeClick(node) {
        // Show agent info modal
        this.showAgentInfoModal(node);
    }

    showAgentInfoModal(node) {
        const agentInfo = this.getAgentInfo(node.agent);
        const stats = this.nodeStats[node.id] || { count: 0, lastTime: null };

        // Create modal HTML
        const modalHTML = `
            <div id="agentInfoModal" class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-6">
                <div class="glass rounded-2xl border border-white/5 max-w-2xl w-full overflow-hidden">
                    <div class="px-6 py-4 border-b border-white/5 flex items-center justify-between" style="background: linear-gradient(135deg, ${node.color}15 0%, transparent 100%);">
                        <div class="flex items-center gap-3">
                            <div class="w-12 h-12 rounded-xl flex items-center justify-center text-2xl" style="background: ${node.color}20; color: ${node.color};">
                                ${this.getAgentIcon(node.agent)}
                            </div>
                            <div>
                                <h3 class="font-semibold text-lg">${node.label}</h3>
                                <p class="text-xs text-gray-500">${agentInfo.role}</p>
                            </div>
                        </div>
                        <button onclick="closeAgentInfoModal()" class="text-gray-500 hover:text-gray-300 transition-colors">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
                        </button>
                    </div>
                    <div class="px-6 py-5 space-y-4">
                        <!-- Purpose -->
                        <div>
                            <h4 class="text-sm font-semibold text-gray-400 mb-2">Purpose</h4>
                            <p class="text-sm text-gray-300 leading-relaxed">${agentInfo.purpose}</p>
                        </div>

                        <!-- How it works -->
                        <div>
                            <h4 class="text-sm font-semibold text-gray-400 mb-2">How It Works</h4>
                            <ul class="text-sm text-gray-300 space-y-1.5">
                                ${agentInfo.howItWorks.map(item => `<li class="flex items-start gap-2"><span class="text-${node.color.replace('#', '')} mt-0.5">•</span><span>${item}</span></li>`).join('')}
                            </ul>
                        </div>

                        <!-- Model info -->
                        <div>
                            <h4 class="text-sm font-semibold text-gray-400 mb-2">Model Configuration</h4>
                            <p class="text-xs text-gray-400 font-mono bg-white/5 px-3 py-2 rounded-lg">${agentInfo.model}</p>
                        </div>

                        <!-- Stats -->
                        <div class="grid grid-cols-2 gap-3 pt-3 border-t border-white/5">
                            <div class="glass rounded-xl border border-white/5 p-3">
                                <p class="text-xs text-gray-500 mb-1">Executions</p>
                                <p class="text-2xl font-bold" style="color: ${node.color};">${stats.count}</p>
                            </div>
                            <div class="glass rounded-xl border border-white/5 p-3">
                                <p class="text-xs text-gray-500 mb-1">Last Run</p>
                                <p class="text-sm font-medium text-gray-300">${stats.lastTime || 'Never'}</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remove existing modal if any
        const existingModal = document.getElementById('agentInfoModal');
        if (existingModal) {
            existingModal.remove();
        }

        // Add modal to body
        document.body.insertAdjacentHTML('beforeend', modalHTML);
    }

    getAgentInfo(agent) {
        const agentDetails = {
            retriever: {
                role: 'RAG Search Agent',
                purpose: 'Searches the ChromaDB knowledge base for relevant code examples that match the current task. Uses semantic similarity to find the top-5 most relevant examples from past successful implementations.',
                howItWorks: [
                    'Receives the user task description',
                    'Queries ChromaDB vector database using embeddings',
                    'Returns top-5 examples with similarity scores',
                    'Formats examples for Approver evaluation'
                ],
                model: 'Local 7B model (qwen2.5-coder:7b) - Fast retrieval'
            },
            approver: {
                role: 'RAG Evaluation Agent',
                purpose: 'Evaluates the relevance of retrieved examples and decides whether they should be used as templates. Acts as a quality gate to prevent low-quality examples from influencing code generation.',
                howItWorks: [
                    'Reviews examples from Retriever agent',
                    'Analyzes relevance to current task',
                    'Assigns confidence score (0.0-1.0)',
                    'Approves or rejects examples based on threshold (0.6)'
                ],
                model: 'Cloud model (gpt-4o-mini) - Strong reasoning for evaluation'
            },
            generator: {
                role: 'Code Generation Agent',
                purpose: 'Writes Lua code based on the task description. If approved examples exist, uses them as templates. Otherwise, generates code from scratch using its training knowledge.',
                howItWorks: [
                    'Receives task and optional approved template',
                    'Generates Lua code following best practices',
                    'Strips markdown code fences',
                    'Returns clean, executable Lua code'
                ],
                model: 'Local 7B model (qwen2.5-coder:7b) - Fast generation'
            },
            validator: {
                role: 'Code Validation Agent',
                purpose: 'Compiles and executes generated Lua code in a sandboxed environment. Catches syntax errors, runtime errors, and security violations before code review.',
                howItWorks: [
                    'Compiles code with luac',
                    'Executes in sandboxed Lua environment',
                    'Generates functional tests',
                    'Reports errors or success'
                ],
                model: 'Local 7B model (qwen2.5-coder:7b) - Fast validation'
            },
            reviewer: {
                role: 'Code Quality Agent',
                purpose: 'Performs final quality review of validated code. Checks for code quality, performance, maintainability, and best practices. Can request improvements or approve for completion.',
                howItWorks: [
                    'Reviews validated code',
                    'Checks quality and performance',
                    'Evaluates best practices',
                    'Approves or requests improvements'
                ],
                model: 'Cloud model (gpt-4o-mini) - Strong reasoning for quality review'
            },
            architect: {
                role: 'Project Architecture Agent',
                purpose: 'Plans the overall project structure for multi-file projects. Designs module organization, dependencies, and file layout.',
                howItWorks: [
                    'Analyzes project requirements',
                    'Designs module structure',
                    'Plans file organization',
                    'Creates architecture blueprint'
                ],
                model: 'Configured via settings.yaml'
            },
            specification: {
                role: 'Specification Agent',
                purpose: 'Creates detailed specifications for each module in the project. Defines interfaces, data structures, and implementation requirements.',
                howItWorks: [
                    'Receives architecture plan',
                    'Creates detailed specs per module',
                    'Defines interfaces and contracts',
                    'Prepares for implementation'
                ],
                model: 'Configured via settings.yaml'
            },
            integrator: {
                role: 'Integration Testing Agent',
                purpose: 'Tests integration between multiple modules in project mode. Ensures modules work together correctly.',
                howItWorks: [
                    'Tests module interactions',
                    'Validates interfaces',
                    'Checks data flow',
                    'Reports integration issues'
                ],
                model: 'Configured via settings.yaml'
            },
            decomposer: {
                role: 'Code Analysis Agent',
                purpose: 'Analyzes code structure and complexity. Identifies potential issues and optimization opportunities.',
                howItWorks: [
                    'Analyzes code structure',
                    'Measures complexity',
                    'Identifies issues',
                    'Suggests optimizations'
                ],
                model: 'Configured via settings.yaml'
            },
            evolver: {
                role: 'Code Optimization Agent',
                purpose: 'Optimizes and refines code for better performance and maintainability. Applies advanced optimization techniques.',
                howItWorks: [
                    'Reviews code performance',
                    'Applies optimizations',
                    'Refines implementation',
                    'Improves maintainability'
                ],
                model: 'Configured via settings.yaml'
            }
        };

        return agentDetails[agent] || {
            role: 'Unknown Agent',
            purpose: 'No information available',
            howItWorks: [],
            model: 'Not configured'
        };
    }

    getHistory() {
        return this.history;
    }

    getStats() {
        return this.nodeStats;
    }

    switchMode(mode) {
        this.mode = mode;
        this.nodes = this.mode === 'project' ? this.projectNodes : this.quickNodes;
        this.edges = this.mode === 'project' ? this.projectEdges : this.quickEdges;

        // Clear and redraw
        this.svg.selectAll('*').remove();
        this.init();
    }
}
