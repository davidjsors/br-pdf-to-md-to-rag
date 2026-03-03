import sys
from pathlib import Path
from markitdown import MarkItDown
import pymupdf4llm
from src.orchestrator import process_pdf

pdf_path = Path("tests/corpus/Convocacao_entrevista_banca_heteroidentificacao_IA_aplicada_Dados_Corporativos.pdf")

# 1. MarkItDown Pure
try:
    md = MarkItDown()
    res = md.convert(str(pdf_path))
    m_text = res.text_content
except Exception as e:
    m_text = f"Failed: {e}"
with open("test_markitdown.md", "w") as f:
    f.write(m_text)

# 2. PyMuPDF Pure
try:
    p_text = pymupdf4llm.to_markdown(str(pdf_path))
except Exception as e:
    p_text = f"Failed: {e}"
with open("test_pymupdf.md", "w") as f:
    f.write(p_text)

# 3. Orquestrador V2 (Cleaner + Judges + Ensemble)
res_orch = process_pdf(pdf_path)
with open("test_orchestrator.md", "w") as f:
    f.write(res_orch.final_markdown)

print("Exported markdowns for reference.")
