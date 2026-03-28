const API_BASE = '';

let allTasks = [];
let selectedTaskId = null;
let selectedTaskText = null;

// Elements
const elTabs = document.querySelectorAll('.tab');
const elSystemTasksList = document.getElementById('tasks-list');
const elEnvTasksList = document.getElementById('env-tasks');
const elEnvStep = document.getElementById('env-step');
const elMetrics = document.getElementById('metrics-container');
const elLogs = document.getElementById('logs-container');
const elToast = document.getElementById('toast');

async function init() {
    setupEventListeners();
    await fetchSystemTasks();
    await fetchState();
    await fetchMemory();
}

function setupEventListeners() {
    document.getElementById('btn-reset').addEventListener('click', handleReset);
    document.getElementById('btn-baseline').addEventListener('click', handleBaseline);
    document.getElementById('action-form').addEventListener('submit', handleManualAction);
    document.getElementById('btn-run-pipeline').addEventListener('click', handleRunPipeline);
    document.getElementById('btn-run-agent').addEventListener('click', handleClassifyOnly);
    elTabs.forEach(tab => tab.addEventListener('click', (e) => {
        elTabs.forEach(t => t.classList.remove('active'));
        e.target.classList.add('active');
        renderSystemTasks(e.target.dataset.difficulty);
    }));
}

// ─── Toast ────────────────────────────────────────────────────────
function showToast(message, sub = '') {
    elToast.innerHTML = `
        <div class="toast-title">Simulation Pulse</div>
        <div>${message}</div>
        ${sub ? `<div class="toast-sub">"${sub}"</div>` : ''}
    `;
    elToast.classList.add('show');
    setTimeout(() => elToast.classList.remove('show'), 6000);
}

// ─── Fetching ────────────────────────────────────────────────────
async function fetchSystemTasks() {
    try {
        const res = await fetch(`${API_BASE}/tasks`);
        const data = await res.json();
        allTasks = data.tasks;
        renderSystemTasks('easy');
    } catch (err) { console.error('Tasks fetch failed', err); }
}

async function fetchState() {
    try {
        const res = await fetch(`${API_BASE}/state`);
        const state = await res.json();
        updateDashboard(state);
    } catch (err) { console.error('State fetch failed', err); }
}

async function fetchMemory() {
    try {
        const res = await fetch(`${API_BASE}/memory`);
        const data = await res.json();
        renderMemory(data);
    } catch (err) { /* Memory endpoint optional */ }
}

// ─── Handlers ────────────────────────────────────────────────────
async function handleReset(e) {
    const btn = e.target; btn.textContent = 'Resetting...';
    try {
        const res = await fetch(`${API_BASE}/reset`, { method: 'POST' });
        updateDashboard(await res.json());
        resetPipelineUI();
        showToast('Workplace environment has been reset.');
    } catch { showToast('Reset failed.'); }
    finally { btn.textContent = 'Reset'; }
}

async function handleBaseline() {
    const btn = document.getElementById('btn-baseline');
    btn.textContent = 'Running...'; btn.disabled = true;
    try {
        const res = await fetch(`${API_BASE}/baseline`);
        const data = await res.json();
        showToast(`Baseline Complete — Score: ${data.score.toFixed(3)}`);
        await fetchState(); await fetchMemory();
    } catch { showToast('Baseline failed.'); }
    finally { btn.textContent = 'Run Baseline'; btn.disabled = false; }
}

async function handleRunPipeline() {
    if (!selectedTaskId) { showToast('Select a task from the inbox first.'); return; }
    const btn = document.getElementById('btn-run-pipeline');
    btn.textContent = '⚡ Running Pipeline...'; btn.disabled = true;
    resetPipelineUI();

    try {
        // Animate stage-by-stage
        setStageState('classify', 'running');
        const res = await fetch(`${API_BASE}/run-pipeline`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ task_id: selectedTaskId, task_text: selectedTaskText })
        });
        const data = await res.json();

        // Render each stage with a stagger for visual effect
        await animateStages(data);
        renderPipelineResult(data);

        if (data.observation) updateDashboard(data.observation);
        await fetchMemory();

        showToast(
            `Pipeline Complete ✓ — Reward: ${data.reward?.toFixed(3) ?? '–'}`,
            data.feedback
        );
    } catch (err) {
        setStageState('classify', 'error');
        showToast('Pipeline execution failed. Check server logs.');
        console.error(err);
    } finally {
        btn.textContent = '⚡ Run Full Agent Pipeline'; btn.disabled = false;
    }
}

