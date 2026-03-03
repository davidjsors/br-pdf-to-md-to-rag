"""
Etapa 1 — Especialista Narrativo Primário: MarkItDown.
Reconstrução do fluxo narrativo e identificação de cabeçalhos.
"""
from pathlib import Path
from src.cleaner import clean_text_block

try:
    from markitdown import MarkItDown
    HAS_MARKITDOWN = True
except ImportError:
    HAS_MARKITDOWN = False


def extract_narrative_markitdown(pdf_path: Path) -> str:
    """Extrai o fluxo narrativo completo usando MarkItDown."""
    if not HAS_MARKITDOWN:
        return ""

    try:
        engine = MarkItDown()
        result = engine.convert(str(pdf_path))
        if result and result.text_content:
            return clean_text_block(result.text_content)
        return ""
    except Exception as e:
        print(f"[MarkItDown] Erro: {e}")
        return ""
