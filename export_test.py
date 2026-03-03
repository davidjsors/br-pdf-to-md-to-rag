import sys
from pathlib import Path
from markitdown import MarkItDown
import pymupdf4llm
from src.orchestrator import process_pdf
from src.metrics.eval_metrics import StructuralDensityEvaluator

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

# Extrair as tags
evaluator = StructuralDensityEvaluator()
print(f"MarkItDown MDEval: {evaluator.evaluate(m_text)}%")
print(f"PyMuPDF MDEval: {evaluator.evaluate(p_text)}%")
print(f"Orchestrator MDEval: {evaluator.evaluate(res_orch.final_markdown)}%")
print("Done. Files exported: test_markitdown.md, test_pymupdf.md, test_orchestrator.md")
