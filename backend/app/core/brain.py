import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from backend.app.schemas.tasks import DynamicPlan, PlanStepSchema
from backend.app.schemas.chat import BrainResponse
from backend.app.core.model_router import model_router
from backend.app.core.agent_registry import agent_registry
from backend.app.core.tool_registry import tool_registry
from backend.app.core.memory import memory_manager
from backend.app.core.orchestrator import task_orchestrator
from backend.app.core.security import security_manager
from backend.app.schemas.common import Priority, MemoryTier
from backend.app.db.database import AsyncSessionLocal
from backend.app.db.models import Session as SessionModel, ChatMessage as ChatMessageModel

logger = logging.getLogger("desktop_ai.brain")

class AIBrain:
    """
    Central AI Brain:
    USER REQUEST -> Intent Understanding -> Context Analysis -> Goal Definition ->
    Task Planning -> Capability Discovery -> Agent Selection -> Tool Selection ->
    Dependency Analysis -> Execution Scheduling -> Verification -> Result
    """
    def __init__(self):
        pass

    async def process_user_input(
        self,
        user_message: str,
        session_id: Optional[str] = None,
        autonomy_level: Optional[int] = None,
        auto_execute: bool = True
    ) -> BrainResponse:
        logger.info(f"AI Brain received user prompt: '{user_message}'")

        # 1. Ensure conversation session exists
        session_obj = await self._get_or_create_session(session_id)
        current_session_id = session_obj.id

        # 2. Record User ChatMessage
        await self._save_chat_message(current_session_id, "user", user_message, "text")

        # 3. Retrieve Context & Memory
        past_context = await memory_manager.get_context_for_prompt(user_message)

        # 4. Check if Emergency Stop is active
        if security_manager.is_emergency_stop_active:
            reply = "⚠️ Emergency Stop is currently ACTIVE. All execution pipelines are paused. You can resume operations from the Settings or top bar."
            await self._save_chat_message(current_session_id, "assistant", reply, "warning")
            return BrainResponse(
                session_id=current_session_id,
                reply_text=reply,
                intent_detected="EMERGENCY_HALT",
                suggested_actions=["Resume System", "Check Audit Logs"]
            )

        # 5. Dynamic Goal & Plan Generation
        system_prompt = f"""You are the Universal Autonomous Desktop AI Brain.
You break down complex human goals into structured multi-agent execution plans.
Registered Agents: {[a['name'] for a in agent_registry.list_agents()]}
Registered Tools: {[t['name'] for t in tool_registry.list_tools()]}
{past_context}
Generate a JSON representation of DynamicPlan with fields: goal, summary, primary_intent, required_capabilities, selected_agents, steps, can_execute_in_parallel.
"""
        plan_json_str = await model_router.route_task(
            task_type="PLANNING",
            system_prompt=system_prompt,
            user_prompt=user_message,
            response_format="json"
        )

        try:
            plan_dict = json.loads(plan_json_str)
            plan = DynamicPlan(**plan_dict)
        except Exception as e:
            logger.error(f"Failed to parse plan JSON: {e}. Generating fallback plan.")
            plan = self._create_fallback_plan(user_message)

        # 6. Store in Short-Term / Task Memory
        await memory_manager.store(
            tier=MemoryTier.SHORT_TERM,
            key=f"goal_{datetime.now().strftime('%H%M%S')}",
            content=f"Goal: {plan.goal} | Selected Agents: {', '.join(plan.selected_agents)}",
            context_type="PLAN"
        )

        task_id = None
        if auto_execute:
            # 7. Create and Schedule Task in Orchestrator
            task_id = await task_orchestrator.create_task_from_plan(
                title=f"{plan.primary_intent.replace('_', ' ').title()}: {plan.goal[:40]}",
                goal=plan.goal,
                plan=plan,
                priority=Priority.NORMAL
            )
            # Trigger asynchronous background execution
            await task_orchestrator.execute_task_async(task_id)

        reply_text = (
            f"I have analyzed your goal and orchestrated a dynamic plan with {len(plan.steps)} subtasks.\n\n"
            f"• **Goal:** {plan.goal}\n"
            f"• **Assigned Agents:** {', '.join(plan.selected_agents)}\n"
            f"• **Execution Strategy:** {'Parallel & Sequential Pipeline' if plan.can_execute_in_parallel else 'Sequential'}\n\n"
            f"Status: **Running autonomously** with real-time verification."
        )

        await self._save_chat_message(
            current_session_id,
            "assistant",
            reply_text,
            "plan",
            metadata={"plan": plan.model_dump(), "task_id": task_id}
        )

        return BrainResponse(
            session_id=current_session_id,
            reply_text=reply_text,
            intent_detected=plan.primary_intent,
            goal=plan.goal,
            plan=plan,
            task_id=task_id,
            requires_approval=any(s.requires_approval for s in plan.steps),
            suggested_actions=["View Live Task", "Inspect Agent Workflows", "Check Audit Log"]
        )

    def _create_fallback_plan(self, goal: str) -> DynamicPlan:
        return DynamicPlan(
            goal=goal,
            summary=f"Direct autonomous execution for: {goal}",
            primary_intent="GENERAL_TASK",
            required_capabilities=["task analysis", "execution", "validation"],
            selected_agents=["Research Agent", "Content Agent", "Quality Assurance Agent"],
            steps=[
                PlanStepSchema(
                    step_order=1,
                    title="Context Analysis & Research",
                    agent_name="Research Agent",
                    tool_name="search_web",
                    description=f"Gather foundational information for: {goal}",
                    dependencies=[],
                    parameters={"query": goal}
                ),
                PlanStepSchema(
                    step_order=2,
                    title="Generate Deliverables",
                    agent_name="Content Agent",
                    tool_name="generate_content",
                    description="Synthesize target outputs.",
                    dependencies=[1],
                    parameters={"goal": goal}
                ),
                PlanStepSchema(
                    step_order=3,
                    title="QA Inspection & Validation",
                    agent_name="Quality Assurance Agent",
                    tool_name="verify_results",
                    description="Verify compliance and finalize delivery.",
                    dependencies=[2],
                    parameters={}
                )
            ]
        )

    async def _get_or_create_session(self, session_id: Optional[str]) -> SessionModel:
        async with AsyncSessionLocal() as session:
            if session_id:
                stmt = select(SessionModel).where(SessionModel.id == session_id)
                res = await session.execute(stmt)
                existing = res.scalar_one_or_none()
                if existing:
                    return existing

            import uuid
            new_session = SessionModel(
                session_token=str(uuid.uuid4()),
                autonomy_level=security_manager.get_autonomy_level().value,
                is_active=True,
                created_at=datetime.now(timezone.utc),
                last_active_at=datetime.now(timezone.utc)
            )
            session.add(new_session)
            await session.commit()
            await session.refresh(new_session)
            return new_session

    async def _save_chat_message(
        self,
        session_id: str,
        role: str,
        content: str,
        message_type: str = "text",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        async with AsyncSessionLocal() as session:
            msg = ChatMessageModel(
                session_id=session_id,
                role=role,
                content=content,
                message_type=message_type,
                metadata_json=json.dumps(metadata or {}),
                timestamp=datetime.now(timezone.utc)
            )
            session.add(msg)
            await session.commit()

ai_brain = AIBrain()
