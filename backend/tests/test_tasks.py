import pytest
from backend.app.core.orchestrator import task_orchestrator
from backend.app.schemas.tasks import DynamicPlan, PlanStepSchema
from backend.app.schemas.common import Priority, TaskStatus
from backend.app.db.database import init_db

@pytest.mark.asyncio
async def test_task_creation_and_pause_resume():
    await init_db()

    plan = DynamicPlan(
        goal="Test Goal",
        summary="Test Summary",
        primary_intent="TEST",
        required_capabilities=["test"],
        selected_agents=["Research Agent"],
        steps=[
            PlanStepSchema(
                step_order=1,
                title="Step 1",
                agent_name="Research Agent",
                tool_name="search_web",
                description="Step 1 details",
                dependencies=[]
            )
        ]
    )

    task_id = await task_orchestrator.create_task_from_plan(
        title="Test Task",
        goal="Test Goal",
        plan=plan,
        priority=Priority.HIGH
    )
    assert task_id is not None

    # Pause task
    await task_orchestrator.pause_task(task_id)
    assert task_id in task_orchestrator._paused_task_ids

    # Resume task
    await task_orchestrator.resume_task(task_id)
    assert task_id not in task_orchestrator._paused_task_ids

    # Update Priority
    await task_orchestrator.update_task_priority(task_id, Priority.URGENT)
