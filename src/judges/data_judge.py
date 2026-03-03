"""
Juiz de Dados — Etapa 2.
Recebe tabelas do docling (semântica) e do pdfplumber (precisão).
Funde as melhores versões.
"""
from pathlib import Path
from src.models import DocumentManifest, StageResult
from src.specialists.table_docling import extract_tables_docling
from src.specialists.table_plumber import extract_tables_plumber


def judge_data(pdf_path: Path, manifest: DocumentManifest) -> StageResult:
    """
    O Juiz de Dados:
    1. Executa docling e pdfplumber.
    2. Compara as tabelas por qualidade.
    3. Gera a lista final de tabelas unificadas.
    """
    if not manifest.pages_with_tables:
        return StageResult(
            stage_name="Etapa 2 - Tabelas",
            tables=[],
            metadata={"skipped": True, "reason": "Nenhuma tabela detectada pelo Radar."},
            success=True,
        )

    print("[Juiz de Dados] Executando especialistas de tabelas...")

    tables_docling = extract_tables_docling(pdf_path)
    tables_plumber = extract_tables_plumber(pdf_path)

    # Heurística de fusão:
    # Usar docling se disponível (melhor semântica), senão plumber.
    # Se ambos geraram tabelas, preferir o que gerou mais (melhor cobertura).
    if len(tables_docling) >= len(tables_plumber) and tables_docling:
        final_tables = tables_docling
        winner = f"docling ({len(tables_docling)} tabelas)"
    elif tables_plumber:
        final_tables = tables_plumber
        winner = f"pdfplumber ({len(tables_plumber)} tabelas)"
    else:
        final_tables = []
        winner = "nenhum (sem tabelas extraídas)"

    print(f"[Juiz de Dados] Vencedor: {winner}")

    return StageResult(
        stage_name="Etapa 2 - Tabelas",
        tables=final_tables,
        metadata={
            "winner": winner,
            "docling_count": len(tables_docling),
            "plumber_count": len(tables_plumber),
        },
        success=True,
    )
