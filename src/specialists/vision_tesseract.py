"""
Etapa 3 — Especialista de Visão Secundário: pytesseract.
Contingência rápida de OCR clássico para não estourar pipeline.
"""
from pathlib import Path

try:
    import pytesseract
    from pdf2image import convert_from_path
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False

def extract_vision_tesseract(pdf_path: Path, pages_with_images: list[int]) -> list[str]:
    """
    Extrai texto usando OCR tradicional Tesseract, filtrado apenas para
    páginas onde o Radar identificou material opaco/imagem.
    """
    if not HAS_TESSERACT:
        return []

    try:
        print("[pytesseract] Convertendo páginas selecionadas em imagens...")
        images = convert_from_path(str(pdf_path))
        results = []
        
        for i, img in enumerate(images):
            # i é 0-indexed, pages_with_images é 1-indexed
            page_num = i + 1
            if not pages_with_images or page_num in pages_with_images:
                # Usa 'por' para OCR em Português
                text = pytesseract.image_to_string(img, lang='por')
                if text.strip():
                    results.append(text.strip())
                    
        return results
    except Exception as e:
        print(f"[pytesseract] Erro de rotina OCR contingência: {e}")
        return []
