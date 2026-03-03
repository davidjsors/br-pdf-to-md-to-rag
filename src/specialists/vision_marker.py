"""
Etapa 3 — Especialista de Visão Primário: marker-pdf.
Converte layouts complexos através de pipelines de modelos de IA.
"""
from pathlib import Path

try:
    from marker.convert import convert_single_pdf
    from marker.models import load_all_models
    HAS_MARKER = True
except ImportError:
    HAS_MARKER = False

# Singleton para evitar carregar o modelo múltiplas vezes e estourar a memória
_MODEL_CACHE = None

def extract_vision_marker(pdf_path: Path) -> str:
    """
    Extrai o PDF usando o pipeline do marker-pdf (Inteligência Artificial).
    Operação de alta carga computacional.
    """
    global _MODEL_CACHE
    if not HAS_MARKER:
        return ""

    try:
        print("[marker-pdf] Carregando modelos de IA (isso pode demorar na 1ª vez)...")
        if _MODEL_CACHE is None:
            # Em prod, ideal carregar sob demanda apenas as models necessarias
            _MODEL_CACHE = load_all_models()
        
        full_text, _, out_meta = convert_single_pdf(str(pdf_path), _MODEL_CACHE)
        return full_text if full_text else ""
    except Exception as e:
        print(f"[marker-pdf] Erro crítico na extração de IA: {e}")
        return ""
