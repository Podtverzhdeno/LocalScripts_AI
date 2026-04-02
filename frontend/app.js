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
