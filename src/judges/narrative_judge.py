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
    # Proteção RAG: Se houver tabelas e elas foram injetadas ao final (como é o caso atual)
    # precisamos de um header de seção para evitar "Orphan Chunks".
    if manifest.pages_with_tables:
        header_section = "\n\n## 📊 Tabelas e Matrizes de Dados Extraídas\n"
        text += str(header_section)

    for page in manifest.pages:
        table_count: int = 0
        for zone in page.zones:
            if zone.zone_type == ZoneType.TABLE:
                table_count += 1
                # Âncora limpa
                anchor = f"\n\n<!-- TABLE_ANCHOR_p{page.page_number}_t{table_count} -->\n"
                text += str(anchor)

    return text


def _extract_narrative_from_odl(manifest: DocumentManifest) -> str:
    """Reconstrói o markdown base a partir das zonas do ODL no Radar."""
    lines = []
    for page in manifest.pages:
        for zone in page.zones:
            if zone.zone_type == ZoneType.TITLE:
                lines.append(f"\n## {zone.content.strip()}\n")
            elif zone.zone_type in [ZoneType.TEXT, ZoneType.LIST]:
                lines.append(f"{zone.content.strip()}")
            elif zone.zone_type == ZoneType.TABLE:
                pass # Anchor will be injected later
    return "\n".join(lines)


def judge_narrative(pdf_path: Path, manifest: DocumentManifest) -> StageResult:
    """
    O Juiz Narrativo (Mosaico Espacial ODL):
    1. Executa MarkItDown e PyMuPDF.
    2. Lê a tradução nativa originada do OpenDataLoader no Manifesto.
    3. Compara volume e estrutura para definir a base principal.
    4. Insere âncoras de tabelas de forma assertiva.
    """
    print("[Juiz Narrativo] Acordando especialistas...")

    # Execução dos especialistas puros
    md_markitdown = extract_narrative_markitdown(pdf_path)
    md_pymupdf = extract_narrative_pymupdf(pdf_path)
    
    # Extraindo do nosso Mosaico BBox (ODL)
    md_odl = _extract_narrative_from_odl(manifest)

    len_mit = len(md_markitdown)
    len_pym = len(md_pymupdf)
    len_odl = len(md_odl)

    print(f"[Juiz Narrativo] Competidores -> MarkItDown: {len_mit} | PyMuPDF: {len_pym} | OpenDataLoader: {len_odl}")

    if len_mit == 0 and len_pym == 0 and len_odl == 0:
        return StageResult(
            stage_name="Etapa 1 - Narrativa",
            success=False,
            error="Nenhum especialista conseguiu extrair texto (documento possivelmente Raster/Zicado)."
        )

    # Escolher a base mais rica. A prioridade é:
    # 1. OpenDataLoader (Por ter coordenadas limpas, só se não falhou miseravelmente)
    # 2. MarkItDown (Estrutura superior se o ODL falhou)
    # 3. PyMuPDF (Fallback para PDF mal-formatado se MarkItDown falhar e ODL zerar)
    
    base = md_odl
    winner = "OpenDataLoader (Geometria Mosaico)"
    
    # Se ODL foi menor que 50% dos outros, PDF é confuso para parser de caixas, confia na IA de extração de linha:
    max_len = max(len_mit, len_pym)
    if len_odl < (max_len * 0.5):
         if len_pym > len_mit * 1.2:
             base = md_pymupdf
             winner = "pymupdf4llm (Fallback IA)"
         else:
             base = md_markitdown
             winner = "MarkItDown (Fallback Semântico)"

    # Inserir âncoras de tabelas para o Juiz de Dados processar depois
    final_narrative = _insert_table_anchors(base, manifest)

    return StageResult(
        stage_name="Etapa 1 - Narrativa",
        content=final_narrative,
        metadata={
            "winner": winner,
            "odl_chars": len_odl,
            "markitdown_chars": len_mit,
            "pymupdf_chars": len_pym,
            "anchors_inserted": len(manifest.pages_with_tables),
        },
        success=True,
    )

