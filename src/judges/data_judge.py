"""
Juiz de Dados — Etapa 2.
Recebe o Manifesto da Fase 0 e usa pdfplumber para extração rigorosa de matrizes.
"""
from pathlib import Path
from src.models import DocumentManifest, StageResult
from src.specialists.table_plumber import extract_tables_plumber


def judge_data(pdf_path: Path, manifest: DocumentManifest) -> StageResult:
    """
    O Juiz de Dados:
    1. Aciona o pdfplumber para extrair tabelas das páginas sinalizadas.
    2. Retorna a lista final de tabelas unificadas.
    """
    print("[Juiz de Dados] Extraindo tabelas via Plumber...")

    final_tables = extract_tables_plumber(pdf_path, manifest)

    if final_tables:
        winner = f"pdfplumber ({len(final_tables)} tabelas)"
    else:
        winner = "nenhum (sem tabelas detectadas)"

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

