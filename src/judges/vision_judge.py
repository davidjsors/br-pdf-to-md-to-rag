"""
Juiz de Visão — Etapa 3.
Avalia complexidade visual e aciona marker-pdf (IA) ou pytesseract (OCR rápido).
"""
from pathlib import Path
from src.models import DocumentManifest, StageResult
from src.specialists.vision_marker import extract_vision_marker
from src.specialists.vision_tesseract import extract_vision_tesseract

def judge_vision(pdf_path: Path, manifest: DocumentManifest) -> StageResult:
    """
    O Juiz de Visão atua ativamente como um Guardião de Carga (Load Guard).
    """
    
    # 1. Pulo Inteligente (Bypass)
    if not manifest.pages_with_images:
        print("[Juiz de Visão] Radar não detectou zonas gráficas. Pulando extração de visão.")
        return StageResult(
            stage_name="Etapa 3 - Visão",
            visuals=[],
            metadata={"skipped": True, "reason": "Página não demandou OCR/Visão"},
            success=True
        )

    print(f"[Juiz de Visão] Tratando zonas não-textuais nativas...")

    # Tenta usar a inteligência robusta primeiro
    # Observação: em um cenário real complexo, poderíamos passar um threshold de tempo
    marker_result = extract_vision_marker(pdf_path)

    if marker_result and marker_result.strip():
        return StageResult(
            stage_name="Etapa 3 - Visão",
            visuals=[marker_result],  # marker já entrega consolidado
            metadata={"winner": "marker-pdf (deep learning)"},
            success=True
        )

    # Contingência Rápida: MarkerFalhou ou Não Instalado
    print("[Juiz de Visão] Acionando plano B: OCR via Tesseract")
    tess_results = extract_vision_tesseract(pdf_path, manifest.pages_with_images)
    
    return StageResult(
        stage_name="Etapa 3 - Visão",
        visuals=tess_results,
        metadata={"winner": "pytesseract (fallback)"},
        success=True
    )
