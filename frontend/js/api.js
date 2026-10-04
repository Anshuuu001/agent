// REST API CLIENT FOR DESKTOP AI
const API_BASE = '/api/v1';

export const ApiService = {
  async getTasks(status = null) {
    const url = status ? `${API_BASE}/tasks?status=${status}` : `${API_BASE}/tasks`;
    const res = await fetch(url);
    return await res.json();
  },

  async getTaskDetails(taskId) {
    const res = await fetch(`${API_BASE}/tasks/${taskId}`);
    return await res.json();
  },

  async getTaskLogs(taskId) {
    const res = await fetch(`${API_BASE}/tasks/${taskId}/logs`);
    return await res.json();
  },

  async pauseTask(taskId) {
    const res = await fetch(`${API_BASE}/tasks/${taskId}/pause`, { method: 'POST' });
    return await res.json();
  },

  async resumeTask(taskId) {
    const res = await fetch(`${API_BASE}/tasks/${taskId}/resume`, { method: 'POST' });
    return await res.json();
  },

  async cancelTask(taskId) {
    const res = await fetch(`${API_BASE}/tasks/${taskId}/cancel`, { method: 'POST' });
    return await res.json();
  },

  async sendBrainMessage(content, sessionId = null) {
    const res = await fetch(`${API_BASE}/brain/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content, session_id: sessionId })
    });
    return await res.json();
  },

  async getAgents() {
    const res = await fetch(`${API_BASE}/agents`);
    return await res.json();
  },

  async executeAgentTest(agentName, instruction) {
    const res = await fetch(`${API_BASE}/agents/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ agent_name: agentName, instruction })
    });
    return await res.json();
  },

  async getTools() {
    const res = await fetch(`${API_BASE}/tools`);
    return await res.json();
  },

  async executeToolTest(toolName, parameters = {}) {
    const res = await fetch(`${API_BASE}/tools/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tool_name: toolName, parameters })
    });
    return await res.json();
  },

  async getApprovals(status = 'PENDING') {
    const res = await fetch(`${API_BASE}/approvals?status=${status}`);
    return await res.json();
  },

  async resolveApproval(approvalId, action) {
    const res = await fetch(`${API_BASE}/approvals/${approvalId}/resolve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action })
    });
    return await res.json();
  },

  async getMemories(query = '') {
    const res = await fetch(`${API_BASE}/memory?q=${encodeURIComponent(query)}`);
    return await res.json();
  },

  async getWorkflows() {
    const res = await fetch(`${API_BASE}/workflows`);
    return await res.json();
  },

  async getAuditLogs() {
    const res = await fetch(`${API_BASE}/audit`);
    return await res.json();
  },

  async getSettings() {
    const res = await fetch(`${API_BASE}/settings`);
    return await res.json();
  },

  async updateSettings(payload) {
    const res = await fetch(`${API_BASE}/settings`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return await res.json();
  },

  async toggleEmergencyStop() {
    const res = await fetch(`${API_BASE}/settings/emergency-stop`, { method: 'POST' });
    return await res.json();
  }
};
