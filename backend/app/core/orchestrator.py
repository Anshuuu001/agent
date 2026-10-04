import asyncio
import json
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy import select, update
from backend.app.schemas.common import TaskStatus, Priority
from backend.app.schemas.tasks import DynamicPlan, PlanStepSchema
from backend.app.core.events import event_bus
from backend.app.core.agent_registry import agent_registry
from backend.app.core.tool_registry import tool_registry
from backend.app.core.security import security_manager
from backend.app.core.audit import audit_logger
from backend.app.core.worker_pool import parallel_worker_pool
from backend.app.core.verifier import verification_engine
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

            # Initial TaskLog
            log_entry = TaskLogModel(
                task_id=task_id,
                level="INFO",
                message=f"Task queued with {len(plan.steps)} DAG subtasks. Assigned workers: {', '.join(plan.selected_agents)}",
                details_json=json.dumps({"plan_summary": plan.summary})
            )
            session.add(log_entry)

            # Checkpoint
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
        """Execution pipeline utilizing Parallel DAG Worker Pool and Verification."""
        logger.info(f"Starting DAG worker execution for task: {task_id}")
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

                # Parse plan for dependencies
                plan_dict = json.loads(task.plan_json or "{}")
                plan_steps = plan_dict.get("steps", [])
                dep_map = {s["step_order"]: s.get("dependencies", []) for s in plan_steps}

            # Prepare subtasks payload for DAG engine
            subtasks_payload = []
            for s in subtasks:
                subtasks_payload.append({
                    "id": s.id,
                    "step_order": s.step_order,
                    "title": s.title,
                    "description": s.description,
                    "agent_name": s.agent_name,
                    "tool_name": s.tool_name,
                    "parameters": json.loads(s.input_data_json or "{}"),
                    "dependencies": dep_map.get(s.step_order, [])
                })

            # Handlers for worker pool events
            async def on_subtask_update(subtask_id: str, status: str, output_data: Dict[str, Any] = None, error: str = None):
                await self._update_subtask_status(subtask_id, status, output_data, error)

            async def on_log(level: str, message: str, subtask_id: str = None):
                await self._add_task_log(task_id, level, message, subtask_id=subtask_id)

            # Execute via Parallel DAG Worker Pool
            dag_success = await parallel_worker_pool.execute_dag(
                task_id=task_id,
                subtasks_list=subtasks_payload,
                on_subtask_update=on_subtask_update,
                on_log=on_log
            )

            if dag_success:
                # Perform Output Verification
                async with AsyncSessionLocal() as session:
                    task_res = await session.execute(select(TaskModel).where(TaskModel.id == task_id))
                    task_rec = task_res.scalar_one_or_none()
                    task_goal = task_rec.goal if task_rec else ""

                # Look for generated artifacts in outputs folder
                import glob
                out_files = glob.glob(f"{settings.OUTPUT_DIRECTORY}/*.*")
                verification_results = []
                for f_path in out_files[-3:]:
                    v_res = verification_engine.verify_document_artifact(f_path)
                    verification_results.append(v_res)

                summary_text = f"All {len(subtasks_payload)} subtask steps executed and verified successfully. Generated artifacts: {len(out_files)}"

                await self._update_task_status(
                    task_id,
                    TaskStatus.COMPLETED,
                    100.0,
                    result_summary=summary_text
                )
                await self._add_task_log(task_id, "INFO", f"Task verification complete: {summary_text}")
                await event_bus.emit_notification("Task Completed", f"Task {task_id[:8]} completed and verified.", "SUCCESS")
            else:
                await self._update_task_status(task_id, TaskStatus.FAILED, error_message="One or more DAG subtasks failed.")
                await self._add_task_log(task_id, "ERROR", "Task halted due to subtask execution failure.")

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

task_orchestrator = TaskOrchestrator()
