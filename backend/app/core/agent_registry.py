import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from backend.app.schemas.common import AgentStatus, AgentHealth, AgentCategory
from backend.app.schemas.agents import AgentExecutionResult
from backend.app.core.events import event_bus
from backend.app.core.tool_registry import tool_registry

logger = logging.getLogger("desktop_ai.agents")

class BaseAgent(ABC):
    name: str
    display_name: str
    description: str
    category: AgentCategory = AgentCategory.GENERAL
    version: str = "1.0.0"
    capabilities: List[str] = []
    required_tools: List[str] = []
    permissions: List[str] = []
    input_schema: Dict[str, Any] = {}
    output_schema: Dict[str, Any] = {}

    def __init__(self):
        self.status: AgentStatus = AgentStatus.IDLE
        self.health: AgentHealth = AgentHealth.HEALTHY
        self.current_task_id: Optional[str] = None
        self.last_execution_time_ms: float = 0.0

    async def set_status(self, new_status: AgentStatus, task_id: Optional[str] = None):
        self.status = new_status
        self.current_task_id = task_id
        await event_bus.emit_agent_status(
            agent_name=self.name,
            status=new_status.value,
            current_task=task_id,
            health=self.health.value
        )

    @abstractmethod
    async def execute(self, instruction: str, context: Optional[Dict[str, Any]] = None) -> AgentExecutionResult:
        """Execute agent workflow for the given instruction."""
        pass

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "category": self.category.value,
            "version": self.version,
            "capabilities": self.capabilities,
            "required_tools": self.required_tools,
            "permissions": self.permissions,
            "status": self.status.value,
            "health": self.health.value,
            "current_task_id": self.current_task_id,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema
        }


class AgentRegistry:
    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}

    def register(self, agent: BaseAgent) -> None:
        """Register an agent into the registry."""
        self._agents[agent.name] = agent
        logger.info(f"Registered Agent: {agent.name} ({agent.category.value}) - Capabilities: {len(agent.capabilities)}")

    def get_agent(self, name: str) -> Optional[BaseAgent]:
        return self._agents.get(name)

    def list_agents(self, category: Optional[AgentCategory] = None) -> List[Dict[str, Any]]:
        agents = list(self._agents.values())
        if category:
            agents = [a for a in agents if a.category == category]
        return [a.get_metadata() for a in agents]

    def find_agents_for_capabilities(self, capabilities: List[str]) -> List[BaseAgent]:
        """Find agents that provide any of the requested capabilities."""
        matched = []
        caps_lower = [c.lower() for c in capabilities]
        for agent in self._agents.values():
            for agent_cap in agent.capabilities:
                if any(c in agent_cap.lower() or agent_cap.lower() in c for c in caps_lower):
                    if agent not in matched:
                        matched.append(agent)
        return matched

    async def execute_agent(
        self,
        agent_name: str,
        instruction: str,
        task_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentExecutionResult:
        agent = self.get_agent(agent_name)
        if not agent:
            return AgentExecutionResult(
                agent_name=agent_name,
                status="FAILED",
                summary=f"Agent '{agent_name}' not found in registry.",
                error=f"Agent '{agent_name}' not found"
            )

        start_time = time.time()
        await agent.set_status(AgentStatus.RUNNING, task_id=task_id)
        
        try:
            result = await agent.execute(instruction, context or {})
            result.execution_time_ms = round((time.time() - start_time) * 1000, 2)
            await agent.set_status(AgentStatus.IDLE)
            return result
        except Exception as e:
            agent.health = AgentHealth.DEGRADED
            await agent.set_status(AgentStatus.ERROR, task_id=task_id)
            logger.error(f"Error during agent execution {agent_name}: {e}", exc_info=True)
            return AgentExecutionResult(
                agent_name=agent_name,
                status="FAILED",
                summary=f"Agent encountered error: {e}",
                error=str(e),
                execution_time_ms=round((time.time() - start_time) * 1000, 2)
            )

agent_registry = AgentRegistry()
