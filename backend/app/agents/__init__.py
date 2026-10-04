from backend.app.core.agent_registry import agent_registry
from backend.app.agents.research_agent import ResearchAgent, WritingAgent, ContentAgent
from backend.app.agents.coding_agents import CodingAgent, DebuggingAgent, TestingAgent
from backend.app.agents.desktop_agents import DesktopAgent, BrowserAgent, FileAgent, VisionAgent
from backend.app.agents.document_agents import (
    WordAgent, ExcelAgent, PowerPointAgent, PDFAgent, DataAnalysisAgent, DiagramAgent, ImageAgent
)
from backend.app.agents.system_agents import (
    QualityAssuranceAgent, SystemAgent, SecurityAgent, CommunicationAgent, EmailAgent, WorkflowAgent
)

def register_default_agents():
    """Register all 23 standard modular agents."""
    agents_to_register = [
        # Research & Content
        ResearchAgent(),
        WritingAgent(),
        ContentAgent(),
        DiagramAgent(),
        ImageAgent(),
        # Engineering & Code
        CodingAgent(),
        DebuggingAgent(),
        TestingAgent(),
        # Desktop & Automation
        DesktopAgent(),
        BrowserAgent(),
        FileAgent(),
        VisionAgent(),
        # Office & Documents
        WordAgent(),
        ExcelAgent(),
        PowerPointAgent(),
        PDFAgent(),
        DataAnalysisAgent(),
        # System & Governance
        QualityAssuranceAgent(),
        SystemAgent(),
        SecurityAgent(),
        CommunicationAgent(),
        EmailAgent(),
        WorkflowAgent(),
    ]
    for agent in agents_to_register:
        agent_registry.register(agent)

# Automatically register on import
register_default_agents()
