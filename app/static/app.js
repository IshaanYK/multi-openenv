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

function showToast(message, feedback = '') {
    elToast.innerHTML = `
        <div style="font-weight:700; margin-bottom: 0.25rem;">Simulation Pulse</div>
        <div>${message}</div>
        ${feedback ? `<div class="feedback-text">"${feedback}"</div>` : ''}
    `;
    elToast.classList.add('show');
    setTimeout(() => elToast.classList.remove('show'), 5000);
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
    btn.textContent = 'Recalibrating...';
    try {
        const res = await fetch(`${API_BASE}/reset`, { method: 'POST' });
        const state = await res.json();
        updateDashboard(state);
        showToast('Workplace environment has been reset.');
    } catch (err) {
        showToast('Calibration failed.');
    } finally {
        btn.textContent = 'Reset Environment';
    }
}

async function handleBaseline() {
    try {
        const res = await fetch(`${API_BASE}/baseline`);
        const data = await res.json();
        showToast(`Baseline Run: Efficiency Score ${data.score.toFixed(2)}`);
        fetchState();
    } catch (err) {
        showToast('Baseline trial failed.');
    }
}

async function handleAction(e) {
    e.preventDefault();
    const action = {
        task_id: document.getElementById('action-task-id').value,
        action_type: document.getElementById('action-type').value,
        tool: document.getElementById('action-tool').value,
        message: document.getElementById('action-message').value,
        reason: document.getElementById('action-message').value, // Use message as reason for grading
        metadata: {}
    };

    try {
        const res = await fetch(`${API_BASE}/step`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(action)
        });
        const data = await res.json();
        updateDashboard(data.observation);
        
        const feedback = data.info.grader ? data.info.grader.feedback : '';
        showToast(`Action Processed. Reward: ${data.reward.toFixed(2)}`, feedback);
        
        document.getElementById('action-form').reset();
    } catch (err) {
        showToast('Operation rejected by environment.');
    }
}

// Rendering
function renderSystemTasks(difficulty) {
    const tasks = allTasks.filter(t => !difficulty || t.difficulty === difficulty || difficulty === 'all');
    
    if (tasks.length === 0) {
        elSystemTasksList.innerHTML = '<p class="text-muted">Inbox is currently empty.</p>';
        return;
    }

    elSystemTasksList.innerHTML = tasks.map(t => `
        <div class="task-card" onclick="document.getElementById('action-task-id').value = '${t.task_id}'" style="cursor: pointer;">
            <div class="task-header">
                <span class="task-sender">${t.sender || 'System'}</span>
                <span class="priority-badge priority-${t.priority}">${t.priority}</span>
            </div>
            <div class="task-input">${t.input}</div>
            <div class="task-meta">
                <span>Task: ${t.task_id}</span>
            </div>
        </div>
    `).join('');
}

function updateDashboard(state) {
    elEnvStep.textContent = state.step_count;
    
    // Render Pending Tasks
    const pendingTasks = state.tasks.filter(t => t.status !== 'completed');
    if (pendingTasks.length === 0) {
        elEnvTasksList.innerHTML = '<div class="panel glass-panel" style="background: rgba(35, 134, 54, 0.05); text-align:center; padding: 2rem;">' +
                                   '<div style="font-size: 2rem; margin-bottom: 1rem;">✨</div>' +
                                   '<p>Workspace clear. All tasks finalized.</p></div>';
    } else {
        elEnvTasksList.innerHTML = pendingTasks.map(t => `
            <div class="task-card">
                <div class="task-header">
                    <span class="task-sender">${t.sender || 'Unknown'}</span>
                    <span class="priority-badge priority-${t.priority}">${t.priority}</span>
                </div>
                <div class="task-input">${t.input}</div>
                <div class="task-meta">
                    <span>${t.task_id}</span>
                    <span>Deadline: ${t.deadline} steps</span>
                </div>
            </div>
        `).join('');
    }

    // Render Metrics
    const metrics = state.performance_metrics || {};
    elMetrics.innerHTML = Object.entries(metrics).map(([key, val]) => `
        <div class="metric-box">
            <div class="metric-value">${typeof val === 'number' ? val.toFixed(2) : val}</div>
            <div class="metric-label">${key.replace(/_/g, ' ')}</div>
        </div>
    `).join('');

    // Render Logs as Chat
    const logs = state.agent_logs || [];
    if (logs.length === 0) {
        elLogs.innerHTML = '<p class="text-muted">Waiting for collaboration...</p>';
    } else {
        elLogs.innerHTML = logs.slice().reverse().map(l => `
            <div class="chat-bubble">
                <img src="${l.avatar || `https://i.pravatar.cc/150?u=${l.from_agent}`}" class="avatar" alt="avatar">
                <div class="bubble-content">
                    <div class="bubble-author">${l.from || l.from_agent}</div>
                    <div class="bubble-msg">${l.message}</div>
                </div>
            </div>
        `).join('');
    }
}

// Start
init();
