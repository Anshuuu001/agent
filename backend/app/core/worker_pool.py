import asyncio
import json
import logging
import time
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timezone
from backend.app.schemas.common import TaskStatus
from backend.app.core.agent_registry import agent_registry
from backend.app.core.tool_registry import tool_registry
from backend.app.core.events import event_bus
from backend.app.core.security import security_manager

logger = logging.getLogger("desktop_ai.worker_pool")

class SharedTaskContext:
    """Inter-agent memory and data exchange bus for a running task."""
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.data: Dict[str, Any] = {}
        self.step_outputs: Dict[int, Any] = {}

    def set(self, key: str, value: Any):
        self.data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def record_step_output(self, step_order: int, output: Any):
        self.step_outputs[step_order] = output

    def get_predecessor_outputs(self, step_orders: List[int]) -> Dict[int, Any]:
        return {s: self.step_outputs.get(s) for s in step_orders if s in self.step_outputs}


class ParallelDAGWorkerPool:
    """
    Asynchronous Parallel DAG Worker Pool:
    Executes independent subtasks concurrently while strictly honoring dependency edges.
    """
    def __init__(self, max_concurrency: int = 4):
        self.max_concurrency = max_concurrency
        self._semaphore = asyncio.Semaphore(max_concurrency)

    async def execute_dag(
        self,
        task_id: str,
        subtasks_list: List[Dict[str, Any]],
        on_subtask_update,
        on_log
    ) -> bool:
        shared_context = SharedTaskContext(task_id)
        
        # Build dependency graph
        completed_steps: Set[int] = set()
        failed_steps: Set[int] = set()
        running_step_tasks: Dict[int, asyncio.Task] = {}
        
        total_steps = len(subtasks_list)
        step_map = {s["step_order"]: s for s in subtasks_list}
        all_steps = set(step_map.keys())

        logger.info(f"[DAG Engine] Starting execution of {total_steps} subtasks for Task {task_id}")

        while len(completed_steps) < total_steps and not failed_steps:
            # Check for emergency stop
            if security_manager.is_emergency_stop_active:
                await on_log("WARNING", "Execution halted due to active Emergency Stop.")
                return False

            # Find ready steps (dependencies satisfied and not already started)
            ready_steps = []
            for step_order in all_steps:
                if step_order not in completed_steps and step_order not in running_step_tasks:
                    deps = set(step_map[step_order].get("dependencies", []))
                    if deps.issubset(completed_steps):
                        ready_steps.append(step_order)

            # Launch ready steps concurrently up to concurrency limit
            for step_order in ready_steps:
                subtask_info = step_map[step_order]
                task_coro = self._run_single_subtask_with_semaphore(
                    task_id=task_id,
                    subtask_info=subtask_info,
                    shared_context=shared_context,
                    on_subtask_update=on_subtask_update,
                    on_log=on_log
                )
                running_step_tasks[step_order] = asyncio.create_task(task_coro)

            if not running_step_tasks:
                if len(completed_steps) < total_steps:
                    logger.error(f"[DAG Engine] Deadlock or unresolvable dependencies in task {task_id}")
                    await on_log("ERROR", "DAG Dependency deadlock detected.")
                    return False
                break

            # Wait for at least one running subtask to complete
            done_tasks, _ = await asyncio.wait(
                running_step_tasks.values(),
                return_when=asyncio.FIRST_COMPLETED
            )

            for completed_task in done_tasks:
                # Identify which step finished
                finished_step_order = None
                for s_order, t in list(running_step_tasks.items()):
                    if t == completed_task:
                        finished_step_order = s_order
                        del running_step_tasks[s_order]
                        break

                if finished_step_order is not None:
                    try:
                        success = completed_task.result()
                        if success:
                            completed_steps.add(finished_step_order)
                            progress = round((len(completed_steps) / total_steps) * 100, 1)
                            await event_bus.emit_task_update(task_id, TaskStatus.RUNNING.value, progress)
                        else:
                            failed_steps.add(finished_step_order)
                    except Exception as e:
                        logger.error(f"[DAG Engine] Step {finished_step_order} raised exception: {e}")
                        failed_steps.add(finished_step_order)

        return len(failed_steps) == 0

    async def _run_single_subtask_with_semaphore(
        self,
        task_id: str,
        subtask_info: Dict[str, Any],
        shared_context: SharedTaskContext,
        on_subtask_update,
        on_log
    ) -> bool:
        async with self._semaphore:
            step_order = subtask_info["step_order"]
            subtask_id = subtask_info.get("id") or f"step_{step_order}"
            title = subtask_info["title"]
            agent_name = subtask_info.get("agent_name") or "System Agent"
            tool_name = subtask_info.get("tool_name")
            params = subtask_info.get("parameters", {})

            # Gather predecessor outputs from shared context
            deps = subtask_info.get("dependencies", [])
            pred_data = shared_context.get_predecessor_outputs(deps)

            await on_subtask_update(subtask_id, "RUNNING")
            await on_log("INFO", f"▶ Starting Subtask #{step_order} ({agent_name}): {title}", subtask_id=subtask_id)

            # Context enriched with predecessor agent outputs
            exec_context = {
                "task_id": task_id,
                "subtask_id": subtask_id,
                "step_order": step_order,
                "predecessor_data": pred_data
            }

            try:
                # 1. Direct tool execution if specified
                if tool_name and tool_registry.get_tool(tool_name):
                    res = await tool_registry.execute_tool(
                        tool_name=tool_name,
                        parameters=params,
                        task_id=task_id,
                        subtask_id=subtask_id,
                        agent_name=agent_name
                    )
                    if res.status == "SUCCESS":
                        shared_context.record_step_output(step_order, res.result)
                        await on_subtask_update(subtask_id, "COMPLETED", output_data=res.result)
                        await on_log("INFO", f"✔ Completed #{step_order} [{tool_name}]: {res.execution_time_ms}ms", subtask_id=subtask_id)
                        return True
                    else:
                        await on_subtask_update(subtask_id, "FAILED", error=res.error)
                        await on_log("ERROR", f"✖ Failed #{step_order} [{tool_name}]: {res.error}", subtask_id=subtask_id)
                        return False

                # 2. Agent Execution
                agent_res = await agent_registry.execute_agent(
                    agent_name=agent_name,
                    instruction=title,
                    task_id=task_id,
                    context=exec_context
                )

                if agent_res.status == "SUCCESS":
                    shared_context.record_step_output(step_order, agent_res.output)
                    await on_subtask_update(subtask_id, "COMPLETED", output_data=agent_res.output)
                    await on_log("INFO", f"✔ Completed #{step_order} ({agent_name}): {agent_res.summary}", subtask_id=subtask_id)
                    return True
                else:
                    await on_subtask_update(subtask_id, "FAILED", error=agent_res.error)
                    await on_log("ERROR", f"✖ Failed #{step_order} ({agent_name}): {agent_res.error}", subtask_id=subtask_id)
                    return False

            except Exception as e:
                logger.error(f"Error in subtask execution #{step_order}: {e}", exc_info=True)
                await on_subtask_update(subtask_id, "FAILED", error=str(e))
                await on_log("CRITICAL", f"Exception in #{step_order}: {e}", subtask_id=subtask_id)
                return False

parallel_worker_pool = ParallelDAGWorkerPool(max_concurrency=4)
