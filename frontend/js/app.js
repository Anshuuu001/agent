import { ApiService } from './api.js';
import { WebSocketClient } from './ws.js';

// Application State Store
const state = {
  activeView: 'home',
  tasks: [],
  agents: [],
  tools: [],
  approvals: [],
  memories: [],
  workflows: [],
  auditLogs: [],
  settings: null,
  activeSessionId: null,
  chatMessages: [],
  emergencyStopActive: false,
  wsConnected: false
};

// DOM Elements
const elements = {
  viewTitle: document.getElementById('view-title'),
  wsStatusDot: document.getElementById('ws-status-dot'),
  wsStatusText: document.getElementById('ws-status-text'),
  btnEmergencyStop: document.getElementById('btn-emergency-stop'),
  emergencyBanner: document.getElementById('emergency-banner'),
  navItems: document.querySelectorAll('.nav-item'),
  views: document.querySelectorAll('.view-pane'),
  approvalBadge: document.getElementById('approval-badge'),

  // Home view
  metricsActiveTasks: document.getElementById('metric-active-tasks'),
  metricsHealthyAgents: document.getElementById('metric-healthy-agents'),
  metricsRegisteredTools: document.getElementById('metric-registered-tools'),
  metricsCpuUsage: document.getElementById('metric-cpu-usage'),
  homeTasksList: document.getElementById('home-tasks-list'),
  homeActivityList: document.getElementById('home-activity-list'),
  homePromptInput: document.getElementById('home-prompt-input'),
  btnHomePromptSend: document.getElementById('btn-home-prompt-send'),

  // Chat view
  chatHistory: document.getElementById('chat-history'),
  chatInput: document.getElementById('chat-input'),
  btnChatSend: document.getElementById('btn-chat-send'),
  btnVoiceTrigger: document.getElementById('btn-voice-trigger'),

  // Tasks view
  tasksContainer: document.getElementById('tasks-container'),
  taskFilterStatus: document.getElementById('task-filter-status'),

  // Agents view
  agentsContainer: document.getElementById('agents-container'),

  // Tools view
  toolsContainer: document.getElementById('tools-container'),
  toolCategoryFilter: document.getElementById('tool-category-filter'),

  // Approvals view
  approvalsContainer: document.getElementById('approvals-container'),

  // Memory view
  memoryContainer: document.getElementById('memory-container'),
  memorySearchInput: document.getElementById('memory-search-input'),

  // Workflows view
  workflowsContainer: document.getElementById('workflows-container'),

  // Audit view
  auditContainer: document.getElementById('audit-container'),

  // Settings view
  autonomyLevelSelect: document.getElementById('autonomy-level-select'),
  autonomyPillLevel: document.getElementById('autonomy-pill-level'),
  systemStatusInfo: document.getElementById('system-status-info')
};

// Initialize WebSocket
const wsClient = new WebSocketClient((payload) => {
  handleRealtimeEvent(payload);
});

function handleRealtimeEvent(payload) {
  const { event, data } = payload;

  if (event === 'connection_status') {
    state.wsConnected = data.connected;
    updateConnectionUI();
    return;
  }

  if (event === 'task_update') {
    // Refresh tasks and telemetry
    loadTasks();
  } else if (event === 'agent_status') {
    loadAgents();
  } else if (event === 'audit_log') {
    state.auditLogs.unshift(data);
    renderAuditLogs();
    renderHomeActivity();
  } else if (event === 'approval_required' || event === 'approval_resolved') {
    loadApprovals();
  } else if (event === 'emergency_stop_state') {
    state.emergencyStopActive = data.active;
    updateEmergencyStopUI();
  } else if (event === 'notification') {
    showNotificationToast(data.title, data.message, data.type);
  }
}

function showNotificationToast(title, message, type = 'INFO') {
  console.log(`[Notification] ${title}: ${message}`);
}

function updateConnectionUI() {
  if (state.wsConnected) {
    elements.wsStatusDot.style.background = 'var(--accent-emerald)';
    elements.wsStatusDot.style.boxShadow = '0 0 10px var(--accent-emerald)';
    elements.wsStatusText.textContent = 'System Operational';
  } else {
    elements.wsStatusDot.style.background = 'var(--accent-rose)';
    elements.wsStatusDot.style.boxShadow = '0 0 10px var(--accent-rose)';
    elements.wsStatusText.textContent = 'Connecting...';
  }
}

