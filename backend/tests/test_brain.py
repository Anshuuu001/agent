import pytest
from backend.app.core.brain import ai_brain
from backend.app.core.security import security_manager

@pytest.mark.asyncio
async def test_brain_plan_generation():
    goal = "Make a 15-page college microproject on 2-to-4 Decoder"
    response = await ai_brain.process_user_input(
        user_message=goal,
        auto_execute=False
    )
    assert response is not None
    assert response.plan is not None
    assert response.plan.goal == goal
    assert len(response.plan.steps) > 0
    assert "Research Agent" in response.plan.selected_agents

@pytest.mark.asyncio
async def test_brain_emergency_stop_halts_plan():
    security_manager.trigger_emergency_stop()
    try:
        response = await ai_brain.process_user_input(
            user_message="Do some work",
            auto_execute=False
        )
        assert response.intent_detected == "EMERGENCY_HALT"
        assert "Emergency Stop is currently ACTIVE" in response.reply_text
    finally:
        security_manager.resume_from_emergency_stop()
