from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from backend.app.schemas.common import AgentCategory
from backend.app.schemas.agents import AgentExecutionRequest, AgentExecutionResult
from backend.app.core.agent_registry import agent_registry

router = APIRouter(prefix="/agents", tags=["Agents"])

@router.get("")
async def list_agents(category: Optional[AgentCategory] = None):
    """List all registered agents, capabilities, and real-time health."""
    return agent_registry.list_agents(category=category)

@router.get("/{agent_name}")
async def get_agent_details(agent_name: str):
    agent = agent_registry.get_agent(agent_name)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
    return agent.get_metadata()

@router.post("/execute", response_model=AgentExecutionResult)
async def execute_agent(payload: AgentExecutionRequest):
    """Directly test/execute an individual agent with an instruction."""
    return await agent_registry.execute_agent(
        agent_name=payload.agent_name,
        instruction=payload.instruction,
        task_id=payload.task_id,
        context=payload.context
    )