function updateEmergencyStopUI() {
  if (state.emergencyStopActive) {
    elements.btnEmergencyStop.classList.add('active-halt');
    elements.btnEmergencyStop.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14"/></svg> RESUME SYSTEM`;
    if (elements.emergencyBanner) elements.emergencyBanner.style.display = 'block';
  } else {
    elements.btnEmergencyStop.classList.remove('active-halt');
    elements.btnEmergencyStop.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/></svg> EMERGENCY STOP`;
    if (elements.emergencyBanner) elements.emergencyBanner.style.display = 'none';
  }
}

// Navigation & View Switching
function switchView(viewName) {
  state.activeView = viewName;
  elements.views.forEach(v => {
    v.classList.toggle('active', v.id === `view-${viewName}`);
  });

  elements.navItems.forEach(item => {
    item.classList.toggle('active', item.dataset.view === viewName);
  });

  const titles = {
    home: 'Mission Control Dashboard',
    chat: 'Natural Language Autonomous AI Brain',
    tasks: 'Autonomous Task Orchestrator',
    agents: 'Multi-Agent Registry & Health Monitor',
    tools: 'Desktop & System Tool Registry',
    approvals: 'Interactive Security Approvals',
    memory: 'Multi-Tiered Memory & Knowledge System',
    workflows: 'Autonomous Workflow Automation',
    audit: 'Security & Action Audit Trail',
    settings: 'System Configuration & Autonomy Controls'
  };
  elements.viewTitle.textContent = titles[viewName] || 'Dashboard';

  // Load specific data on view enter
  if (viewName === 'tasks') loadTasks();
  if (viewName === 'agents') loadAgents();
  if (viewName === 'tools') loadTools();
  if (viewName === 'approvals') loadApprovals();
  if (viewName === 'memory') loadMemories();
  if (viewName === 'workflows') loadWorkflows();
  if (viewName === 'audit') loadAuditLogs();
  if (viewName === 'settings') loadSettings();
}

// Data Loaders
async function loadHomeMetrics() {
  try {
    const settings = await ApiService.getSettings();
    state.settings = settings;
    state.emergencyStopActive = settings.autonomy.emergency_stop_active;
    updateEmergencyStopUI();

    if (elements.autonomyPillLevel) {
      const names = { 1: 'Assisted', 2: 'Supervised', 3: 'Autonomous', 4: 'Full Workflow' };
      elements.autonomyPillLevel.textContent = `L${settings.autonomy.autonomy_level} ${names[settings.autonomy.autonomy_level]}`;
    }

    if (elements.metricsCpuUsage && settings.system_status) {
      elements.metricsCpuUsage.textContent = `${settings.system_status.cpu_percent}%`;
    }
  } catch (err) {
    console.error('Failed to load settings:', err);
  }
}

async function loadTasks() {
  try {
    const filter = elements.taskFilterStatus ? elements.taskFilterStatus.value : null;
    const tasks = await ApiService.getTasks(filter === 'ALL' ? null : filter);
    state.tasks = tasks;

    // Update Home Metrics
    const runningCount = tasks.filter(t => t.status === 'RUNNING').length;
    if (elements.metricsActiveTasks) {
      elements.metricsActiveTasks.textContent = runningCount;
    }

    renderHomeTasks();
    renderTasksView();
  } catch (err) {
    console.error('Failed to load tasks:', err);
  }
}

async function loadAgents() {
  try {
    const agents = await ApiService.getAgents();
    state.agents = agents;

    const healthyCount = agents.filter(a => a.health === 'HEALTHY').length;
    if (elements.metricsHealthyAgents) {
      elements.metricsHealthyAgents.textContent = `${healthyCount} / ${agents.length}`;
    }

    renderAgentsView();
  } catch (err) {
    console.error('Failed to load agents:', err);
  }
}

async function loadTools() {
  try {
    const tools = await ApiService.getTools();
    state.tools = tools;

    if (elements.metricsRegisteredTools) {
      elements.metricsRegisteredTools.textContent = tools.length;
    }

    renderToolsView();
  } catch (err) {
    console.error('Failed to load tools:', err);
  }
}

async function loadApprovals() {
  try {
    const approvals = await ApiService.getApprovals('PENDING');
    state.approvals = approvals;

    if (elements.approvalBadge) {
      elements.approvalBadge.textContent = approvals.length;
      elements.approvalBadge.style.display = approvals.length > 0 ? 'inline-block' : 'none';
    }

    renderApprovalsView();
  } catch (err) {
    console.error('Failed to load approvals:', err);
  }
}

async function loadMemories(query = '') {
  try {
    const memories = await ApiService.getMemories(query);
    state.memories = memories;
    renderMemoryView();
  } catch (err) {
    console.error('Failed to load memories:', err);
  }
}

async function loadWorkflows() {
  try {
    const workflows = await ApiService.getWorkflows();
    state.workflows = workflows;
    renderWorkflowsView();
  } catch (err) {
    console.error('Failed to load workflows:', err);
  }
}

async function loadAuditLogs() {
  try {
    const logs = await ApiService.getAuditLogs();
    state.auditLogs = logs;
    renderAuditLogs();
    renderHomeActivity();
  } catch (err) {
    console.error('Failed to load audit logs:', err);
  }
}

async function loadSettings() {
  try {
    const settings = await ApiService.getSettings();
    state.settings = settings;

    if (elements.autonomyLevelSelect) {
      elements.autonomyLevelSelect.value = settings.autonomy.autonomy_level;
    }

    if (elements.systemStatusInfo) {
      elements.systemStatusInfo.innerHTML = `
        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; font-size: 13px;">
          <div><strong style="color: var(--text-secondary);">OS:</strong> ${settings.system_status.os}</div>
          <div><strong style="color: var(--text-secondary);">Python:</strong> ${settings.system_status.python_version}</div>
          <div><strong style="color: var(--text-secondary);">CPU Cores / Usage:</strong> ${settings.system_status.cpu_percent}%</div>
          <div><strong style="color: var(--text-secondary);">RAM Utilization:</strong> ${settings.system_status.ram_percent}%</div>
        </div>
      `;
    }
  } catch (err) {
    console.error('Failed to load settings:', err);
  }
}

// Render Functions
function renderHomeTasks() {
  if (!elements.homeTasksList) return;
  if (state.tasks.length === 0) {
    elements.homeTasksList.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-muted); padding: 24px;">No tasks queued or running. Give a goal above!</td></tr>`;
    return;
  }

  elements.homeTasksList.innerHTML = state.tasks.slice(0, 5).map(t => `
    <tr>
      <td><strong>${escapeHtml(t.title)}</strong><div style="font-size: 11px; color: var(--text-muted);">${escapeHtml(t.goal.substring(0, 40))}...</div></td>
      <td><span class="status-badge badge-${t.status.toLowerCase()}">${t.status}</span></td>
      <td style="width: 140px;">
        <div style="font-size: 11px; font-weight: 600;">${t.progress}%</div>
        <div class="progress-bar-bg"><div class="progress-bar-fill" style="width: ${t.progress}%"></div></div>
      </td>
      <td><span style="font-size: 11px; color: var(--accent-cyan);">${t.assigned_agents.join(', ')}</span></td>
      <td><button class="quick-chip" onclick="window.viewTaskDetails('${t.id}')">Inspect</button></td>
    </tr>
  `).join('');
}

