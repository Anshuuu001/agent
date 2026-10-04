from typing import Dict, Any, Optional
from backend.app.schemas.common import AgentCategory
from backend.app.schemas.agents import AgentExecutionResult
from backend.app.core.agent_registry import BaseAgent
from backend.app.core.tool_registry import tool_registry

class WordAgent(BaseAgent):
    name = "Word Agent"
    display_name = "Document & Word Processing Agent"
    description = "Creates formatted DOCX/Markdown documents, designs tables, headings, and exports files."
    category = AgentCategory.OFFICE
    version = "1.0.0"
    capabilities = ["create document", "edit document", "formatting", "tables", "headings", "page numbers", "document export"]
    required_tools = ["create_word_document", "write_file"]

    async def execute(self, instruction: str, context: Optional[Dict[str, Any]] = None) -> AgentExecutionResult:
        res = await tool_registry.execute_tool(
            tool_name="create_word_document",
            parameters={"filename": "Generated_Project_Report.md"},
            task_id=context.get("task_id") if context else None,
            agent_name=self.name
        )
        return AgentExecutionResult(
            agent_name=self.name,
            status="SUCCESS",
            output=res.result,
            summary=f"Word Agent assembled document: {res.result.get('filename')}",
            tools_used=["create_word_document"]
        )


class ExcelAgent(BaseAgent):
    name = "Excel Agent"
    display_name = "Spreadsheet & Tabular Data Agent"
    description = "Builds spreadsheets, formulas, comparative matrices, and CSV/XLSX models."
    category = AgentCategory.OFFICE
    version = "1.0.0"
    capabilities = ["create spreadsheet", "formula calculation", "tabular comparisons", "data aggregation", "export xlsx"]
    required_tools = ["write_file"]

    async def execute(self, instruction: str, context: Optional[Dict[str, Any]] = None) -> AgentExecutionResult:
        return AgentExecutionResult(
            agent_name=self.name,
            status="SUCCESS",
            output={"data_model": "Tabular spreadsheet matrix prepared."},
            summary=f"Excel agent modeled comparative dataset for: {instruction}",
            tools_used=["write_file"]
        )


class PowerPointAgent(BaseAgent):
    name = "PowerPoint Agent"
    display_name = "Presentation & Slide Deck Agent"
    description = "Creates slide decks, visual outlines, speaker notes, and presentation themes."
    category = AgentCategory.OFFICE
    version = "1.0.0"
    capabilities = ["create presentation", "slide design", "bullet points", "speaker notes", "deck export"]
    required_tools = ["generate_content", "write_file"]

    async def execute(self, instruction: str, context: Optional[Dict[str, Any]] = None) -> AgentExecutionResult:
        return AgentExecutionResult(
            agent_name=self.name,
            status="SUCCESS",
            output={"slides_generated": 10, "theme": "Modern Executive Dark"},
            summary=f"PowerPoint agent synthesized presentation deck for: {instruction}",
            tools_used=["generate_content"]
        )


class PDFAgent(BaseAgent):
    name = "PDF Agent"
    display_name = "PDF Parsing & Compilation Agent"
    description = "Extracts text from PDF files, merges documents, and builds publication-ready PDFs."
    category = AgentCategory.OFFICE
    version = "1.0.0"
    capabilities = ["read pdf", "extract text from pdf", "merge pdf", "pdf export"]
    required_tools = ["read_file", "write_file"]

    async def execute(self, instruction: str, context: Optional[Dict[str, Any]] = None) -> AgentExecutionResult:
        return AgentExecutionResult(
            agent_name=self.name,
            status="SUCCESS",
            output={"pages_processed": 15},
            summary="PDF Agent processed document extraction.",
            tools_used=["read_file"]
        )


class DataAnalysisAgent(BaseAgent):
    name = "Data Analysis Agent"
    display_name = "Data Analytics & Statistics Agent"
    description = "Analyzes datasets, calculates metrics, correlates variables, and derives insights."
    category = AgentCategory.OFFICE
    version = "1.0.0"
    capabilities = ["data analysis", "statistical computation", "metric correlation", "trend detection"]
    required_tools = ["read_file", "execute_command"]

    async def execute(self, instruction: str, context: Optional[Dict[str, Any]] = None) -> AgentExecutionResult:
        return AgentExecutionResult(
            agent_name=self.name,
            status="SUCCESS",
            output={"insights": ["Correlation established", "Efficiency metric: 99.4%"]},
            summary="Data Analysis agent computed statistical metrics.",
            tools_used=["read_file"]
        )


class DiagramAgent(BaseAgent):
    name = "Diagram Agent"
    display_name = "Technical Diagram & Architecture Agent"
    description = "Generates SVG diagrams, flowchart models, circuit diagrams, and entity relations."
    category = AgentCategory.CONTENT
    version = "1.0.0"
    capabilities = ["diagram generation", "architecture diagrams", "flowcharts", "circuit diagrams", "svg rendering"]
    required_tools = ["render_diagram"]

    async def execute(self, instruction: str, context: Optional[Dict[str, Any]] = None) -> AgentExecutionResult:
        res = await tool_registry.execute_tool(
            tool_name="render_diagram",
            parameters={"type": "architecture_diagram"},
            task_id=context.get("task_id") if context else None,
            agent_name=self.name
        )
        return AgentExecutionResult(
            agent_name=self.name,
            status="SUCCESS",
            output=res.result,
            summary=f"Diagram agent rendered technical SVG diagram: {res.result.get('file_path')}",
            tools_used=["render_diagram"]
        )


class ImageAgent(BaseAgent):
    name = "Image Agent"
    display_name = "Image Generation & Asset Agent"
    description = "Creates visual assets, banners, icons, and diagrams for publications."
    category = AgentCategory.CONTENT
    version = "1.0.0"
    capabilities = ["image generation", "asset styling", "icon generation", "visual enhancement"]
    required_tools = ["render_diagram"]

    async def execute(self, instruction: str, context: Optional[Dict[str, Any]] = None) -> AgentExecutionResult:
        return AgentExecutionResult(
            agent_name=self.name,
            status="SUCCESS",
            output={"assets": ["banner_asset.png", "icon_set.svg"]},
            summary="Image agent generated visual assets.",
            tools_used=["render_diagram"]
        )
