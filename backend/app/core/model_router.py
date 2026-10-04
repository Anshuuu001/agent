import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from backend.app.config import settings

logger = logging.getLogger("desktop_ai.model_router")

class BaseModelProvider(ABC):
    @abstractmethod
    async def generate_response(self, system_prompt: str, user_prompt: str, response_format: Optional[str] = None) -> str:
        """Generate response given prompts."""
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        pass


class HeuristicProvider(BaseModelProvider):
    """
    Intelligent offline rule-based & semantic parsing engine for Phase 1 & offline resilience.
    Generates structured dynamic plans, intent classifications, and agent assignments.
    """
    def get_provider_name(self) -> str:
        return "heuristic"

    async def generate_response(self, system_prompt: str, user_prompt: str, response_format: Optional[str] = None) -> str:
        prompt_lower = user_prompt.lower()

        # Check if structured plan is requested
        if response_format == "json" or "dynamicplan" in system_prompt.lower() or "create a plan" in user_prompt.lower() or "research" in prompt_lower or "project" in prompt_lower or "fix" in prompt_lower or "organize" in prompt_lower or "create" in prompt_lower:
            return self._generate_heuristic_plan(user_prompt)

        return f"Understood your request: '{user_prompt}'. I will analyze required capabilities, assign agents, and orchestrate the execution."

    def _generate_heuristic_plan(self, goal: str) -> str:
        g = goal.lower()
        steps = []
        selected_agents = []
        capabilities = []
        primary_intent = "EXECUTION"

        # Topic research and document/presentation generation
        if "research" in g or "microproject" in g or "report" in g or "decoder" in g:
            primary_intent = "RESEARCH_AND_DOCUMENT"
            selected_agents = ["Research Agent", "Content Agent", "Diagram Agent", "Word Agent", "Quality Assurance Agent"]
            capabilities = ["web research", "content synthesis", "diagram generation", "document creation", "quality check"]

            steps = [
                {
                    "step_order": 1,
                    "title": "Topic Research & Evidence Gathering",
                    "agent_name": "Research Agent",
                    "tool_name": "search_web",
                    "description": f"Gather primary sources, technical references, and structured facts for: {goal}",
                    "dependencies": [],
                    "estimated_risk": "LOW",
                    "requires_approval": False,
                    "is_parallel_safe": True,
                    "parameters": {"query": goal}
                },
                {
                    "step_order": 2,
                    "title": "Content Architecture & Synthesis",
                    "agent_name": "Content Agent",
                    "tool_name": "generate_content",
                    "description": "Synthesize research data into structured sections, headings, and detailed explanations.",
                    "dependencies": [1],
                    "estimated_risk": "LOW",
                    "requires_approval": False,
                    "is_parallel_safe": True,
                    "parameters": {"format": "structured_sections"}
                },
                {
                    "step_order": 3,
                    "title": "Generate Technical Diagrams",
                    "agent_name": "Diagram Agent",
                    "tool_name": "render_diagram",
                    "description": "Create high-resolution architectural / circuit / workflow diagrams to accompany content.",
                    "dependencies": [1],
                    "estimated_risk": "LOW",
                    "requires_approval": False,
                    "is_parallel_safe": True,
                    "parameters": {"type": "architecture_diagram"}
                },
                {
                    "step_order": 4,
                    "title": "Document Assembly & Professional Styling",
                    "agent_name": "Word Agent",
                    "tool_name": "create_word_document",
                    "description": "Format full document with title page, executive summary, tables, diagrams, and page numbering.",
                    "dependencies": [2, 3],
                    "estimated_risk": "LOW",
                    "requires_approval": False,
                    "is_parallel_safe": False,
                    "parameters": {"output_format": "DOCX"}
                },
                {
                    "step_order": 5,
                    "title": "Quality Assurance & Final Verification",
                    "agent_name": "Quality Assurance Agent",
                    "tool_name": "verify_file_output",
                    "description": "Verify file existence, page count, formatting standards, and output integrity.",
                    "dependencies": [4],
                    "estimated_risk": "LOW",
                    "requires_approval": False,
                    "is_parallel_safe": False,
                    "parameters": {"check_integrity": True}
                }
            ]

        # Coding and bug fixing
        elif "code" in g or "error" in g or "fix" in g or "vs code" in g or "debug" in g:
            primary_intent = "CODE_INVESTIGATION_AND_REPAIR"
            selected_agents = ["Coding Agent", "Debugging Agent", "Testing Agent", "Quality Assurance Agent"]
            capabilities = ["inspect code", "modify code", "run code", "debugging", "unit testing"]

            steps = [
                {
                    "step_order": 1,
                    "title": "Inspect Workspace & Reproduce Error",
                    "agent_name": "Debugging Agent",
                    "tool_name": "search_files",
                    "description": f"Scan project files and trace error stack: {goal}",
                    "dependencies": [],
                    "estimated_risk": "LOW",
                    "requires_approval": False,
                    "is_parallel_safe": True,
                    "parameters": {"path": "."}
                },
                {
                    "step_order": 2,
                    "title": "Develop Patch & Fix",
                    "agent_name": "Coding Agent",
                    "tool_name": "edit_file",
                    "description": "Apply clean refactoring and bug resolution to the affected code units.",
                    "dependencies": [1],
                    "estimated_risk": "MEDIUM",
                    "requires_approval": False,
                    "is_parallel_safe": False,
                    "parameters": {}
                },
                {
                    "step_order": 3,
                    "title": "Run Regression Tests",
                    "agent_name": "Testing Agent",
                    "tool_name": "execute_command",
                    "description": "Execute test suite to ensure the fix resolves the issue without regressions.",
                    "dependencies": [2],
                    "estimated_risk": "LOW",
                    "requires_approval": False,
                    "is_parallel_safe": False,
                    "parameters": {"command": "pytest"}
                },
                {
                    "step_order": 4,
                    "title": "Verification and Summary Report",
                    "agent_name": "Quality Assurance Agent",
                    "tool_name": "verify_results",
                    "description": "Generate diff summary and verification report for user review.",
                    "dependencies": [3],
                    "estimated_risk": "LOW",
                    "requires_approval": False,
                    "is_parallel_safe": False,
                    "parameters": {}
                }
            ]

        # File organization & desktop maintenance
        elif "organize" in g or "download" in g or "folder" in g or "files" in g:
            primary_intent = "FILE_ORGANIZATION"
            selected_agents = ["File Agent", "System Agent", "Quality Assurance Agent"]
            capabilities = ["list files", "categorize files", "move files", "verify directory"]

            steps = [
                {
                    "step_order": 1,
                    "title": "Scan Target Directory & Classify Files",
                    "agent_name": "File Agent",
                    "tool_name": "list_files",
                    "description": "Catalog all files by extension, modification date, and document type.",
                    "dependencies": [],
                    "estimated_risk": "LOW",
                    "requires_approval": False,
                    "is_parallel_safe": True,
                    "parameters": {"target": "Downloads"}
                },
                {
                    "step_order": 2,
                    "title": "Create Organized Directory Structure",
                    "agent_name": "File Agent",
                    "tool_name": "create_folder",
                    "description": "Generate structured subfolders for Documents, Images, Archives, Installers, Code.",
                    "dependencies": [1],
                    "estimated_risk": "LOW",
                    "requires_approval": False,
                    "is_parallel_safe": False,
                    "parameters": {}
                },
                {
                    "step_order": 3,
                    "title": "Move Files into Designated Categories",
                    "agent_name": "File Agent",
                    "tool_name": "move_file",
                    "description": "Safely relocate items to respective destination folders with conflict prevention.",
                    "dependencies": [2],
                    "estimated_risk": "MEDIUM",
                    "requires_approval": False,
                    "is_parallel_safe": False,
                    "parameters": {}
                },
                {
                    "step_order": 4,
                    "title": "Verify Organization & Summary",
                    "agent_name": "Quality Assurance Agent",
                    "tool_name": "verify_file_output",
                    "description": "Confirm all items were moved accurately without data loss.",
                    "dependencies": [3],
                    "estimated_risk": "LOW",
                    "requires_approval": False,
                    "is_parallel_safe": False,
                    "parameters": {}
                }
            ]

        # General Autonomous Workflow
        else:
            primary_intent = "GENERAL_AUTONOMOUS_TASK"
            selected_agents = ["Research Agent", "Content Agent", "System Agent", "Quality Assurance Agent"]
            capabilities = ["task analysis", "execution", "validation"]

            steps = [
                {
                    "step_order": 1,
                    "title": "Analyze Goal and Discover Capabilities",
                    "agent_name": "System Agent",
                    "tool_name": "get_system_info",
                    "description": f"Gather context and environment state for: {goal}",
                    "dependencies": [],
                    "estimated_risk": "LOW",
                    "requires_approval": False,
                    "is_parallel_safe": True,
                    "parameters": {}
                },
                {
                    "step_order": 2,
                    "title": "Execute Goal Subtasks",
                    "agent_name": "Content Agent",
                    "tool_name": "generate_content",
                    "description": "Process inputs and generate the required outcomes and artifacts.",
                    "dependencies": [1],
                    "estimated_risk": "LOW",
                    "requires_approval": False,
                    "is_parallel_safe": False,
                    "parameters": {"goal": goal}
                },
                {
                    "step_order": 3,
                    "title": "Quality Verification & Output Delivery",
                    "agent_name": "Quality Assurance Agent",
                    "tool_name": "verify_results",
                    "description": "Validate task output and summarize final delivery for user.",
                    "dependencies": [2],
                    "estimated_risk": "LOW",
                    "requires_approval": False,
                    "is_parallel_safe": False,
                    "parameters": {}
                }
            ]

        plan_dict = {
            "goal": goal,
            "summary": f"Dynamic multi-agent execution plan designed for: '{goal}'",
            "primary_intent": primary_intent,
            "required_capabilities": capabilities,
            "selected_agents": selected_agents,
            "steps": steps,
            "can_execute_in_parallel": True
        }
        return json.dumps(plan_dict)


