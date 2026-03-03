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
    O Juiz Narrativo (Stack Lite):
    1. Executa MarkItDown e PyMuPDF.
    2. Compara volume e estrutura para definir a base principal.
    3. Insere âncoras de tabelas para o próximo estágio.
    """
    print("[Juiz Narrativo] Acordando especialistas...")

    # Execução dos especialistas puros
    md_markitdown = extract_narrative_markitdown(pdf_path)
    md_pymupdf = extract_narrative_pymupdf(pdf_path)
    
    len_mit = len(md_markitdown)
    len_pym = len(md_pymupdf)

    print(f"[Juiz Narrativo] Competidores -> MarkItDown: {len_mit} | PyMuPDF: {len_pym}")

    if len_mit == 0 and len_pym == 0:
        return StageResult(
            stage_name="Etapa 1 - Narrativa",
            success=False,
            error="Nenhum especialista conseguiu extrair texto."
        )

    # Decisão Bimodal
    if len_pym > len_mit * 1.5:
        base = md_pymupdf
        winner = "pymupdf4llm (Maior Volume)"
    else:
        base = md_markitdown
        winner = "MarkItDown (Estrutura Semântica)"

    # Inserir âncoras de tabelas para o Juiz de Dados processar depois
    final_narrative = _insert_table_anchors(base, manifest)

    return StageResult(
        stage_name="Etapa 1 - Narrativa",
        content=final_narrative,
        metadata={
            "winner": winner,
            "markitdown_chars": len_mit,
            "pymupdf_chars": len_pym,
        },
        success=True,
    )