function renderHomeActivity() {
  if (!elements.homeActivityList) return;
  if (state.auditLogs.length === 0) {
    elements.homeActivityList.innerHTML = `<div style="text-align: center; color: var(--text-muted); padding: 20px;">No recent activity logged.</div>`;
    return;
  }

  elements.homeActivityList.innerHTML = state.auditLogs.slice(0, 6).map(log => `
    <div style="display: flex; align-items: center; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.04); font-size: 12.5px;">
      <div style="display: flex; align-items: center; gap: 10px;">
        <span class="risk-badge risk-${log.risk_level.toLowerCase()}">${log.risk_level}</span>
        <div>
          <span style="font-weight: 600; color: var(--text-primary);">${escapeHtml(log.action)}</span>
          <span style="color: var(--text-muted);">by ${log.agent_name || 'AI Brain'}</span>
        </div>
      </div>
      <div style="color: var(--text-muted); font-size: 11px;">${new Date(log.timestamp).toLocaleTimeString()}</div>
    </div>
  `).join('');
}

function renderTasksView() {
  if (!elements.tasksContainer) return;
  if (state.tasks.length === 0) {
    elements.tasksContainer.innerHTML = `<div class="glass-panel" style="text-align: center; color: var(--text-muted); padding: 40px;">No tasks available. Submit a command to initiate autonomous workflows.</div>`;
    return;
  }

  elements.tasksContainer.innerHTML = state.tasks.map(t => `
    <div class="glass-panel" style="margin-bottom: 20px;">
      <div style="display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 12px;">
        <div>
          <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 4px;">
            <h3 style="font-size: 17px; font-weight: 700;">${escapeHtml(t.title)}</h3>
            <span class="status-badge badge-${t.status.toLowerCase()}">${t.status}</span>
            <span class="risk-badge risk-medium">Priority: ${t.priority}</span>
          </div>
          <p style="font-size: 13px; color: var(--text-secondary);">${escapeHtml(t.goal)}</p>
        </div>
        <div style="display: flex; gap: 8px;">
          ${t.status === 'RUNNING' ? `<button class="quick-chip" onclick="window.pauseTask('${t.id}')">Pause</button>` : ''}
          ${t.status === 'PAUSED' ? `<button class="quick-chip" onclick="window.resumeTask('${t.id}')">Resume</button>` : ''}
          ${t.status !== 'COMPLETED' && t.status !== 'CANCELLED' ? `<button class="quick-chip" style="color: var(--accent-rose);" onclick="window.cancelTask('${t.id}')">Cancel</button>` : ''}
        </div>
      </div>

      <div style="margin: 14px 0;">
        <div style="display: flex; justify-content: space-between; font-size: 12px; color: var(--text-secondary); margin-bottom: 4px;">
          <span>Execution Progress</span>
          <span><strong>${t.progress}%</strong></span>
        </div>
        <div class="progress-bar-bg"><div class="progress-bar-fill" style="width: ${t.progress}%"></div></div>
      </div>

      <div style="background: rgba(0,0,0,0.25); border-radius: var(--radius-sm); padding: 12px; margin-top: 12px;">
        <div style="font-size: 12px; font-weight: 600; color: var(--accent-cyan); margin-bottom: 8px;">Subtask DAG Timeline:</div>
        <div style="display: flex; flex-direction: column; gap: 6px;">
          ${t.subtasks.map(s => `
            <div style="display: flex; align-items: center; justify-content: space-between; font-size: 12px; padding: 6px 10px; background: rgba(255,255,255,0.02); border-radius: 4px;">
              <div style="display: flex; align-items: center; gap: 8px;">
                <span class="step-num">${s.step_order}</span>
                <span><strong>${escapeHtml(s.title)}</strong> &middot; <span style="color: var(--text-muted);">${s.agent_name || 'System'}</span></span>
              </div>
              <span class="status-badge badge-${s.status.toLowerCase()}" style="font-size: 9px; padding: 2px 6px;">${s.status}</span>
            </div>
          `).join('')}
        </div>
      </div>
    </div>
  `).join('');
}

