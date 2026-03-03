"""
Etapa 2 — Especialista de Tabelas Primário: docling (IBM).
Analisa semântica de matrizes complexas e identifica células mescladas.
"""
from pathlib import Path

try:
    from docling.document_converter import DocumentConverter
    HAS_DOCLING = True
except ImportError:
    HAS_DOCLING = False


def extract_tables_docling(pdf_path: Path) -> list[str]:
    """
    Usa o docling para extrair tabelas com compreensão semântica.
    Retorna uma lista de strings Markdown, uma por tabela encontrada.
    """
    if not HAS_DOCLING:
        return []

    try:
        converter = DocumentConverter()
        result = converter.convert(str(pdf_path))
        doc = result.document

        tables_md = []
        for table in doc.tables:
            md_table = table.export_to_markdown()
            if md_table and md_table.strip():
                tables_md.append(md_table.strip())

        print(f"[docling] Extraídas {len(tables_md)} tabelas.")
        return tables_md

    except Exception as e:
        print(f"[docling] Erro: {e}")
        return []
