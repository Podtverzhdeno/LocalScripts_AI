/**
 * Interactive LangGraph visualization with d3.js
 * Enhanced version with detailed node info, execution timeline, and clickable nodes
 */

class PipelineGraph {
    constructor(containerId, mode = 'quick') {
        this.container = d3.select(`#${containerId}`);
        this.width = 900;
        this.height = 500;
        this.currentNode = null;
        this.history = [];
        this.nodeStats = {}; // Track execution count and timing per node
        this.mode = mode;

        // Quick mode: Generator → Validator → Reviewer
        this.quickNodes = [
            { id: 'start', label: 'START', x: 80, y: 250, type: 'start' },
            { id: 'generate', label: 'Generator', x: 280, y: 250, type: 'agent', agent: 'generator', desc: 'Writes Lua code' },
            { id: 'validate', label: 'Validator', x: 480, y: 250, type: 'agent', agent: 'validator', desc: 'Compiles & runs code' },
            { id: 'review', label: 'Reviewer', x: 680, y: 250, type: 'agent', agent: 'reviewer', desc: 'Quality check' },
            { id: 'fail', label: 'FAIL', x: 480, y: 380, type: 'end', color: '#ef4444' },
            { id: 'end', label: 'SUCCESS', x: 820, y: 250, type: 'end', color: '#10b981' }
        ];

        this.quickEdges = [
            { from: 'start', to: 'generate', label: '' },
            { from: 'generate', to: 'validate', label: '' },
            { from: 'validate', to: 'review', label: 'OK' },
            { from: 'validate', to: 'generate', label: 'errors', curve: true, type: 'retry' },
            { from: 'validate', to: 'fail', label: 'max iter', type: 'fail' },
            { from: 'review', to: 'end', label: 'approved' },
            { from: 'review', to: 'generate', label: 'improve', curve: true, type: 'retry' }
        ];

        // Project mode: Architect → Decomposer → Generator → Validator → Reviewer → Evolver
        this.projectNodes = [
            { id: 'start', label: 'START', x: 60, y: 250, type: 'start' },
            { id: 'architect', label: 'Architect', x: 160, y: 180, type: 'agent', agent: 'architect', desc: 'Designs system architecture' },
            { id: 'decomposer', label: 'Decomposer', x: 160, y: 320, type: 'agent', agent: 'decomposer', desc: 'Breaks down tasks' },
            { id: 'generate', label: 'Generator', x: 320, y: 250, type: 'agent', agent: 'generator', desc: 'Writes Lua code' },
            { id: 'validate', label: 'Validator', x: 480, y: 250, type: 'agent', agent: 'validator', desc: 'Compiles & runs code' },
            { id: 'review', label: 'Reviewer', x: 640, y: 250, type: 'agent', agent: 'reviewer', desc: 'Quality check' },
            { id: 'evolver', label: 'Evolver', x: 760, y: 180, type: 'agent', agent: 'evolver', desc: 'Optimizes & refines' },
            { id: 'fail', label: 'FAIL', x: 480, y: 400, type: 'end', color: '#ef4444' },
            { id: 'end', label: 'SUCCESS', x: 840, y: 250, type: 'end', color: '#10b981' }
        ];

        this.projectEdges = [
            { from: 'start', to: 'architect', label: '' },
            { from: 'start', to: 'decomposer', label: '' },
            { from: 'architect', to: 'generate', label: '' },
            { from: 'decomposer', to: 'generate', label: '' },
            { from: 'generate', to: 'validate', label: '' },
            { from: 'validate', to: 'review', label: 'OK' },
            { from: 'validate', to: 'generate', label: 'errors', curve: true, type: 'retry' },
            { from: 'validate', to: 'fail', label: 'max iter', type: 'fail' },
            { from: 'review', to: 'evolver', label: 'optimize' },
            { from: 'review', to: 'end', label: 'done' },
            { from: 'evolver', to: 'end', label: '' },
            { from: 'review', to: 'generate', label: 'improve', curve: true, type: 'retry' }
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

        // Info panel (top right)
        this.infoPanel = this.svg.append('g')
            .attr('class', 'info-panel')
            .attr('transform', `translate(${this.width - 180}, 20)`);

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
                if (d.type === 'retry') return 'rgba(234, 179, 8, 0.15)';
                if (d.type === 'fail') return 'rgba(239, 68, 68, 0.15)';
                return 'rgba(255,255,255,0.1)';
            })
            .attr('stroke-width', 2)
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
            .style('font-size', '10px')
            .style('font-weight', '500')
            .style('fill', '#6b7280')
            .style('pointer-events', 'none')
            .text(d => d.label);
    }

    getEdgePath(edge) {
        const from = this.nodes.find(n => n.id === edge.from);
        const to = this.nodes.find(n => n.id === edge.to);

        if (!from || !to) return '';

        const nodeRadius = 40;

        if (edge.curve) {
            // Curved path for feedback loops
            const midX = (from.x + to.x) / 2;
            const midY = from.y + 120;
            return `M ${from.x + nodeRadius} ${from.y} Q ${midX} ${midY} ${to.x - nodeRadius} ${to.y}`;
        }

        if (edge.from === 'validate' && edge.to === 'fail') {
            // Downward path
            return `M ${from.x} ${from.y + nodeRadius} L ${to.x} ${to.y - 25}`;
        }

        // For project mode: handle architect/decomposer to generator
        if ((edge.from === 'architect' || edge.from === 'decomposer') && edge.to === 'generate') {
            return `M ${from.x + nodeRadius} ${from.y} L ${to.x - nodeRadius} ${to.y}`;
        }

        // For project mode: handle review to evolver
        if (edge.from === 'review' && edge.to === 'evolver') {
            return `M ${from.x + nodeRadius/2} ${from.y - nodeRadius/2} L ${to.x - nodeRadius/2} ${to.y + nodeRadius/2}`;
        }

        // For project mode: handle evolver to end
        if (edge.from === 'evolver' && edge.to === 'end') {
            return `M ${from.x + nodeRadius/2} ${from.y + nodeRadius/2} L ${to.x - 25} ${to.y}`;
        }

        // For project mode: handle start to architect/decomposer
        if (edge.from === 'start' && (edge.to === 'architect' || edge.to === 'decomposer')) {
            return `M ${from.x + 25} ${from.y} L ${to.x - nodeRadius} ${to.y}`;
        }

        return `M ${from.x + nodeRadius} ${from.y} L ${to.x - nodeRadius} ${to.y}`;
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
                if (d.type === 'agent') {
                    self.showTooltip(event, d);
                }
            })
            .on('mousemove', function(event, d) {
                if (d.type === 'agent') {
                    self.moveTooltip(event);
                }
            })
            .on('mouseleave', function() {
                self.hideTooltip();
            });

        // Node background (larger circle for hover effect)
        nodeEnter.append('circle')
            .attr('r', d => d.type === 'start' || d.type === 'end' ? 25 : 40)
            .attr('class', 'node-bg')
            .attr('fill', 'transparent')
            .attr('stroke', 'none');

        // Node circles
        nodeEnter.append('circle')
            .attr('r', d => d.type === 'start' || d.type === 'end' ? 20 : 35)
            .attr('class', 'node-circle')
            .attr('fill', d => this.getNodeColor(d))
            .attr('stroke', d => d.color || 'rgba(255,255,255,0.2)')
            .attr('stroke-width', 2);

        // Node labels
        nodeEnter.append('text')
            .attr('text-anchor', 'middle')
            .attr('dy', d => d.type === 'agent' ? -8 : 5)
            .style('font-size', d => d.type === 'agent' ? '13px' : '11px')
            .style('font-weight', '600')
            .style('fill', '#fff')
            .style('pointer-events', 'none')
            .text(d => d.label);

        // Agent icons
        nodeEnter.filter(d => d.type === 'agent')
            .append('text')
            .attr('text-anchor', 'middle')
            .attr('dy', 18)
            .style('font-size', '20px')
            .style('pointer-events', 'none')
            .text(d => this.getAgentIcon(d.agent));

        // Execution count badge
        nodeEnter.filter(d => d.type === 'agent')
            .append('g')
            .attr('class', 'exec-count')
            .attr('transform', 'translate(28, -28)')
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
            .attr('cx', -28)
            .attr('cy', -28)
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
            architect: '🏗',
            decomposer: '🔨',
            generator: '⚡',
            validator: '✓',
            reviewer: '👁',
            evolver: '🔄'
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
            'architect': 'Designing architecture',
            'decomposer': 'Breaking down tasks',
            'generate': 'Generating code',
            'validate': 'Validating code',
            'review': 'Reviewing quality',
            'evolver': 'Optimizing code',
            'end': 'Completed ✓',
            'fail': 'Failed ✗'
        };
        this.statusText.text(`Status: ${statusMap[nodeId] || 'Running'}`);

        // Reset all nodes
        this.nodeGroup.selectAll('.node-circle')
            .attr('stroke', d => d.color || 'rgba(255,255,255,0.2)')
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

            this.nodeGroup.select(`.node-${nodeId} .node-circle`)
                .attr('stroke', nodeId === 'fail' ? '#ef4444' : '#10b981')
                .attr('stroke-width', 3)
                .style('filter', isEndNode ? glowFilter : 'url(#glow-green)')
                .transition()
                .duration(300)
                .attr('r', d => {
                    if (d.type === 'agent') return 38;
                    if (d.type === 'end') return 23;
                    return 22;
                })
                .transition()
                .duration(300)
                .attr('r', d => {
                    if (d.type === 'agent') return 35;
                    if (d.type === 'end') return 20;
                    return 20;
                });

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

        this.nodeGroup.selectAll('.node-circle')
            .attr('stroke', d => d.color || 'rgba(255,255,255,0.2)')
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
                if (d.type === 'retry') return 'rgba(234, 179, 8, 0.15)';
                if (d.type === 'fail') return 'rgba(239, 68, 68, 0.15)';
                return 'rgba(255,255,255,0.1)';
            })
            .attr('stroke-width', 2)
            .attr('marker-end', 'url(#arrow)');
    }

    onNodeClick(node) {
        // Emit custom event for parent to handle
        const event = new CustomEvent('nodeClick', {
            detail: {
                nodeId: node.id,
                agent: node.agent,
                stats: this.nodeStats[node.id] || { count: 0 }
            }
        });
        this.container.node().dispatchEvent(event);
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
