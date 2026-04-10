/**
 * Interactive modals handler for clarification and checkpoint
 */

// State
let clarificationData = null;
let checkpointData = null;
let selectedAlternative = null;

// ── Clarification Modal ──────────────────────────────────────────────────────

function showClarificationModal(data) {
    clarificationData = data;
    const modal = document.getElementById('clarificationModal');
    const taskEl = document.getElementById('clarificationTask');
    const questionsEl = document.getElementById('clarificationQuestions');

    // Set task
    taskEl.textContent = data.task || 'Unknown task';

    // Render questions
    questionsEl.innerHTML = data.questions.map((q, i) => `
        <div class="space-y-2">
            <label class="block text-sm font-medium text-gray-300">
                ${q.required ? '<span class="text-red-400">*</span> ' : ''}
                ${escapeHtml(q.question)}
            </label>
            <div class="space-y-2">
                ${q.options.map((opt, j) => `
                    <label class="flex items-center gap-3 px-4 py-3 rounded-lg bg-white/5 hover:bg-white/10 cursor-pointer transition-all border border-white/10 hover:border-emerald-500/30">
                        <input
                            type="radio"
                            name="question_${i}"
                            value="${escapeHtml(opt)}"
                            class="w-4 h-4 text-emerald-500 focus:ring-emerald-500 focus:ring-offset-0"
                        >
                        <span class="text-sm text-gray-300">${escapeHtml(opt)}</span>
                    </label>
                `).join('')}
                <label class="flex items-center gap-3 px-4 py-3 rounded-lg bg-white/5 hover:bg-white/10 cursor-pointer transition-all border border-white/10 hover:border-amber-500/30">
                    <input
                        type="radio"
                        name="question_${i}"
                        value="__other__"
                        class="w-4 h-4 text-amber-500 focus:ring-amber-500 focus:ring-offset-0"
                        onchange="toggleOtherInput(${i}, this.checked)"
                    >
                    <span class="text-sm text-gray-300">Other:</span>
                    <input
                        type="text"
                        id="other_${i}"
                        placeholder="Specify..."
                        disabled
                        class="flex-1 bg-transparent border-b border-white/20 px-2 py-1 text-sm text-gray-300 placeholder-gray-600 focus:outline-none focus:border-amber-500 disabled:opacity-50"
                    >
                </label>
            </div>
        </div>
    `).join('');

    modal.classList.remove('hidden');
    addLog('info', 'Clarification', `Showing ${data.questions.length} question(s)`);
}

function toggleOtherInput(questionIndex, checked) {
    const input = document.getElementById(`other_${questionIndex}`);
    input.disabled = !checked;
    if (checked) {
        input.focus();
    }
}

function skipClarification() {
    const modal = document.getElementById('clarificationModal');
    modal.classList.add('hidden');
    addLog('info', 'Clarification', 'User skipped questions');
}

async function submitClarification() {
    const answers = {};
    const questions = clarificationData.questions;

    // Collect answers
    for (let i = 0; i < questions.length; i++) {
        const selected = document.querySelector(`input[name="question_${i}"]:checked`);

        if (!selected && questions[i].required) {
            alert(`Please answer question ${i + 1}`);
            return;
        }

        if (selected) {
            if (selected.value === '__other__') {
                const otherInput = document.getElementById(`other_${i}`);
                answers[i.toString()] = otherInput.value.trim() || selected.value;
            } else {
                answers[i.toString()] = selected.value;
            }
        }
    }

    addLog('info', 'Clarification', `Submitting ${Object.keys(answers).length} answer(s)`);

    try {
        await api(`/api/session/${SESSION_ID}/clarification`, {
            method: 'POST',
            body: JSON.stringify({ answers })
        });

        document.getElementById('clarificationModal').classList.add('hidden');
        addLog('success', 'Clarification', 'Answers submitted successfully');
    } catch (err) {
        addLog('error', 'Clarification', `Failed to submit: ${err.message}`);

        // Show user-friendly error with retry option
        const retry = confirm(`Failed to submit answers: ${err.message}\n\nWould you like to try again?`);
        if (retry) {
            // Retry after 1 second
            setTimeout(() => submitClarification(), 1000);
        }
    }
}

