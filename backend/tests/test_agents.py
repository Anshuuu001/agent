import pytest
from backend.app.core.agent_registry import agent_registry

def test_agent_registry_initialization():
    agents = agent_registry.list_agents()
    assert len(agents) >= 20
    agent_names = [a["name"] for a in agents]
    assert "Research Agent" in agent_names
    assert "Coding Agent" in agent_names
    assert "Word Agent" in agent_names
    assert "Quality Assurance Agent" in agent_names
    assert "Desktop Agent" in agent_names

def test_find_agents_by_capability():
    research_matches = agent_registry.find_agents_for_capabilities(["web research"])
    assert len(research_matches) >= 1
    assert any(a.name == "Research Agent" for a in research_matches)

    code_matches = agent_registry.find_agents_for_capabilities(["modify code"])
    assert len(code_matches) >= 1
    assert any(a.name == "Coding Agent" for a in code_matches)

@pytest.mark.asyncio
async def test_agent_execution():
    result = await agent_registry.execute_agent(
        agent_name="Research Agent",
        instruction="Quantum Computing"
    )
    assert result.status == "SUCCESS"
    assert "Quantum Computing" in result.summary
    assert len(result.tools_used) > 0