class OpenAIProvider(BaseModelProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key

    def get_provider_name(self) -> str:
        return "openai"

    async def generate_response(self, system_prompt: str, user_prompt: str, response_format: Optional[str] = None) -> str:
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.api_key)
            kwargs = {
                "model": "gpt-4o",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            }
            if response_format == "json":
                kwargs["response_format"] = {"type": "json_object"}

            response = await client.chat.completions.create(**kwargs)
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.warning(f"OpenAI provider failed, falling back to heuristic provider: {e}")
            fallback = HeuristicProvider()
            return await fallback.generate_response(system_prompt, user_prompt, response_format)


class ModelRouter:
    def __init__(self):
        self._providers: Dict[str, BaseModelProvider] = {
            "heuristic": HeuristicProvider()
        }
        if settings.OPENAI_API_KEY:
            self._providers["openai"] = OpenAIProvider(settings.OPENAI_API_KEY)

    def get_provider(self, provider_name: Optional[str] = None) -> BaseModelProvider:
        name = provider_name or settings.DEFAULT_MODEL_PROVIDER
        if name in self._providers:
            return self._providers[name]
        logger.info(f"Provider '{name}' not found, using heuristic provider.")
        return self._providers["heuristic"]

    def register_provider(self, name: str, provider: BaseModelProvider) -> None:
        self._providers[name] = provider

    async def route_task(
        self,
        task_type: str,
        system_prompt: str,
        user_prompt: str,
        response_format: Optional[str] = None
    ) -> str:
        """Route request to the most appropriate AI model or provider."""
        provider = self.get_provider()
        return await provider.generate_response(system_prompt, user_prompt, response_format)

model_router = ModelRouter()
