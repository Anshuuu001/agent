# Universal Autonomous Desktop AI — System Architecture

## 1. Executive Summary & Core Philosophy

**Universal Autonomous Desktop AI** is a production-grade, capability-driven desktop operating assistant designed to autonomously understand natural-language human goals and orchestrate multi-agent pipelines to achieve concrete results on the user's computer.

### The Core Paradigm
$$\text{USER GOAL} \longrightarrow \text{INTENT} \longrightarrow \text{DYNAMIC PLAN} \longrightarrow \text{CAPABILITY DISCOVERY} \longrightarrow \text{MULTI-AGENT EXECUTION} \longrightarrow \text{VERIFICATION} \longrightarrow \text{DELIVERY}$$

Instead of hardcoded command routines (`if command == 'make report'`), the system employs dynamic intent analysis, DAG-based task graph synthesis, capability matching across registries, and iterative self-correction.

---

## 2. System Architecture Diagram

```
+-----------------------------------------------------------------------------------+
|                                 DESKTOP SHELL & UI                                |
| (Modern Glassmorphic Dashboard, Voice Interface, Emergency Stop, WebSocket Stream) |
+------------------------------------------+----------------------------------------+
                                           |
                                      REST / WebSocket
                                           |
+------------------------------------------v----------------------------------------+
|                                      AI BRAIN                                     |
|  - Natural Language Intent Understanding     - Dynamic Plan Formulation (DAG)     |
|  - Context & Memory Synthesis                - Provider-Independent Model Router  |
+----+-------------------------------------+-----------------------------------+----+
     |                                     |                                   |
+----v-------------------+   +-------------v-------------+   +-----------------v----+
|   TASK ORCHESTRATOR    |   |      AGENT REGISTRY       |   |    TOOL REGISTRY     |
| - DAG Dependency Engine|   | - 23 Specialized Agents   |   | - Desktop Automation |
| - Concurrency & Queue  |   | - Dynamic Capabilities    |   | - File & System      |
| - Checkpoint & Rollback|   | - Health & Status Guard   |   | - Vision & OCR       |
+----+-------------------+   +-------------+-------------+   +-----------------+----+
     |                                     |                                   |
+----v-------------------------------------v-----------------------------------v----+
|                        SECURITY & AUDIT GOVERNANCE LAYER                          |
| - 4-Level Autonomy Policy (Assisted -> Full Workflow)                             |
| - Action Risk Classifier & Interactive Approvals Drawer                           |
| - PII / Secret Redaction Engine & Signed Audit Logging                            |
+------------------------------------------+----------------------------------------+
                                           |
+------------------------------------------v----------------------------------------+
|                                PERSISTENCE LAYER                                  |
| - SQLite Database (SQLAlchemy 2.0 Async ORM with 22+ Entities)                    |
| - Multi-Tier Memory Store (Short-Term, Task, Long-Term, Workflow, App)            |
+-----------------------------------------------------------------------------------+
```

---

## 3. Major System Components (Phase 1 Baseline)

1. **AI Brain (`backend.app.core.brain:AIBrain`)**:
   Central reasoning engine that receives natural language requests, fetches context from the multi-tier memory system, dynamically produces multi-agent task execution graphs, and assigns tasks.

2. **Task Orchestrator (`backend.app.core.orchestrator:TaskOrchestrator`)**:
   Manages task lifecycles, subtask DAG dependencies, priority scheduling (LOW, NORMAL, HIGH, URGENT), pause/resume/cancel semantics, checkpoint creation, and step-by-step progress tracking.

3. **Agent Registry (`backend.app.core.agent_registry:AgentRegistry`)**:
   Houses 23 specialized agents categorized across RESEARCH, CONTENT, ENGINEERING, AUTOMATION, OFFICE, SYSTEM, and SECURITY. Exposes capability matching so the Brain can dynamically query which agents solve a given subtask.

4. **Tool Registry (`backend.app.core.tool_registry:ToolRegistry`)**:
   Extensible registry of executable system, desktop, file, browser, vision, and document tools. Every tool execution is evaluated for risk level and permission before invocation.

5. **Security Manager (`backend.app.core.security:SecurityManager`)**:
   Enforces autonomy levels (1: Assisted, 2: Supervised, 3: Autonomous, 4: Full Workflow), validates actions against risk policies, generates interactive approval requests, sanitizes secrets, and provides an instant Global Emergency Stop.

6. **Action Audit Logger (`backend.app.core.audit:AuditLogger`)**:
   Maintains an immutable, sanitized audit trail of all tool invocations and user approvals in the database and streams them live via WebSocket.

7. **Multi-Tier Memory Manager (`backend.app.core.memory:MemoryManager`)**:
   Manages 5 discrete memory tiers: `SHORT_TERM` (working buffer), `TASK` (project scope), `LONG_TERM` (user preferences/facts), `APPLICATION` (tool settings), and `WORKFLOW` (saved pipelines).

8. **Model Router (`backend.app.core.model_router:ModelRouter`)**:
   Provider-independent LLM routing interface supporting OpenAI, Anthropic, Ollama, and an intelligent offline Heuristic / Rule-based engine.

---

## 4. Complete Database Schema

The database model is built with SQLAlchemy 2.0 Async ORM and persisted in SQLite (`data/desktop_ai.db`):

| Entity | Purpose |
| :--- | :--- |
| `User` | User profiles, roles, and global preferences |
| `Project` | High-level workspace projects |
| `Task` | Top-level goals, priorities, progress, and plans |
| `Subtask` | Atomic execution steps linked in DAG order |
| `TaskDependency` | Dependency graph edges between subtasks |
| `TaskLog` | Detailed timestamped event logs per task |
| `Agent` | Registered agent profiles, versions, health, and status |
| `AgentCapability` | Granular capability indexing for discovery |
| `Tool` | Registered tools with category and risk levels |
| `ToolExecution` | Execution telemetry, timings, and outputs |
| `Approval` | Interactive confirmation requests for sensitive actions |
| `Permission` | Policy configuration by autonomy level |
| `Memory` | Multi-tier memory entries with query indexing |
| `Workflow` | Saved reusable multi-agent workflows |
| `WorkflowStep` | Steps belonging to saved reusable workflows |
| `FileRecord` | File tracking, checksums, and categories |
| `Session` | Conversation sessions |
| `ChatMessage` | User and AI conversational turns |
| `Notification` | In-app alerts, errors, and task completions |
| `Checkpoint` | State snapshots for rollback and crash recovery |
| `AuditLog` | Security action audit records |
| `ModelConfiguration`| LLM profiles, token limits, and default models |
| `Plugin` | Dynamic plugin registry and permission scopes |

---

## 5. Security & Autonomy Architecture

The platform provides 4 strict autonomy tiers:
* **Level 1 — Assisted**: Confirms almost every action before execution.
* **Level 2 — Supervised (Default)**: Executes Low/Medium risk tasks automatically (reading files, web research, document synthesis); requires explicit user approval for High/Critical actions (deleting files, running arbitrary shell scripts).
* **Level 3 — Autonomous**: Operates independently across Low, Medium, and High risk actions, requiring approval only for Critical/destructive actions.
* **Level 4 — Full Workflow**: End-to-end long-running pipeline execution with emergency stop supervision.

### Emergency Stop
A single-click emergency kill-switch (`/api/v1/settings/emergency-stop`) immediately suspends all active background tasks, blocks all subsequent tool execution calls, and notifies all connected clients.
