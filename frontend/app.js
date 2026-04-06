/**
 * LocalScript — shared frontend utilities.
 */

// ── API helper ───────────────────────────────────────────────────────────────

async function api(url, options = {}) {
    const defaults = {
        headers: { 'Content-Type': 'application/json' },
    };
    const resp = await fetch(url, { ...defaults, ...options });
    if (!resp.ok) {
        let detail = `HTTP ${resp.status}`;
        try {
            const body = await resp.json();
            detail = body.detail || detail;
        } catch { /* ignore parse errors */ }
        throw new Error(detail);
    }
    return resp.json();
}

// ── HTML escaping ────────────────────────────────────────────────────────────

function escapeHtml(text) {
    const el = document.createElement('span');
    el.textContent = text;
    return el.innerHTML;
}

// ── Byte formatting ──────────────────────────────────────────────────────────

function formatBytes(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

// ── Mode switching ───────────────────────────────────────────────────────────

let currentMode = 'quick';

function switchMode(mode) {
    console.log('switchMode called with mode:', mode);
    currentMode = mode;

    const quickBtn = document.getElementById('quickModeBtn');
    const projectBtn = document.getElementById('projectModeBtn');
    const quickInput = document.getElementById('quickModeInput');
    const projectInput = document.getElementById('projectModeInput');
    const modeDescription = document.getElementById('modeDescription');
    const quickModeInfo = document.getElementById('quickModeInfo');
    const projectModeInfo = document.getElementById('projectModeInfo');

    console.log('Elements found:', {quickBtn, projectBtn, quickInput, projectInput});

    if (mode === 'quick') {
        quickBtn.classList.add('mode-btn-active');
        projectBtn.classList.remove('mode-btn-active');
        quickInput.classList.remove('hidden');
        projectInput.classList.add('hidden');
        if (quickModeInfo) quickModeInfo.classList.remove('hidden');
        if (projectModeInfo) projectModeInfo.classList.add('hidden');
        if (modeDescription) {
            modeDescription.textContent = 'Fast single-file generation — describe a task and get working Lua code in seconds.';
        }
    } else {
        projectBtn.classList.add('mode-btn-active');
        quickBtn.classList.remove('mode-btn-active');
        projectInput.classList.remove('hidden');
        quickInput.classList.add('hidden');
        if (quickModeInfo) quickModeInfo.classList.add('hidden');
        if (projectModeInfo) projectModeInfo.classList.remove('hidden');
        if (modeDescription) {
            modeDescription.textContent = 'Multi-file project with architecture planning and optional evolution cycles for continuous improvement.';
        }
    }
}

// ── Run project ──────────────────────────────────────────────────────────────

async function runProject() {
    const requirements = document.getElementById('projectRequirements').value.trim();
    const maxIterations = parseInt(document.getElementById('maxIterations').value);
    const evolutions = parseInt(document.getElementById('evolutions').value);
    const btn = document.getElementById('runProjectBtn');
    const errorEl = document.getElementById('taskError');
    const successEl = document.getElementById('taskSuccess');

    errorEl.classList.add('hidden');
    successEl.classList.add('hidden');

    if (!requirements) {
        errorEl.textContent = 'Please enter project requirements';
        errorEl.classList.remove('hidden');
        return;
    }

    btn.disabled = true;
    btn.innerHTML = '<svg class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> Creating Project...';

    try {
        const result = await api('/api/run-task', {
            method: 'POST',
            body: JSON.stringify({
                task: requirements,
                mode: 'project',
                max_iterations: maxIterations,
                evolutions: evolutions
            })
        });

        successEl.innerHTML = `
            <div class="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
                Project pipeline started!
                <a href="/session/${result.session_id}" class="underline font-medium hover:text-emerald-300">View session →</a>
            </div>`;
        successEl.classList.remove('hidden');

        document.getElementById('projectRequirements').value = '';
        loadSessions();

    } catch (err) {
        errorEl.innerHTML = `<span class="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-red-500/10 border border-red-500/20">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
            ${escapeHtml(err.message)}</span>`;
        errorEl.classList.remove('hidden');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/></svg> Create Project';
    }
}
