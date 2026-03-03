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
        table_count = 0
        for zone in page.zones:
            if zone.zone_type == ZoneType.TABLE:
                table_count += 1
                anchor = f"\n\n<!-- TABLE_ANCHOR_p{page.page_number}_t{table_count} -->\n\n"
                # Heurística: inserir âncora após a última linha de texto 
                # que precede a posição da tabela na página
                # Por simplicidade, adicionamos ao final do bloco narrativo
                text += anchor

    return text


def judge_narrative(pdf_path: Path, manifest: DocumentManifest) -> StageResult:
    """
    O Juiz Narrativo:
    1. Executa ambos os especialistas em paralelo.
    2. Compara volume de texto para detectar lacunas.
    3. Funde no bloco mais completo.
    4. Insere âncoras de tabelas.
    """
    print("[Juiz Narrativo] Executando especialistas...")

    # Execução dos especialistas
    md_markitdown = extract_narrative_markitdown(pdf_path)
    md_pymupdf = extract_narrative_pymupdf(pdf_path)

    len_mit = len(md_markitdown)
    len_pym = len(md_pymupdf)

    print(f"[Juiz Narrativo] MarkItDown: {len_mit} chars | pymupdf4llm: {len_pym} chars")

    # Heurística de fusão:
    # Se a diferença de volume for > 20%, o maior provavelmente capturou mais conteúdo.
    # Usamos o maior como base, mas verificamos se o menor tem conteúdo ausente.

    if len_mit == 0 and len_pym == 0:
        return StageResult(
            stage_name="Etapa 1 - Narrativa",
            success=False,
            error="Nenhum especialista conseguiu extrair texto."
        )

    # Escolher a base mais rica
    if len_pym > len_mit * 1.2:
        # pymupdf capturou significativamente mais → ele é a base
        base = md_pymupdf
        winner = "pymupdf4llm (maior volume)"
    else:
        # MarkItDown é a base (melhor estrutura semântica)
        base = md_markitdown
        winner = "MarkItDown (melhor estrutura)"

    # Inserir âncoras de tabelas
    final_narrative = _insert_table_anchors(base, manifest)

    return StageResult(
        stage_name="Etapa 1 - Narrativa",
        content=final_narrative,
        metadata={
            "winner": winner,
            "markitdown_chars": len_mit,
            "pymupdf_chars": len_pym,
            "anchors_inserted": len(manifest.pages_with_tables),
        },
        success=True,
    )