function renderAgentsView() {
  if (!elements.agentsContainer) return;
  elements.agentsContainer.innerHTML = state.agents.map(a => `
    <div class="item-card">
      <div class="item-card-header">
        <div>
          <div class="item-name">${escapeHtml(a.name)}</div>
          <span style="font-size: 10px; text-transform: uppercase; letter-spacing: 1px; color: var(--accent-cyan); font-weight: 700;">${a.category} &middot; v${a.version}</span>
        </div>
        <span class="status-badge badge-${a.status === 'RUNNING' ? 'running' : 'completed'}" style="font-size: 10px;">${a.status}</span>
      </div>
      <p class="item-desc">${escapeHtml(a.description)}</p>
      <div>
        <div style="font-size: 11px; font-weight: 600; color: var(--text-muted); margin-bottom: 6px;">Capabilities:</div>
        <div class="tag-list">
          ${a.capabilities.map(c => `<span class="tag-pill">${escapeHtml(c)}</span>`).join('')}
        </div>
      </div>
      <div style="margin-top: auto; padding-top: 10px; border-top: 1px solid var(--border-glass); display: flex; justify-content: space-between; align-items: center;">
        <span style="font-size: 11px; color: var(--accent-emerald);">&bull; ${a.health}</span>
        <button class="quick-chip" onclick="window.testAgentModal('${a.name}')">Test Agent</button>
      </div>
    </div>
  `).join('');
}

