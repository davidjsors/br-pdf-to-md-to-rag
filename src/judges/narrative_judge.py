"""
Juiz Narrativo — Etapa 1.
Cruza o esqueleto semântico do MarkItDown com o volume do pymupdf4llm.
Insere âncoras posicionais onde o Radar detectou tabelas.
"""
import re
from pathlib import Path
from src.models import DocumentManifest, StageResult, ZoneType
from src.specialists.narrative_markitdown import extract_narrative_markitdown
from src.specialists.narrative_pymupdf import extract_narrative_pymupdf
from src.metrics.eval_metrics import StructuralDensityEvaluator


def _insert_table_anchors(text: str, manifest: DocumentManifest) -> str:
    """
    Insere âncoras <!-- TABLE_ANCHOR_pX_tY --> no fluxo narrativo
    nas posições onde o Radar detectou tabelas.
    """
    for page in manifest.pages:
        table_count: int = 0
        for zone in page.zones:
            if zone.zone_type == ZoneType.TABLE:
                table_count += 1
                anchor = f"\n\n<!-- TABLE_ANCHOR_p{page.page_number}_t{table_count} -->\n"
                text += str(anchor)

    return text


def judge_narrative(pdf_path: Path, manifest: DocumentManifest) -> StageResult:
    """
    O Juiz Narrativo (Stack Lite - Otimizada por Saúde):
    1. Executa MarkItDown e PyMuPDF.
    2. Avalia a saúde estrutural (MDEval) de ambos os outputs.
    3. Escolhe o vencedor por Saúde (e não apenas Volume).
    """
    print("[Juiz Narrativo] Acordando especialistas...")

    # Instancia avaliador de saúde
    evaluator = StructuralDensityEvaluator()

    # Execução dos especialistas puros
    md_markitdown = extract_narrative_markitdown(pdf_path)
    md_pymupdf = extract_narrative_pymupdf(pdf_path)
    
    # Avaliação de Saúde em tempo real
    score_mit = evaluator.evaluate(md_markitdown)
    score_pym = evaluator.evaluate(md_pymupdf)

    print(f"[Juiz Narrativo] Competidores -> MarkItDown (Saúde: {score_mit}%) | PyMuPDF (Saúde: {score_pym}%)")

    if len(md_markitdown) == 0 and len(md_pymupdf) == 0:
        return StageResult(
            stage_name="Etapa 1 - Narrativa",
            success=False,
            error="Nenhum especialista conseguiu extrair texto."
        )

    # Decisão BASEADA EM SAÚDE MDE
    # O motor com melhor estrutura ganha a base do documento
    if score_pym > score_mit:
        base = md_pymupdf
        winner = f"pymupdf4llm (Saúde Superior: {score_pym}%)"
    else:
        base = md_markitdown
        winner = f"MarkItDown (Saúde Superior: {score_mit}%)"

    # Caso ambos tenham saúde zerada, desempata pro PyMuPDF se houver volume
    if score_pym == 0 and score_mit == 0:
        if len(md_pymupdf) > len(md_markitdown):
            base = md_pymupdf
            winner = "pymupdf4llm (Desempate por Volume)"

    # Inserir âncoras de tabelas para o Juiz de Dados processar depois
    final_narrative = _insert_table_anchors(base, manifest)

    return StageResult(
        stage_name="Etapa 1 - Narrativa",
        content=final_narrative,
        metadata={
            "winner": winner,
            "filename": pdf_path.name,
            "markitdown_chars": len(md_markitdown),
            "pymupdf_chars": len(md_pymupdf),
            "score_mit": score_mit,
            "score_pym": score_pym
        },
        success=True,
    )


