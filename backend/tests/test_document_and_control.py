import pytest
from pathlib import Path
from backend.app.core.tool_registry import tool_registry
from backend.app.core.verifier import verification_engine
from backend.app.core.execution_loop import react_execution_engine
from backend.app.db.database import init_db

@pytest.mark.asyncio
async def test_real_word_document_generation():
    await init_db()
    
    # Execute document generation
    res = await tool_registry.execute_tool(
        tool_name="create_word_document",
        parameters={
            "topic": "2-to-4 Line Decoder",
            "target_pages": 15,
            "filename": "Test_2_to_4_Decoder_Microproject.docx"
        }
    )
    assert res.status == "SUCCESS"
    assert "file_path" in res.result
    
    file_path = Path(res.result["file_path"])
    assert file_path.exists()
    assert file_path.stat().st_size > 1000

    # Verify with Verification Engine
    v_res = verification_engine.verify_document_artifact(str(file_path), min_estimated_pages=5)
    assert v_res["passed"] is True
    assert v_res["paragraph_count"] > 10
    assert v_res["table_count"] >= 2
    assert v_res["word_count"] > 500

@pytest.mark.asyncio
async def test_real_web_search():
    res = await tool_registry.execute_tool(
        tool_name="search_web",
        parameters={"query": "binary decoder logic circuit"}
    )
    assert res.status == "SUCCESS"
    assert res.result["results_count"] > 0
    assert len(res.result["sources"]) > 0

@pytest.mark.asyncio
async def test_react_execution_loop():
    await init_db()
    res = await react_execution_engine.execute_goal_loop(
        goal="Make a 15-page microproject on 2-to-4 Decoder"
    )
    assert res["status"] == "COMPLETED"
    assert len(res["tools_executed"]) > 0
    assert len(res["artifacts"]) > 0
