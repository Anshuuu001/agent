import pytest
from sqlalchemy import select
from backend.app.db.database import init_db, AsyncSessionLocal
from backend.app.db.models import User, Agent, Tool, Project, Memory
from backend.app.schemas.common import MemoryTier

@pytest.mark.asyncio
async def test_database_tables_and_models():
    await init_db()

    async with AsyncSessionLocal() as session:
        # Create test user
        user = User(username="admin_test", role="owner")
        session.add(user)

        # Create test memory
        mem = Memory(
            tier=MemoryTier.LONG_TERM.value,
            key="user_name",
            content="Alex",
            context_type="PROFILE"
        )
        session.add(mem)
        await session.commit()

        # Query back
        res = await session.execute(select(User).where(User.username == "admin_test"))
        fetched_user = res.scalar_one_or_none()
        assert fetched_user is not None
        assert fetched_user.role == "owner"

        mem_res = await session.execute(select(Memory).where(Memory.key == "user_name"))
        fetched_mem = mem_res.scalar_one_or_none()
        assert fetched_mem is not None
        assert fetched_mem.content == "Alex"
