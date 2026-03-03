"""
Juiz de Dados — Etapa 2.
Recebe o Manifesto Híbrido da Fase 0 (ODL / Unstructured) contendo Mosaico Geométrico com as Coordenadas das tabelas e recorta as tabelas exatas.
"""
from pathlib import Path
from src.models import DocumentManifest, StageResult
from src.specialists.table_plumber import extract_tables_plumber


def judge_data(pdf_path: Path, manifest: DocumentManifest) -> StageResult:
    """
    O Juiz de Dados:
    1. Verifica se houve tabela via Radar.
    2. Envia para o pdfplumber fazer o crop nas coordenadas.
    3. Retorna a lista final de tabelas unificadas.
    """
    if not manifest.pages_with_tables:
        return StageResult(
            stage_name="Etapa 2 - Tabelas",
            tables=[],
            metadata={"skipped": True, "reason": "Nenhuma tabela detectada pelo Radar Mosaico."},
            success=True,
        )

    print("[Juiz de Dados] Extraindo Bounding Boxes das tabelas via Plumber...")

    final_tables = extract_tables_plumber(pdf_path, manifest)

    if final_tables:
        winner = f"pdfplumber ({len(final_tables)} tabelas via Crop)"
    else:
        winner = "nenhum (sem tabelas extraídas ou erro de CROP)"

    print(f"[Juiz de Dados] Vencedor: {winner}")

    return StageResult(
        stage_name="Etapa 2 - Tabelas",
        tables=final_tables,
        metadata={
            "winner": winner,
            "plumber_count": len(final_tables),
        },
        success=True,
    )
