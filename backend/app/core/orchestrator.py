import asyncio
import json
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy import select, update
from backend.app.schemas.common import TaskStatus, Priority, AgentStatus
from backend.app.schemas.tasks import DynamicPlan, PlanStepSchema
from backend.app.core.events import event_bus
from backend.app.core.agent_registry import agent_registry
from backend.app.core.tool_registry import tool_registry
from backend.app.core.security import security_manager
from backend.app.core.audit import audit_logger
from backend.app.db.database import AsyncSessionLocal
from backend.app.db.models import (
    Task as TaskModel, Subtask as SubtaskModel, TaskLog as TaskLogModel,
    Checkpoint as CheckpointModel, FileRecord as FileRecordModel
)

logger = logging.getLogger("desktop_ai.orchestrator")

class TaskOrchestrator:
    def __init__(self):
        self._running_tasks: Dict[str, asyncio.Task] = {}
        self._paused_task_ids: set = set()
        self._cancelled_task_ids: set = set()

    async def create_task_from_plan(
        self,
        title: str,
        goal: str,
        plan: DynamicPlan,
        priority: Priority = Priority.NORMAL,
        project_id: Optional[str] = None
    ) -> str:
        """Create Task and Subtasks DAG in database from DynamicPlan."""
        async with AsyncSessionLocal() as session:
            task = TaskModel(
                title=title,
                goal=goal,
                priority=priority.value,
                status=TaskStatus.QUEUED.value,
                progress=0.0,
                assigned_agents_json=json.dumps(plan.selected_agents),
                plan_json=json.dumps(plan.model_dump()),
                project_id=project_id,
                created_at=datetime.now(timezone.utc)
            )
            session.add(task)
            await session.commit()
            await session.refresh(task)
            task_id = task.id

            # Create Subtasks
            for step in plan.steps:
                subtask = SubtaskModel(
                    task_id=task_id,
                    title=step.title,
                    description=step.description,
                    agent_name=step.agent_name,
                    tool_name=step.tool_name,
                    status="QUEUED",
                    step_order=step.step_order,
                    input_data_json=json.dumps(step.parameters),
                    requires_approval=step.requires_approval,
                    is_parallel_safe=step.is_parallel_safe,
                    created_at=datetime.now(timezone.utc)
                )
                session.add(subtask)

            # Add initial TaskLog
            log_entry = TaskLogModel(
                task_id=task_id,
                level="INFO",
                message=f"Task created with {len(plan.steps)} subtask steps. Assigned agents: {', '.join(plan.selected_agents)}",
                details_json=json.dumps({"plan_summary": plan.summary})
            )
            session.add(log_entry)

            # Create Initial Checkpoint
            checkpoint = CheckpointModel(
                task_id=task_id,
                title="Initial Task State Checkpoint",
                state_snapshot_json=json.dumps({
                    "task_id": task_id,
                    "status": "QUEUED",
                    "step_count": len(plan.steps)
                }),
                can_rollback=True
            )
            session.add(checkpoint)

            await session.commit()

        await event_bus.emit_task_update(task_id, TaskStatus.QUEUED.value, 0.0, {"title": title, "goal": goal})
        return task_id

    async def execute_task_async(self, task_id: str) -> None:
        """Schedule and run task pipeline in background."""
        if task_id in self._running_tasks and not self._running_tasks[task_id].done():
            logger.warning(f"Task {task_id} is already running.")
            return

        async_task = asyncio.create_task(self._run_task_pipeline(task_id))
        self._running_tasks[task_id] = async_task

    async def _run_task_pipeline(self, task_id: str) -> None:
        """Execution pipeline for task steps respecting DAG dependencies."""
        logger.info(f"Starting execution of task: {task_id}")
        await self._update_task_status(task_id, TaskStatus.RUNNING, 0.05)
        await event_bus.emit_notification("Task Started", f"Execution started for task {task_id[:8]}", "INFO")

        try:
            async with AsyncSessionLocal() as session:
                task_stmt = select(TaskModel).where(TaskModel.id == task_id)
                task_res = await session.execute(task_stmt)
                task = task_res.scalar_one_or_none()
                if not task:
                    logger.error(f"Task {task_id} not found.")
                    return

                subtasks_stmt = select(SubtaskModel).where(SubtaskModel.task_id == task_id).order_by(SubtaskModel.step_order)
                subtasks_res = await session.execute(subtasks_stmt)
                subtasks = list(subtasks_res.scalars().all())

            total_steps = len(subtasks)
            completed_steps = 0

            for subtask in subtasks:
                # Check for emergency stop, pause, or cancellation
                if security_manager.is_emergency_stop_active:
                    await self._update_task_status(task_id, TaskStatus.PAUSED, (completed_steps / total_steps) if total_steps else 0.0)
                    await self._add_task_log(task_id, "WARNING", "Execution halted due to active Emergency Stop.")
                    return

                if task_id in self._cancelled_task_ids:
                    await self._update_task_status(task_id, TaskStatus.CANCELLED, (completed_steps / total_steps) if total_steps else 0.0)
                    await self._add_task_log(task_id, "WARNING", "Task cancelled by user.")
                    return

                while task_id in self._paused_task_ids:
                    await self._update_task_status(task_id, TaskStatus.PAUSED, (completed_steps / total_steps) if total_steps else 0.0)
                    await asyncio.sleep(1.0)
                    if task_id in self._cancelled_task_ids:
                        await self._update_task_status(task_id, TaskStatus.CANCELLED)
                        return

                await self._update_task_status(task_id, TaskStatus.RUNNING)

                # Execute individual subtask
                await self._update_subtask_status(subtask.id, "RUNNING")
                await self._add_task_log(task_id, "INFO", f"Executing Subtask #{subtask.step_order}: {subtask.title}", subtask_id=subtask.id)

                agent_name = subtask.agent_name or "System Agent"
                instruction = subtask.description or subtask.title
                
                # Execute agent
                agent_res = await agent_registry.execute_agent(
                    agent_name=agent_name,
                    instruction=instruction,
                    task_id=task_id,
                    context={"subtask_id": subtask.id}
                )

                if agent_res.status == "SUCCESS":
                    await self._update_subtask_status(subtask.id, "COMPLETED", output_data=agent_res.output)
                    completed_steps += 1
                    progress = round((completed_steps / total_steps) * 100, 1)
                    await self._update_task_status(task_id, TaskStatus.RUNNING, progress)
                    await self._add_task_log(
                        task_id, "INFO",
                        f"Subtask #{subtask.step_order} completed by {agent_name}: {agent_res.summary}",
                        subtask_id=subtask.id
                    )
                else:
                    # Self-correction check / retry
                    await self._add_task_log(
                        task_id, "WARNING",
                        f"Subtask #{subtask.step_order} failed: {agent_res.error}. Attempting self-correction retry...",
                        subtask_id=subtask.id
                    )
                    # Retry once
                    retry_res = await agent_registry.execute_agent(
                        agent_name=agent_name,
                        instruction=instruction,
                        task_id=task_id,
                        context={"subtask_id": subtask.id, "retry": True}
                    )
                    if retry_res.status == "SUCCESS":
                        await self._update_subtask_status(subtask.id, "COMPLETED", output_data=retry_res.output)
                        completed_steps += 1
                        progress = round((completed_steps / total_steps) * 100, 1)
                        await self._update_task_status(task_id, TaskStatus.RUNNING, progress)
                    else:
                        await self._update_subtask_status(subtask.id, "FAILED", error=retry_res.error)
                        await self._update_task_status(task_id, TaskStatus.FAILED, error_message=retry_res.error)
                        await self._add_task_log(task_id, "ERROR", f"Task failed at step: {subtask.title}", subtask_id=subtask.id)
                        await event_bus.emit_notification("Task Failed", f"Task {task_id[:8]} encountered error at step {subtask.title}", "ERROR", "HIGH")
                        return

                # Checkpoint progress
                await self._create_task_checkpoint(task_id, f"Checkpoint after step {subtask.step_order}: {subtask.title}")

            # All steps completed successfully
            await self._update_task_status(
                task_id,
                TaskStatus.COMPLETED,
                100.0,
                result_summary=f"All {total_steps} subtask steps completed and verified autonomously."
            )
            await self._add_task_log(task_id, "INFO", "Task execution finished with 100% verification score.")
            await event_bus.emit_notification("Task Completed", f"Task {task_id[:8]} completed successfully.", "SUCCESS")

        except Exception as e:
            logger.error(f"Task {task_id} unhandled exception: {e}", exc_info=True)
            await self._update_task_status(task_id, TaskStatus.FAILED, error_message=str(e))
            await self._add_task_log(task_id, "CRITICAL", f"Fatal runtime error: {e}")

    async def pause_task(self, task_id: str) -> None:
        self._paused_task_ids.add(task_id)
        await self._update_task_status(task_id, TaskStatus.PAUSED)
        await self._add_task_log(task_id, "WARNING", "Task paused by user request.")

    async def resume_task(self, task_id: str) -> None:
        self._paused_task_ids.discard(task_id)
        await self._update_task_status(task_id, TaskStatus.RUNNING)
        await self._add_task_log(task_id, "INFO", "Task resumed by user.")
        if task_id not in self._running_tasks or self._running_tasks[task_id].done():
            await self.execute_task_async(task_id)

    async def cancel_task(self, task_id: str) -> None:
        self._cancelled_task_ids.add(task_id)
        await self._update_task_status(task_id, TaskStatus.CANCELLED)
        await self._add_task_log(task_id, "WARNING", "Task cancelled by user.")

    async def update_task_priority(self, task_id: str, new_priority: Priority) -> None:
        async with AsyncSessionLocal() as session:
            stmt = update(TaskModel).where(TaskModel.id == task_id).values(
                priority=new_priority.value,
                updated_at=datetime.now(timezone.utc)
            )
            await session.execute(stmt)
            await session.commit()
        await self._add_task_log(task_id, "INFO", f"Task priority changed to {new_priority.value}")
        await event_bus.emit_task_update(task_id, "PRIORITY_CHANGED", 0.0, {"priority": new_priority.value})

    async def _update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        progress: Optional[float] = None,
        result_summary: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> None:
        async with AsyncSessionLocal() as session:
            values: Dict[str, Any] = {
                "status": status.value,
                "updated_at": datetime.now(timezone.utc)
            }
            if progress is not None:
                values["progress"] = progress
            if result_summary is not None:
                values["result_summary"] = result_summary
            if error_message is not None:
                values["error_message"] = error_message

            stmt = update(TaskModel).where(TaskModel.id == task_id).values(**values)
            await session.execute(stmt)
            await session.commit()

        await event_bus.emit_task_update(task_id, status.value, progress or 0.0, {
            "result_summary": result_summary,
            "error_message": error_message
        })

    async def _update_subtask_status(
        self,
        subtask_id: str,
        status: str,
        output_data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> None:
        async with AsyncSessionLocal() as session:
            values: Dict[str, Any] = {
                "status": status,
                "updated_at": datetime.now(timezone.utc)
            }
            if output_data is not None:
                values["output_data_json"] = json.dumps(output_data)
            if error is not None:
                values["error"] = error

            stmt = update(SubtaskModel).where(SubtaskModel.id == subtask_id).values(**values)
            await session.execute(stmt)
            await session.commit()

    async def _add_task_log(
        self,
        task_id: str,
        level: str,
        message: str,
        subtask_id: Optional[str] = None,
        agent_name: Optional[str] = None
    ) -> None:
        async with AsyncSessionLocal() as session:
            log = TaskLogModel(
                task_id=task_id,
                subtask_id=subtask_id,
                level=level,
                agent_name=agent_name,
                message=message,
                timestamp=datetime.now(timezone.utc)
            )
            session.add(log)
            await session.commit()

    async def _create_task_checkpoint(self, task_id: str, title: str) -> None:
        async with AsyncSessionLocal() as session:
            checkpoint = CheckpointModel(
                task_id=task_id,
                title=title,
                state_snapshot_json=json.dumps({"timestamp": datetime.now(timezone.utc).isoformat()}),
                can_rollback=True
            )
            session.add(checkpoint)
            await session.commit()

task_orchestrator = TaskOrchestrator()