async function handleClassifyOnly() {
    if (!selectedTaskId) { showToast('Select a task first.'); return; }
    const btn = document.getElementById('btn-run-agent');
    btn.textContent = 'Analyzing...'; btn.disabled = true;

    try {
        const res = await fetch(`${API_BASE}/run-agent`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ task_id: selectedTaskId, task_text: selectedTaskText })
        });
        const data = await res.json();

        // Pre-fill form
        document.getElementById('action-task-id').value = selectedTaskId;
        document.getElementById('action-type').value = data.action_type;
        document.getElementById('action-tool').value = data.tool;
        document.getElementById('action-message').value = data.reasoning;

        setStageState('classify', 'done');
        document.getElementById('stage-classify-output').textContent =
            `${data.category} · ${(data.confidence * 100).toFixed(0)}% conf`;

        showToast(`Classified: ${data.category.toUpperCase()} (${(data.confidence * 100).toFixed(0)}% confidence)`);
    } catch { showToast('Classification failed.'); }
    finally { btn.textContent = '🔍 Classify Only'; btn.disabled = false; }
}

async function handleManualAction(e) {
    e.preventDefault();
    const action = {
        task_id: document.getElementById('action-task-id').value,
        action_type: document.getElementById('action-type').value,
        tool: document.getElementById('action-tool').value,
        message: document.getElementById('action-message').value,
        reason: document.getElementById('action-message').value,
        metadata: {}
    };
    try {
        const res = await fetch(`${API_BASE}/step`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(action)
        });
        const data = await res.json();
        updateDashboard(data.observation);
        const fb = data.info?.grader?.feedback || '';
        showToast(`Dispatched — Reward: ${data.reward.toFixed(3)}`, fb);
        document.getElementById('action-form').reset();
    } catch { showToast('Dispatch failed. Verify form fields.'); }
}

// ─── Pipeline Animation ──────────────────────────────────────────
async function animateStages(data) {
    const delay = ms => new Promise(r => setTimeout(r, ms));

    setStageState('classify', 'done');
    document.getElementById('stage-classify-output').textContent =
        `${data.category} · ${(data.confidence * 100).toFixed(0)}% conf`;
    await delay(350);

    setStageState('plan', 'done');
    document.getElementById('stage-plan-output').textContent =
        `→ ${data.tool}`;
    await delay(350);

    setStageState('exec', data.status === 'completed' ? 'done' : (data.status === 'failed' ? 'error' : 'partial'));
    document.getElementById('stage-exec-output').textContent =
        `${data.status} · ${data.reward?.toFixed(2) ?? '?'}`;
    await delay(200);
}

function setStageState(stage, state) {
    const el = document.getElementById(`stage-${stage}`);
    if (!el) return;
    el.classList.remove('running', 'done', 'error', 'partial');
    el.classList.add(state);
}

function resetPipelineUI() {
    ['classify', 'plan', 'exec'].forEach(s => {
        setStageState(s, '');
        const out = document.getElementById(`stage-${s}-output`);
        if (out) out.textContent = 'Waiting...';
    });
    const pr = document.getElementById('pipeline-result');
    if (pr) { pr.classList.add('hidden'); pr.innerHTML = ''; }
}

function renderPipelineResult(data) {
    const el = document.getElementById('pipeline-result');
    if (!el) return;
    el.classList.remove('hidden');

    const statusColor = data.status === 'completed' ? '#3fb950' : data.status === 'failed' ? '#f85149' : '#d29922';

    el.innerHTML = `
        <div class="result-header">
            <span class="result-status-badge" style="background: ${statusColor}22; color: ${statusColor}; border-color: ${statusColor}44;">
                ${data.status?.toUpperCase() ?? 'UNKNOWN'}
            </span>
            <span class="timing-badge">⏱ ${data.total_ms}ms</span>
            ${data.used_llm ? '<span class="llm-badge">🤖 LLM Powered</span>' : '<span class="llm-badge rule">📐 Rule Engine</span>'}
        </div>
        ${data.memory_hint ? `<div class="memory-hint-inline">💡 ${data.memory_hint}</div>` : ''}
        <div class="result-steps">
            ${(data.steps || []).map((s, i) => `
                <div class="step-item" style="animation-delay: ${i * 0.1}s">
                    <span class="step-num">${i + 1}</span>
                    <span>${s}</span>
                </div>
            `).join('')}
        </div>
        <div class="result-metrics">
            <div class="mini-metric"><span>${(data.accuracy * 100).toFixed(0)}%</span>Accuracy</div>
            <div class="mini-metric"><span>${(data.efficiency * 100).toFixed(0)}%</span>Efficiency</div>
            <div class="mini-metric"><span>${data.reward?.toFixed(3) ?? '–'}</span>Reward</div>
            <div class="mini-metric"><span>${(data.confidence * 100).toFixed(0)}%</span>Confidence</div>
        </div>
        <div class="result-feedback">"${data.feedback}"</div>
    `;
}

