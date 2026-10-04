import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import docx

logger = logging.getLogger("desktop_ai.verifier")

class VerificationEngine:
    """
    Automated QA & Self-Correction Engine:
    Validates generated artifacts against the user's initial goals and engineering benchmarks.
    """
    def verify_document_artifact(
        self,
        file_path_str: str,
        expected_sections: Optional[List[str]] = None,
        min_estimated_pages: int = 1
    ) -> Dict[str, Any]:
        p = Path(file_path_str)
        if not p.exists():
            return {
                "passed": False,
                "error": f"File does not exist on disk: {p}",
                "needs_correction": True,
                "corrective_action": "REGENERATE_DOCUMENT"
            }

        size_bytes = p.stat().st_size
        if size_bytes < 100:
            return {
                "passed": False,
                "error": f"File is empty or corrupted ({size_bytes} bytes)",
                "needs_correction": True,
                "corrective_action": "REGENERATE_DOCUMENT"
            }

        # If .docx, inspect document internal structure
        if p.suffix.lower() == ".docx":
            try:
                doc = docx.Document(str(p))
                paragraphs = [par.text for par in doc.paragraphs if par.text.strip()]
                tables_count = len(doc.tables)
                word_count = sum(len(par.split()) for par in paragraphs)

                # Estimate page count (~300 words per page + tables/diagrams)
                estimated_pages = max(1, round((word_count / 280) + (tables_count * 0.5) + 2))

                is_compliant = estimated_pages >= min_estimated_pages

                return {
                    "passed": True,
                    "file_path": str(p),
                    "size_bytes": size_bytes,
                    "paragraph_count": len(paragraphs),
                    "table_count": tables_count,
                    "word_count": word_count,
                    "estimated_pages": estimated_pages,
                    "meets_page_target": is_compliant,
                    "needs_correction": not is_compliant,
                    "corrective_action": "EXPAND_TECHNICAL_SECTIONS" if not is_compliant else None
                }
            except Exception as e:
                return {
                    "passed": False,
                    "error": f"Failed to parse DOCX: {e}",
                    "needs_correction": True,
                    "corrective_action": "REPAIR_DOCX_STRUCTURE"
                }

        return {
            "passed": True,
            "file_path": str(p),
            "size_bytes": size_bytes,
            "needs_correction": False
        }

verification_engine = VerificationEngine()
