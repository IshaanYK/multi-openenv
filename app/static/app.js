const API_BASE = '';

let allTasks = { easy: [], medium: [], hard: [] };
let currentEnvState = null;

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
}

function setupEventListeners() {
    document.getElementById('btn-reset').addEventListener('click', handleReset);
    document.getElementById('btn-baseline').addEventListener('click', handleBaseline);
    document.getElementById('action-form').addEventListener('submit', handleAction);

    elTabs.forEach(tab => {
        tab.addEventListener('click', (e) => {
            elTabs.forEach(t => t.classList.remove('active'));
            e.target.classList.add('active');
            renderSystemTasks(e.target.dataset.difficulty);
        });
    });
}

function showToast(message, type = 'success') {
    elToast.textContent = message;
    elToast.style.borderLeftColor = type === 'error' ? '#ef4444' : '#10b981';
    elToast.classList.add('show');
    setTimeout(() => elToast.classList.remove('show'), 3000);
}

// Data Fetching
async function fetchSystemTasks() {
    try {
        const res = await fetch(`${API_BASE}/tasks`);
        const data = await res.json();
        // The API now returns { "tasks": [...], "action_schema": {...} }
        // We can group them by difficulty if needed, but let's assume they have it or just show all
        // For simplicity, let's store them and filter in render
        allTasks = data.tasks; 
        renderSystemTasks('easy'); // Default view
    } catch (err) {
        console.error('Failed to fetch tasks', err);
    }
}

async function fetchState() {
    try {
        const res = await fetch(`${API_BASE}/state`);
        currentEnvState = await res.json();
        updateDashboard(currentEnvState);
    } catch (err) {
        console.error('Failed to fetch state', err);
    }
}

// Handlers
async function handleReset(e) {
    const btn = e.target;
    btn.textContent = 'Resetting...';
    try {
        const res = await fetch(`${API_BASE}/reset`, { method: 'POST' });
        const state = await res.json();
        updateDashboard(state);
        showToast('Environment reset successful.');
    } catch (err) {
        showToast('Reset failed.', 'error');
    } finally {
        btn.textContent = 'Reset Environment';
    }
}

async function handleBaseline() {
    try {
        const res = await fetch(`${API_BASE}/baseline`);
        const data = await res.json();
        showToast(`Baseline Agent finished! Score: ${data.score.toFixed(2)}`);
        fetchState();
    } catch (err) {
        showToast('Baseline run failed.', 'error');
    }
}

async function handleAction(e) {
    e.preventDefault();
    const action = {
        task_id: document.getElementById('action-task-id').value,
        action_type: document.getElementById('action-type').value,
        tool: document.getElementById('action-tool').value,
        message: document.getElementById('action-message').value,
        metadata: {},
        reason: ""
    };

    try {
        const res = await fetch(`${API_BASE}/step`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(action)
        });
        const data = await res.json();
        updateDashboard(data.observation);
        showToast(`Step processed! Reward: ${data.reward.toFixed(2)}`);
        document.getElementById('action-form').reset();
    } catch (err) {
        showToast('Action failed.', 'error');
    }
}

// Rendering
function renderSystemTasks(difficulty) {
    // If the tasks in the new API don't have difficulty, we might need to handle that.
    // Assuming for now they might have it, or we just show them.
    const tasks = allTasks.filter(t => !difficulty || t.difficulty === difficulty || difficulty === 'all');
    
    if (tasks.length === 0) {
        elSystemTasksList.innerHTML = '<p class="text-muted">No tasks available.</p>';
        return;
    }

    elSystemTasksList.innerHTML = tasks.map(t => `
        <div class="task-card" onclick="document.getElementById('action-task-id').value = '${t.id || t.task_id || ''}'" style="cursor: pointer;">
            <div class="task-header">
                <span class="task-id">${t.id || t.task_id || 'N/A'}</span>
            </div>
            <div class="task-input">${t.input || t.description || ''}</div>
        </div>
    `).join('');
}

function updateDashboard(state) {
    elEnvStep.textContent = state.step_count;
    
    // Render Pending Tasks
    const pendingTasks = state.tasks.filter(t => t.status !== 'completed');
    if (pendingTasks.length === 0) {
        elEnvTasksList.innerHTML = '<p class="text-muted">No pending tasks! Good job.</p>';
    } else {
        elEnvTasksList.innerHTML = pendingTasks.map(t => `
            <div class="task-card">
                <div class="task-header">
                    <span class="task-id">${t.task_id}</span>
                    <span class="priority-badge priority-${t.priority}">${t.priority}</span>
                </div>
                <div class="task-input">${t.input}</div>
                <div class="task-meta">
                    <span>Deadline: ${t.deadline}</span>
                    <span>Status: ${t.status}</span>
                </div>
            </div>
        `).join('');
    }

    // Render Metrics
    const metrics = state.performance_metrics || {};
    if (Object.keys(metrics).length === 0) {
        elMetrics.innerHTML = '<p class="text-muted">No metrics yet.</p>';
    } else {
        elMetrics.innerHTML = Object.entries(metrics).map(([key, val]) => `
            <div class="metric-box">
                <div class="metric-value">${typeof val === 'number' ? val.toFixed(2) : val}</div>
                <div class="metric-label">${key.replace(/_/g, ' ')}</div>
            </div>
        `).join('');
    }

    // Render Logs
    const logs = state.agent_logs || [];
    if (logs.length === 0) {
        elLogs.innerHTML = '<p class="text-muted">No logs recorded.</p>';
    } else {
        elLogs.innerHTML = logs.slice().reverse().map(l => `
            <div class="log-entry">
                <div class="log-agents">${l.from || l.from_agent} → ${l.to || l.to_agent}</div>
                <div class="log-msg">${l.message}</div>
            </div>
        `).join('');
    }
}

// Start
init();