function renderToolsView() {
  if (!elements.toolsContainer) return;
  const categoryFilter = elements.toolCategoryFilter ? elements.toolCategoryFilter.value : 'ALL';
  const filtered = categoryFilter === 'ALL' ? state.tools : state.tools.filter(t => t.category === categoryFilter);

  elements.toolsContainer.innerHTML = filtered.map(t => `
    <div class="item-card">
      <div class="item-card-header">
        <div>
          <div class="item-name">${escapeHtml(t.display_name)}</div>
          <code style="font-size: 11px; color: var(--accent-cyan);">${escapeHtml(t.name)}</code>
        </div>
        <span class="risk-badge risk-${t.risk_level.toLowerCase()}">${t.risk_level}</span>
      </div>
      <p class="item-desc">${escapeHtml(t.description)}</p>
      <div style="display: flex; justify-content: space-between; font-size: 11px; color: var(--text-muted); margin-top: auto; padding-top: 10px; border-top: 1px solid var(--border-glass);">
        <span>Category: <strong>${t.category}</strong></span>
        <button class="quick-chip" onclick="window.testToolModal('${t.name}')">Execute Tool</button>
      </div>
    </div>
  `).join('');
}

function renderApprovalsView() {
  if (!elements.approvalsContainer) return;
  if (state.approvals.length === 0) {
    elements.approvalsContainer.innerHTML = `<div class="glass-panel" style="text-align: center; color: var(--text-muted); padding: 40px;">No pending approvals required at current autonomy level.</div>`;
    return;
  }

  elements.approvalsContainer.innerHTML = state.approvals.map(appr => `
    <div class="glass-panel" style="border-left: 4px solid var(--accent-amber); margin-bottom: 16px;">
      <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
        <div>
          <div style="display: flex; align-items: center; gap: 8px;">
            <h4 style="font-size: 16px; font-weight: 700;">Action Approval Required</h4>
            <span class="risk-badge risk-${appr.risk_level.toLowerCase()}">${appr.risk_level} RISK</span>
          </div>
          <p style="font-size: 13px; color: var(--text-secondary); margin-top: 4px;">${escapeHtml(appr.reason)}</p>
        </div>
        <div style="font-size: 11px; color: var(--text-muted);">${new Date(appr.requested_at).toLocaleTimeString()}</div>
      </div>
      <div style="display: flex; gap: 10px; justify-content: flex-end;">
        <button class="quick-chip" style="color: var(--accent-rose); border-color: var(--accent-rose);" onclick="window.resolveApproval('${appr.id}', 'REJECT')">Reject Action</button>
        <button class="btn-prompt-send" style="padding: 6px 16px; font-size: 12px;" onclick="window.resolveApproval('${appr.id}', 'APPROVE')">Approve & Execute</button>
      </div>
    </div>
  `).join('');
}

function renderMemoryView() {
  if (!elements.memoryContainer) return;
  if (state.memories.length === 0) {
    elements.memoryContainer.innerHTML = `<div style="text-align: center; color: var(--text-muted); padding: 30px;">No memories stored matching search criteria.</div>`;
    return;
  }

  elements.memoryContainer.innerHTML = state.memories.map(m => `
    <div class="glass-panel" style="margin-bottom: 12px; padding: 16px;">
      <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
        <div>
          <span class="risk-badge risk-low" style="margin-right: 6px;">${m.tier}</span>
          <strong>${escapeHtml(m.key)}</strong>
        </div>
        <span style="font-size: 11px; color: var(--text-muted);">Accessed: ${m.access_count} times</span>
      </div>
      <div style="font-size: 13px; color: var(--text-secondary);">${escapeHtml(m.content)}</div>
    </div>
  `).join('');
}

