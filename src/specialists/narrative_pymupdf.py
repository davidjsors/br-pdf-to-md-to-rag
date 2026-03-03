"""
Etapa 1 — Especialista Narrativo Secundário: pymupdf4llm.
Scanner de velocidade para garantir volume total de texto.
"""
from pathlib import Path
from src.cleaner import clean_text_block

try:
    import pymupdf4llm
    HAS_PYMUPDF4LLM = True
except ImportError:
    HAS_PYMUPDF4LLM = False


def extract_narrative_pymupdf(pdf_path: Path) -> str:
    """Extrai todo o texto do PDF usando pymupdf4llm."""
    if not HAS_PYMUPDF4LLM:
        return ""

    try:
        raw_md = pymupdf4llm.to_markdown(str(pdf_path))
        if raw_md:
            return clean_text_block(raw_md)
        return ""
    except Exception as e:
        print(f"[pymupdf4llm] Erro: {e}")
        return ""
