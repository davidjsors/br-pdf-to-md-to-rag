from pathlib import Path
from markitdown import MarkItDown
from src.cleaner import clean_text_block

def parse_pdf_markitdown(pdf_path: Path) -> str:
    """
    Especialista: Microsoft MarkItDown.
    Excelente para reconstrução de fluxo e títulos (H1, H2).
    """
    try:
        md_engine = MarkItDown()
        result = md_engine.convert(str(pdf_path))
        
        if not result or not result.text_content:
            return "Erro: MarkItDown não extraiu conteúdo."
            
        # Aplica nossa limpeza customizada em cima do resultado estrutural
        cleaned_md = clean_text_block(result.text_content)
        return cleaned_md

    except Exception as e:
        return f"Erro no MarkItDown: {e}"
