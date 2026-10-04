import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy import select, or_
from backend.app.schemas.common import MemoryTier
from backend.app.db.database import AsyncSessionLocal
from backend.app.db.models import Memory

logger = logging.getLogger("desktop_ai.memory")

class MemoryManager:
    def __init__(self):
        # In-memory working buffer for fast short-term context
        self._short_term_buffer: Dict[str, List[Dict[str, Any]]] = {}

    async def store(
        self,
        tier: MemoryTier,
        key: str,
        content: str,
        context_type: str = "GENERAL",
        task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store a memory entry in SQLite and working buffer."""
        meta_json = json.dumps(metadata or {})
        now = datetime.now(timezone.utc)

        # Update fast in-memory buffer if short term
        if tier == MemoryTier.SHORT_TERM:
            buffer_key = task_id or "global"
            if buffer_key not in self._short_term_buffer:
                self._short_term_buffer[buffer_key] = []
            self._short_term_buffer[buffer_key].append({
                "key": key,
                "content": content,
                "timestamp": now.isoformat()
            })
            # Keep buffer bounded
            if len(self._short_term_buffer[buffer_key]) > 50:
                self._short_term_buffer[buffer_key].pop(0)

        # Persist to database
        async with AsyncSessionLocal() as session:
            # Check if key exists in this tier/task
            query = select(Memory).where(
                Memory.tier == tier.value,
                Memory.key == key,
                Memory.task_id == task_id
            )
            result = await session.execute(query)
            existing = result.scalar_one_or_none()

            if existing:
                existing.content = content
                existing.context_type = context_type
                existing.metadata_json = meta_json
                existing.access_count += 1
                existing.last_accessed_at = now
                await session.commit()
                return existing.id
            else:
                entry = Memory(
                    tier=tier.value,
                    key=key,
                    content=content,
                    context_type=context_type,
                    task_id=task_id,
                    metadata_json=meta_json,
                    access_count=1,
                    last_accessed_at=now,
                    created_at=now
                )
                session.add(entry)
                await session.commit()
                await session.refresh(entry)
                return entry.id

    async def retrieve(
        self,
        query: str,
        tier: Optional[MemoryTier] = None,
        task_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Retrieve memories matching criteria or keyword."""
        async with AsyncSessionLocal() as session:
            stmt = select(Memory)
            filters = []
            if tier:
                filters.append(Memory.tier == tier.value)
            if task_id:
                filters.append(or_(Memory.task_id == task_id, Memory.task_id.is_(None)))
            if query:
                filters.append(or_(
                    Memory.key.ilike(f"%{query}%"),
                    Memory.content.ilike(f"%{query}%")
                ))

            if filters:
                stmt = stmt.where(*filters)

            stmt = stmt.order_by(Memory.last_accessed_at.desc()).limit(limit)
            result = await session.execute(stmt)
            memories = result.scalars().all()

            results = []
            for m in memories:
                # Increment access count
                m.access_count += 1
                m.last_accessed_at = datetime.now(timezone.utc)
                results.append({
                    "id": m.id,
                    "tier": m.tier,
                    "key": m.key,
                    "content": m.content,
                    "context_type": m.context_type,
                    "task_id": m.task_id,
                    "metadata": json.loads(m.metadata_json or "{}"),
                    "access_count": m.access_count,
                    "last_accessed_at": m.last_accessed_at.isoformat()
                })
            await session.commit()
            return results

    async def get_context_for_prompt(self, current_goal: str, task_id: Optional[str] = None) -> str:
        """Assemble relevant short-term, task, and long-term memory for the AI Brain."""
        relevant_memories = await self.retrieve(query=current_goal[:30], task_id=task_id, limit=5)
        if not relevant_memories:
            return ""

        context_lines = ["Relevant Context & Past Memory:"]
        for mem in relevant_memories:
            context_lines.append(f"- [{mem['tier']}] {mem['key']}: {mem['content']}")
        return "\n".join(context_lines)

memory_manager = MemoryManager()