function renderWorkflowsView() {
  if (!elements.workflowsContainer) return;
  if (state.workflows.length === 0) {
    elements.workflowsContainer.innerHTML = `<div class="glass-panel" style="text-align: center; color: var(--text-muted); padding: 30px;">No custom saved workflows. Reusable workflows will appear here.</div>`;
    return;
  }

  elements.workflowsContainer.innerHTML = state.workflows.map(w => `
    <div class="glass-panel" style="margin-bottom: 16px;">
      <h4 style="font-size: 16px; font-weight: 700; color: var(--accent-cyan);">${escapeHtml(w.name)}</h4>
      <p style="font-size: 13px; color: var(--text-secondary); margin: 6px 0 12px 0;">${escapeHtml(w.description || 'No description provided')}</p>
      <div style="font-size: 12px; font-weight: 600; color: var(--text-muted); margin-bottom: 6px;">Pipeline Steps (${w.steps.length}):</div>
      <div style="display: flex; flex-direction: column; gap: 4px;">
        ${w.steps.map(s => `
          <div style="font-size: 12px; padding: 4px 8px; background: rgba(255,255,255,0.03); border-radius: 4px;">
            ${s.step_order}. <strong>${escapeHtml(s.title)}</strong> &middot; <span style="color: var(--accent-indigo);">${s.agent_name || 'System'}</span>
          </div>
        `).join('')}
      </div>
    </div>
  `).join('');
}

function renderAuditLogs() {
  if (!elements.auditContainer) return;
  elements.auditContainer.innerHTML = state.auditLogs.map(log => `
    <tr>
      <td>${new Date(log.timestamp).toLocaleTimeString()}</td>
      <td><span class="risk-badge risk-${log.risk_level.toLowerCase()}">${log.risk_level}</span></td>
      <td><strong>${escapeHtml(log.action)}</strong></td>
      <td>${escapeHtml(log.agent_name || 'AI Brain')}</td>
      <td><code style="font-size: 11px; color: var(--accent-cyan);">${escapeHtml(JSON.stringify(log.parameters))}</code></td>
      <td><span class="status-badge badge-${log.approval_status === 'BLOCKED' ? 'failed' : 'completed'}" style="font-size: 9px;">${log.approval_status}</span></td>
    </tr>
  `).join('');
}

// Chat Submission & Brain Processing
async function submitGoalPrompt(promptText) {
  if (!promptText || !promptText.trim()) return;

  // Append user message in chat
  appendChatMessage('user', promptText);

  // Switch to chat view if not already there
  if (state.activeView !== 'chat') {
    switchView('chat');
  }

  // Placeholder thinking bubble
  const loadingBubble = appendChatMessage('assistant', '<span style="color: var(--accent-cyan); animation: pulse-dot 1s infinite;">🧠 Analyzing intent, discovering capabilities, and generating multi-agent plan...</span>');

  try {
    const res = await ApiService.sendBrainMessage(promptText, state.activeSessionId);
    state.activeSessionId = res.session_id;

    // Remove placeholder and render structured reply
    if (loadingBubble) loadingBubble.remove();

    let formattedContent = `<p>${escapeHtml(res.reply_text).replace(/\n/g, '<br>')}</p>`;

    if (res.plan) {
      formattedContent += `
        <div class="plan-card">
          <div class="plan-card-header">
            <span>Dynamic Plan: ${escapeHtml(res.plan.primary_intent)}</span>
            <span style="font-size: 11px; color: var(--text-muted);">${res.plan.steps.length} Subtasks</span>
          </div>
          <div class="plan-steps-list">
            ${res.plan.steps.map(s => `
              <div class="plan-step-item">
                <span class="step-num">${s.step_order}</span>
                <span><strong>${escapeHtml(s.title)}</strong> &mdash; <span style="color: var(--accent-indigo);">${escapeHtml(s.agent_name)}</span></span>
              </div>
            `).join('')}
          </div>
        </div>
      `;
    }

    appendChatMessage('assistant', formattedContent);
    loadTasks();
  } catch (err) {
    if (loadingBubble) loadingBubble.remove();
    appendChatMessage('assistant', `<span style="color: var(--accent-rose);">Error communicating with AI Brain: ${err.message}</span>`);
  }
}

function appendChatMessage(role, htmlContent) {
  if (!elements.chatHistory) return null;
  const msgDiv = document.createElement('div');
  msgDiv.className = `chat-msg ${role}`;
  msgDiv.innerHTML = `
    <div class="chat-avatar">${role === 'user' ? 'U' : 'AI'}</div>
    <div class="chat-bubble">${htmlContent}</div>
  `;
  elements.chatHistory.appendChild(msgDiv);
  elements.chatHistory.scrollTop = elements.chatHistory.scrollHeight;
  return msgDiv;
}

// Global Window Helpers for Buttons
window.viewTaskDetails = (taskId) => {
  switchView('tasks');
};