// ─── Rendering ───────────────────────────────────────────────────
function renderSystemTasks(difficulty) {
    const tasks = allTasks.filter(t => t.difficulty === difficulty);
    if (!tasks.length) {
        elSystemTasksList.innerHTML = '<p class="text-muted">Inbox empty.</p>';
        return;
    }
    elSystemTasksList.innerHTML = tasks.map(t => `
        <div class="task-card" id="tc-${t.task_id}" onclick="selectTask('${t.task_id}', \`${t.input.replace(/`/g, "'")}\`)" style="cursor:pointer">
            <div class="task-header">
                <span class="task-sender">${t.sender || 'System'}</span>
                <span class="priority-badge priority-${t.priority}">${t.priority}</span>
            </div>
            <div class="task-input">${t.input}</div>
            <div class="task-meta"><span>${t.task_id}</span></div>
        </div>
    `).join('');
}

function selectTask(taskId, taskText) {
    selectedTaskId = taskId; selectedTaskText = taskText;
    document.getElementById('action-task-id').value = taskId;
    document.querySelectorAll('.task-card').forEach(c => c.classList.remove('selected'));
    const card = document.getElementById(`tc-${taskId}`);
    if (card) card.classList.add('selected');
    resetPipelineUI();
    showToast(`${taskId} selected. Click "Run Full Agent Pipeline".`);
}

function updateDashboard(state) {
    elEnvStep.textContent = state.step_count;

    const pending = state.tasks.filter(t => t.status !== 'completed');
    elEnvTasksList.innerHTML = pending.length === 0
        ? '<div style="text-align:center;padding:2rem;opacity:.6"><div style="font-size:2rem">✨</div><p>All tasks resolved.</p></div>'
        : pending.map(t => `
            <div class="task-card">
                <div class="task-header">
                    <span class="task-sender">${t.sender || 'Unknown'}</span>
                    <span class="priority-badge priority-${t.priority}">${t.priority}</span>
                </div>
                <div class="task-input">${t.input}</div>
                <div class="task-meta"><span>${t.task_id}</span><span>⏰ ${t.deadline} steps</span></div>
            </div>`).join('');

    const metricLabels = { overall_accuracy: 'Accuracy', overall_efficiency: 'Efficiency', total_reward: 'Total Reward' };
    const metrics = state.performance_metrics || {};
    elMetrics.innerHTML = Object.entries(metrics).map(([k, v]) => `
        <div class="metric-box">
            <div class="metric-value">${typeof v === 'number' ? v.toFixed(2) : v}</div>
            <div class="metric-label">${metricLabels[k] || k.replace(/_/g, ' ').toUpperCase()}</div>
        </div>`).join('') || '<p class="text-muted">Awaiting data.</p>';

    const logs = state.agent_logs || [];
    elLogs.innerHTML = logs.length === 0
        ? '<p class="text-muted">Awaiting agent activity...</p>'
        : logs.slice().reverse().map(l => `
            <div class="chat-bubble">
                <img src="${l.avatar || `https://i.pravatar.cc/150?u=${l.from || l.from_agent}`}" class="avatar" alt="avatar" onerror="this.style.display='none'">
                <div class="bubble-content">
                    <div class="bubble-author">${l.from || l.from_agent || 'Agent'}</div>
                    <div class="bubble-msg">${l.message}</div>
                </div>
            </div>`).join('');
}

function renderMemory(data) {
    const statsEl = document.getElementById('memory-stats');
    const logEl = document.getElementById('memory-log');
    if (!statsEl) return;

    const s = data.stats || {};
    statsEl.innerHTML = s.total_tasks > 0 ? `
        <div class="mem-stats-grid">
            <div class="mem-stat"><span>${s.total_tasks}</span>Tasks</div>
            <div class="mem-stat"><span>${(s.success_rate * 100).toFixed(0)}%</span>Success</div>
            <div class="mem-stat"><span>${s.avg_reward?.toFixed(2) ?? '–'}</span>Avg Reward</div>
            <div class="mem-stat"><span>${s.top_category ?? '–'}</span>Top Type</div>
        </div>` : '<p class="text-muted">No memory entries yet.</p>';

    if (logEl && data.recent) {
        logEl.innerHTML = data.recent.slice().reverse().slice(0, 4).map(e => `
            <div class="mem-entry">
                <span class="mem-badge priority-${e.status === 'completed' ? 'low' : 'high'}">${e.status}</span>
                <span class="mem-text">${e.task_id} — ${e.category}</span>
            </div>`).join('') || '';
    }
}

init();