// ── Checkpoint Modal ─────────────────────────────────────────────────────────

function showCheckpointModal(data) {
    checkpointData = data;
    const modal = document.getElementById('checkpointModal');

    // Set code
    document.getElementById('checkpointCode').textContent = data.code || '// No code available';

    // Set test results
    if (data.test_results) {
        const { total, passed } = data.test_results;
        document.getElementById('checkpointTestsCount').textContent = `${passed}/${total} passed`;
    }

    // Set performance
    if (data.profile_metrics) {
        document.getElementById('checkpointTime').textContent = `${data.profile_metrics.time.toFixed(3)}s`;
    }

    modal.classList.remove('hidden');
    addLog('info', 'Checkpoint', `Code ready for review (iteration ${data.iteration})`);
}

function copyCheckpointCode() {
    const code = document.getElementById('checkpointCode').textContent;
    navigator.clipboard.writeText(code).then(() => {
        addLog('success', 'Checkpoint', 'Code copied to clipboard');
    });
}

async function checkpointAction(action) {
    addLog('info', 'Checkpoint', `User action: ${action}`);

    if (action === 'reject') {
        // Show feedback section
        document.getElementById('feedbackSection').classList.remove('hidden');
        document.getElementById('checkpointActions').innerHTML = `
            <button onclick="cancelFeedback()" class="flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-gray-500/10 border border-gray-500/20 text-gray-400 hover:bg-gray-500/20 transition-all font-medium text-sm">
                Cancel
            </button>
            <button onclick="submitFeedback()" class="flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 hover:bg-emerald-500/20 transition-all font-medium text-sm">
                Submit Changes
            </button>
        `;
        return;
    }

    if (action === 'alternatives') {
        // Request alternatives
        try {
            await api(`/api/session/${SESSION_ID}/checkpoint`, {
                method: 'POST',
                body: JSON.stringify({ action: 'alternatives' })
            });

            // Show loading state
            document.getElementById('alternativesSection').classList.remove('hidden');
            document.getElementById('alternativesList').innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    <svg class="w-8 h-8 mx-auto mb-2 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <p class="text-sm">Generating alternatives...</p>
                </div>
            `;

            addLog('info', 'Checkpoint', 'Generating alternative implementations');
        } catch (err) {
            addLog('error', 'Checkpoint', `Failed: ${err.message}`);

            const retry = confirm(`Failed to generate alternatives: ${err.message}\n\nWould you like to try again?`);
            if (retry) {
                setTimeout(() => checkpointAction('alternatives'), 1000);
            }
        }
        return;
    }

    // Submit action
    try {
        await api(`/api/session/${SESSION_ID}/checkpoint`, {
            method: 'POST',
            body: JSON.stringify({ action })
        });

        document.getElementById('checkpointModal').classList.add('hidden');

        if (action === 'save_to_kb') {
            addLog('success', 'Checkpoint', 'Code approved and saved to knowledge base!');
        } else {
            addLog('success', 'Checkpoint', `Action '${action}' submitted`);
        }
    } catch (err) {
        addLog('error', 'Checkpoint', `Failed: ${err.message}`);

        const retry = confirm(`Failed to submit action: ${err.message}\n\nWould you like to try again?`);
        if (retry) {
            setTimeout(() => checkpointAction(action), 1000);
        }
    }
}

function cancelFeedback() {
    document.getElementById('feedbackSection').classList.add('hidden');
    // Restore original buttons
    document.getElementById('checkpointActions').innerHTML = `
        <button onclick="checkpointAction('approve')" class="flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 hover:bg-emerald-500/20 transition-all font-medium text-sm">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
            </svg>
            Approve & Continue
        </button>
        <button onclick="checkpointAction('reject')" class="flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-orange-500/10 border border-orange-500/20 text-orange-400 hover:bg-orange-500/20 transition-all font-medium text-sm">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
            </svg>
            Request Changes
        </button>
        <button onclick="checkpointAction('alternatives')" class="flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 hover:bg-cyan-500/20 transition-all font-medium text-sm">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01"/>
            </svg>
            Generate Alternatives
        </button>
        <button onclick="checkpointAction('save_to_kb')" class="flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-violet-500/10 border border-violet-500/20 text-violet-400 hover:bg-violet-500/20 transition-all font-medium text-sm">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"/>
            </svg>
            Approve & Save to KB
        </button>
    `;
}

async function submitFeedback() {
    const feedback = document.getElementById('checkpointFeedback').value.trim();

    if (!feedback) {
        alert('Please provide feedback');
        return;
    }

    try {
        await api(`/api/session/${SESSION_ID}/checkpoint`, {
            method: 'POST',
            body: JSON.stringify({
                action: 'reject',
                feedback: feedback
            })
        });

        document.getElementById('checkpointModal').classList.add('hidden');
        addLog('success', 'Checkpoint', 'Feedback submitted, regenerating code');
    } catch (err) {
        addLog('error', 'Checkpoint', `Failed: ${err.message}`);

        const retry = confirm(`Failed to submit feedback: ${err.message}\n\nWould you like to try again?`);
        if (retry) {
            setTimeout(() => submitFeedback(), 1000);
        }
    }
}

function showAlternatives(alternatives) {
    const listEl = document.getElementById('alternativesList');

    listEl.innerHTML = alternatives.map((code, i) => `
        <label class="block cursor-pointer">
            <input
                type="radio"
                name="alternative"
                value="${i}"
                onchange="selectedAlternative = ${i}"
                class="hidden peer"
            >
            <div class="p-4 rounded-lg bg-white/5 border border-white/10 peer-checked:border-emerald-500 peer-checked:bg-emerald-500/10 hover:bg-white/10 transition-all">
                <div class="flex items-center justify-between mb-2">
                    <span class="text-sm font-medium text-gray-300">Alternative ${i + 1}</span>
                    <svg class="w-5 h-5 text-emerald-400 hidden peer-checked:block" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                    </svg>
                </div>
                <pre class="text-xs text-gray-400 font-mono max-h-32 overflow-y-auto">${escapeHtml(code)}</pre>
            </div>
        </label>
    `).join('');

    // Update actions
    document.getElementById('checkpointActions').innerHTML = `
        <button onclick="cancelAlternatives()" class="flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-gray-500/10 border border-gray-500/20 text-gray-400 hover:bg-gray-500/20 transition-all font-medium text-sm">
            Cancel
        </button>
        <button onclick="selectAlternative()" class="flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 hover:bg-emerald-500/20 transition-all font-medium text-sm">
            Use Selected
        </button>
    `;
}

function cancelAlternatives() {
    document.getElementById('alternativesSection').classList.add('hidden');
    cancelFeedback(); // Restore original buttons
}

async function selectAlternative() {
    if (selectedAlternative === null) {
        alert('Please select an alternative');
        return;
    }

    try {
        await api(`/api/session/${SESSION_ID}/checkpoint`, {
            method: 'POST',
            body: JSON.stringify({
                action: 'alternatives',
                selected_alternative: selectedAlternative
            })
        });

        document.getElementById('checkpointModal').classList.add('hidden');
        addLog('success', 'Checkpoint', `Selected alternative ${selectedAlternative + 1}`);
    } catch (err) {
        addLog('error', 'Checkpoint', `Failed: ${err.message}`);

        const retry = confirm(`Failed to select alternative: ${err.message}\n\nWould you like to try again?`);
        if (retry) {
            setTimeout(() => selectAlternative(), 1000);
        }
    }
}

// ── WebSocket event handlers ─────────────────────────────────────────────────

function handleClarificationRequired(data) {
    showClarificationModal({
        task: data.task || 'Unknown',
        questions: data.questions || []
    });
}

function handleCheckpointRequired(data) {
    showCheckpointModal(data.data || data);
}

// Export for use in session.html
if (typeof window !== 'undefined') {
    window.showClarificationModal = showClarificationModal;
    window.showCheckpointModal = showCheckpointModal;
    window.handleClarificationRequired = handleClarificationRequired;
    window.handleCheckpointRequired = handleCheckpointRequired;
    window.showAlternatives = showAlternatives;
}