window.pauseTask = async (taskId) => {
  await ApiService.pauseTask(taskId);
  loadTasks();
};

window.resumeTask = async (taskId) => {
  await ApiService.resumeTask(taskId);
  loadTasks();
};

window.cancelTask = async (taskId) => {
  await ApiService.cancelTask(taskId);
  loadTasks();
};

window.resolveApproval = async (approvalId, action) => {
  await ApiService.resolveApproval(approvalId, action);
  loadApprovals();
};

window.testAgentModal = async (agentName) => {
  const instruction = prompt(`Enter test instruction for ${agentName}:`, "Synthesize research overview");
  if (!instruction) return;
  const res = await ApiService.executeAgentTest(agentName, instruction);
  alert(`[Agent Execution Result]\nStatus: ${res.status}\nSummary: ${res.summary}\nTime: ${res.execution_time_ms}ms`);
  loadAgents();
};

window.testToolModal = async (toolName) => {
  const res = await ApiService.executeToolTest(toolName, {});
  alert(`[Tool Execution Result]\nStatus: ${res.status}\nExecution Time: ${res.execution_time_ms}ms\nResult: ${JSON.stringify(res.result, null, 2)}`);
  loadTools();
};

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// Event Listeners Setup
function initEventListeners() {
  // Navigation
  elements.navItems.forEach(item => {
    item.addEventListener('click', () => {
      switchView(item.dataset.view);
    });
  });

  // Emergency Stop Button
  elements.btnEmergencyStop.addEventListener('click', async () => {
    const res = await ApiService.toggleEmergencyStop();
    state.emergencyStopActive = res.emergency_stop_active;
    updateEmergencyStopUI();
  });

  // Home prompt send
  elements.btnHomePromptSend?.addEventListener('click', () => {
    const text = elements.homePromptInput.value;
    elements.homePromptInput.value = '';
    submitGoalPrompt(text);
  });

  elements.homePromptInput?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      const text = elements.homePromptInput.value;
      elements.homePromptInput.value = '';
      submitGoalPrompt(text);
    }
  });

  // Chat input send
  elements.btnChatSend?.addEventListener('click', () => {
    const text = elements.chatInput.value;
    elements.chatInput.value = '';
    submitGoalPrompt(text);
  });

  elements.chatInput?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      const text = elements.chatInput.value;
      elements.chatInput.value = '';
      submitGoalPrompt(text);
    }
  });

  // Quick prompt chips
  document.querySelectorAll('.quick-chip[data-prompt]').forEach(chip => {
    chip.addEventListener('click', () => {
      submitGoalPrompt(chip.dataset.prompt);
    });
  });

  // Voice Assistant button
  elements.btnVoiceTrigger?.addEventListener('click', () => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognition = new SpeechRecognition();
      recognition.lang = 'en-US';
      recognition.onstart = () => {
        elements.btnVoiceTrigger.style.borderColor = 'var(--accent-rose)';
        elements.chatInput.placeholder = 'Listening... Speak your goal';
      };
      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        elements.chatInput.value = transcript;
        submitGoalPrompt(transcript);
      };
      recognition.onend = () => {
        elements.btnVoiceTrigger.style.borderColor = 'var(--border-glass)';
        elements.chatInput.placeholder = 'Type your goal (e.g. Research a topic and build a 15-page report)...';
      };
      recognition.start();
    } else {
      alert('Web Speech recognition not natively available in this browser window. Type your command instead.');
    }
  });

  // Filters
  elements.taskFilterStatus?.addEventListener('change', loadTasks);
  elements.toolCategoryFilter?.addEventListener('change', renderToolsView);
  elements.memorySearchInput?.addEventListener('input', (e) => loadMemories(e.target.value));

  // Autonomy Level selector in Settings
  elements.autonomyLevelSelect?.addEventListener('change', async (e) => {
    const level = parseInt(e.target.value, 10);
    await ApiService.updateSettings({ autonomy_level: level });
    loadHomeMetrics();
  });
}

// Initial Boot
async function initApp() {
  initEventListeners();
  wsClient.connect();
  await loadHomeMetrics();
  await loadTasks();
  await loadAgents();
  await loadTools();
  await loadApprovals();
  await loadAuditLogs();
}

window.addEventListener('DOMContentLoaded', initApp);
