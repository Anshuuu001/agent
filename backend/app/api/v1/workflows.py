import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from backend.app.db.database import get_db
from backend.app.db.models import Workflow as WorkflowModel, WorkflowStep as WorkflowStepModel
from backend.app.schemas.workflows import WorkflowCreate, WorkflowRead, WorkflowStepSchema

router = APIRouter(prefix="/workflows", tags=["Workflows"])

@router.get("", response_model=List[WorkflowRead])
async def list_workflows(db: AsyncSession = Depends(get_db)):
    stmt = select(WorkflowModel).order_by(desc(WorkflowModel.created_at))
    res = await db.execute(stmt)
    workflows = res.scalars().all()

    output = []
    for w in workflows:
        steps_stmt = select(WorkflowStepModel).where(WorkflowStepModel.workflow_id == w.id).order_by(WorkflowStepModel.step_order)
        steps_res = await db.execute(steps_stmt)
        steps = steps_res.scalars().all()

        output.append(WorkflowRead(
            id=w.id,
            name=w.name,
            description=w.description,
            tags=json.loads(w.tags_json or "[]"),
            is_reusable=w.is_reusable,
            created_by=w.created_by,
            metadata=json.loads(w.metadata_json or "{}"),
            created_at=w.created_at,
            updated_at=w.updated_at,
            steps=[
                WorkflowStepSchema(
                    step_order=s.step_order,
                    title=s.title,
                    agent_name=s.agent_name,
                    tool_name=s.tool_name,
                    parameters_template=json.loads(s.parameters_template_json or "{}"),
                    depends_on_step=s.depends_on_step
                ) for s in steps
            ]
        ))
    return output

@router.post("", response_model=WorkflowRead)
async def create_workflow(payload: WorkflowCreate, db: AsyncSession = Depends(get_db)):
    wf = WorkflowModel(
        name=payload.name,
        description=payload.description,
        tags_json=json.dumps(payload.tags),
        is_reusable=payload.is_reusable,
        created_by="user",
        metadata_json=json.dumps(payload.metadata)
    )
    db.add(wf)
    await db.commit()
    await db.refresh(wf)

    for s in payload.steps:
        step_model = WorkflowStepModel(
            workflow_id=wf.id,
            step_order=s.step_order,
            title=s.title,
            agent_name=s.agent_name,
            tool_name=s.tool_name,
            parameters_template_json=json.dumps(s.parameters_template),
            depends_on_step=s.depends_on_step
        )
        db.add(step_model)

    await db.commit()
    return await list_workflows(db=db)
