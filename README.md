# Universal Autonomous Desktop AI

An intelligent desktop operating assistant that understands natural-language goals and autonomously orchestrates multi-agent pipelines to execute complex tasks on your computer.

---

## 🌟 Core Philosophy

$$\text{USER GOAL} \longrightarrow \text{INTENT} \longrightarrow \text{DYNAMIC PLAN} \longrightarrow \text{CAPABILITY DISCOVERY} \longrightarrow \text{MULTI-AGENT EXECUTION} \longrightarrow \text{VERIFICATION} \longrightarrow \text{DELIVERY}$$

The system is **capability-driven** rather than hardcoded command-driven. The AI dynamically analyzes user goals, formulates task DAG graphs, selects specialized agents and tools, executes steps with concurrency, verifies output integrity, and delivers results.

---

## 🚀 Key Features

* **Central AI Brain**: Natural language intent understanding, dynamic DAG plan formulation, and context memory synthesis.
* **Provider-Independent Model Router**: Compatible with OpenAI (GPT-4o), Anthropic (Claude 3.5 Sonnet), Ollama local models, and offline heuristic reasoning engines.
* **23 Modular Agents**: Specialized agents across Research, Writing, Content, Diagramming, Coding, Debugging, Testing, Desktop OS, Browser, File Management, Vision/OCR, Word, Excel, PowerPoint, PDF, Data Analysis, Quality Assurance, Security, and Workflows.
* **Extensible Tool Registry**: Pre-execution risk classification (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), parameter validation, and action audit logging.
* **Task Orchestrator & DAG Engine**: Subtask dependencies, priority scheduling (`LOW`, `NORMAL`, `HIGH`, `URGENT`), pause, resume, cancel, checkpointing, and real-time progress tracking.
* **4 Autonomy Levels**:
  * `Level 1 — Assisted`: Confirms before executing most actions.
  * `Level 2 — Supervised`: Executes normal tasks automatically; requests confirmation for sensitive operations.
  * `Level 3 — Autonomous`: Executes independently across normal and high-risk operations.
  * `Level 4 — Full Workflow`: Unattended long-running pipeline execution with emergency stop supervision.
* **Global Emergency Stop**: One-click instant suspension of all active pipelines and tool invocations.
* **Action Audit Log**: Redacted, signed security audit records for every executed tool.
* **Multi-Tiered Memory**: Short-term buffer, Task context, Long-term facts, Application configurations, and Workflow templates.
* **Modern Desktop Dashboard**: Glassmorphic UI with real-time WebSocket telemetry, Mission Control, Task Manager, Agent Health grid, Tool Registry explorer, Approvals drawer, and Web Speech voice input.

---

## 🛠️ Quick Start

### Prerequisites
* Python 3.10+
* Git

### Installation
```bash
# Clone the repository
git clone https://github.com/Anshuuu001/agent.git
cd agent

# Install dependencies
pip install -r requirements.txt
```

### Launch Application
```bash
python run.py
```
* **Dashboard UI**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
* **Interactive API Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### Run Test Suite
```bash
python -m pytest
```

---

## 🏛️ Architecture & Documentation

* Detailed Architecture: [`ARCHITECTURE.md`](./ARCHITECTURE.md)
* Changelog: [`CHANGELOG.md`](./CHANGELOG.md)
* Future Roadmap (Phase 2 - Phase 15): [`TODO.md`](./TODO.md)

---

## 📄 License

MIT License.
