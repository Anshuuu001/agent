import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from backend.app.db.database import get_db
from backend.app.db.models import Task as TaskModel, Subtask as SubtaskModel, TaskLog as TaskLogModel
from backend.app.schemas.tasks import TaskRead, TaskCreate, TaskUpdate, TaskLogRead, SubtaskRead
from backend.app.schemas.common import Priority, TaskStatus
from backend.app.core.orchestrator import task_orchestrator

router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.get("", response_model=List[TaskRead])
async def list_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(TaskModel)
    if status:
        stmt = stmt.where(TaskModel.status == status)
    if priority:
        stmt = stmt.where(TaskModel.priority == priority)
    stmt = stmt.order_by(desc(TaskModel.created_at)).limit(limit)

    res = await db.execute(stmt)
    tasks = res.scalars().all()

    output = []
    for t in tasks:
        # Load subtasks
        sub_stmt = select(SubtaskModel).where(SubtaskModel.task_id == t.id).order_by(SubtaskModel.step_order)
        sub_res = await db.execute(sub_stmt)
        subtasks = sub_res.scalars().all()

        sub_list = []
        for s in subtasks:
            sub_list.append(SubtaskRead(
                id=s.id,
                task_id=s.task_id,
                title=s.title,
                description=s.description,
                agent_name=s.agent_name,
                tool_name=s.tool_name,
                status=s.status,
                step_order=s.step_order,
                input_data=json.loads(s.input_data_json or "{}"),
                output_data=json.loads(s.output_data_json or "{}"),
                error=s.error,
                requires_approval=s.requires_approval,
                is_parallel_safe=s.is_parallel_safe,
                created_at=s.created_at,
                updated_at=s.updated_at
            ))

        output.append(TaskRead(
            id=t.id,
            title=t.title,
            goal=t.goal,
            priority=Priority(t.priority),
            status=TaskStatus(t.status),
            progress=t.progress,
            project_id=t.project_id,
            assigned_agents=json.loads(t.assigned_agents_json or "[]"),
            result_summary=t.result_summary,
            error_message=t.error_message,
            requires_approval=t.requires_approval,
            subtasks=sub_list,
            created_at=t.created_at,
            updated_at=t.updated_at
        ))
    return output


@router.get("/{task_id}", response_model=TaskRead)
async def get_task_details(task_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(TaskModel).where(TaskModel.id == task_id)
    res = await db.execute(stmt)
    t = res.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    sub_stmt = select(SubtaskModel).where(SubtaskModel.task_id == t.id).order_by(SubtaskModel.step_order)
    sub_res = await db.execute(sub_stmt)
    subtasks = sub_res.scalars().all()

    sub_list = [
        SubtaskRead(
            id=s.id,
            task_id=s.task_id,
            title=s.title,
            description=s.description,
            agent_name=s.agent_name,
            tool_name=s.tool_name,
            status=s.status,
            step_order=s.step_order,
            input_data=json.loads(s.input_data_json or "{}"),
            output_data=json.loads(s.output_data_json or "{}"),
            error=s.error,
            requires_approval=s.requires_approval,
            is_parallel_safe=s.is_parallel_safe,
            created_at=s.created_at,
            updated_at=s.updated_at
        ) for s in subtasks
    ]

    return TaskRead(
        id=t.id,
        title=t.title,
        goal=t.goal,
        priority=Priority(t.priority),
        status=TaskStatus(t.status),
        progress=t.progress,
        project_id=t.project_id,
        assigned_agents=json.loads(t.assigned_agents_json or "[]"),
        result_summary=t.result_summary,
        error_message=t.error_message,
        requires_approval=t.requires_approval,
        subtasks=sub_list,
        created_at=t.created_at,
        updated_at=t.updated_at
    )


@router.get("/{task_id}/logs", response_model=List[TaskLogRead])
async def get_task_logs(task_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(TaskLogModel).where(TaskLogModel.task_id == task_id).order_by(TaskLogModel.timestamp.asc())
    res = await db.execute(stmt)
    logs = res.scalars().all()
    return [
        TaskLogRead(
            id=l.id,
            task_id=l.task_id,
            subtask_id=l.subtask_id,
            level=l.level,
            agent_name=l.agent_name,
            message=l.message,
            details=json.loads(l.details_json or "{}"),
            timestamp=l.timestamp
        ) for l in logs
    ]


@router.post("/{task_id}/pause")
async def pause_task(task_id: str):
    await task_orchestrator.pause_task(task_id)
    return {"status": "PAUSED", "task_id": task_id}


@router.post("/{task_id}/resume")
async def resume_task(task_id: str):
    await task_orchestrator.resume_task(task_id)
    return {"status": "RESUMED", "task_id": task_id}


@router.post("/{task_id}/cancel")
async def cancel_task(task_id: str):
    await task_orchestrator.cancel_task(task_id)
    return {"status": "CANCELLED", "task_id": task_id}


@router.patch("/{task_id}/priority")
async def update_priority(task_id: str, priority: Priority):
    await task_orchestrator.update_task_priority(task_id, priority)
    return {"task_id": task_id, "priority": priority.value}
