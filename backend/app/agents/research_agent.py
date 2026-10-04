from typing import Dict, Any, Optional
from backend.app.schemas.common import AgentCategory
from backend.app.schemas.agents import AgentExecutionResult
from backend.app.core.agent_registry import BaseAgent
from backend.app.core.tool_registry import tool_registry

class ResearchAgent(BaseAgent):
    name = "Research Agent"
    display_name = "Autonomous Research Agent"
    description = "Performs web research, information extraction, source comparison, and factual summarization."
    category = AgentCategory.RESEARCH
    version = "1.0.0"
    capabilities = [
        "web research", "information extraction", "source comparison",
        "literature review", "fact verification", "topic exploration"
    ]
    required_tools = ["search_web", "read_page"]
    permissions = ["READ_WEB", "EXTRACT_DATA"]

    async def execute(self, instruction: str, context: Optional[Dict[str, Any]] = None) -> AgentExecutionResult:
        task_id = context.get("task_id") if context else None
        
        # Invoke search tool
        search_res = await tool_registry.execute_tool(
            tool_name="search_web",
            parameters={"query": instruction},
            task_id=task_id,
            agent_name=self.name
        )

        return AgentExecutionResult(
            agent_name=self.name,
            status="SUCCESS" if search_res.status == "SUCCESS" else "FAILED",
            output={"research_data": search_res.result},
            summary=f"Synthesized research and sources for: {instruction}",
            tools_used=["search_web"]
        )


class WritingAgent(BaseAgent):
    name = "Writing Agent"
    display_name = "Professional Writing Agent"
    description = "Drafts comprehensive essays, whitepapers, summaries, and formal prose."
    category = AgentCategory.CONTENT
    version = "1.0.0"
    capabilities = ["formal writing", "article drafting", "executive summaries", "proofreading", "tone adaptation"]
    required_tools = ["generate_content"]

    async def execute(self, instruction: str, context: Optional[Dict[str, Any]] = None) -> AgentExecutionResult:
        content_res = await tool_registry.execute_tool(
            tool_name="generate_content",
            parameters={"goal": instruction},
            task_id=context.get("task_id") if context else None,
            agent_name=self.name
        )
        return AgentExecutionResult(
            agent_name=self.name,
            status="SUCCESS",
            output=content_res.result,
            summary=f"Generated professional prose for '{instruction}'",
            tools_used=["generate_content"]
        )


class ContentAgent(BaseAgent):
    name = "Content Agent"
    display_name = "Content Structuring & Synthesis Agent"
    description = "Structures outline, generates multi-section deliverables, and formats content hierarchies."
    category = AgentCategory.CONTENT
    version = "1.0.0"
    capabilities = ["content structuring", "outline generation", "section synthesis", "table generation"]
    required_tools = ["generate_content"]

    async def execute(self, instruction: str, context: Optional[Dict[str, Any]] = None) -> AgentExecutionResult:
        content_res = await tool_registry.execute_tool(
            tool_name="generate_content",
            parameters={"goal": instruction},
            task_id=context.get("task_id") if context else None,
            agent_name=self.name
        )
        return AgentExecutionResult(
            agent_name=self.name,
            status="SUCCESS",
            output=content_res.result,
            summary="Structured content sections and technical outlines generated.",
            tools_used=["generate_content"]
        )
