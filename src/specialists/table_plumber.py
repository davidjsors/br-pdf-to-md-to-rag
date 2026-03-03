"""
Etapa 2 — Especialista de Tabelas Secundário: pdfplumber.
Garante precisão geométrica e matemática das coordenadas.
"""
from pathlib import Path
from src.formatter import table_to_markdown

try:
    import pdfplumber
except ImportError:
    pdfplumber = None


def extract_tables_plumber(pdf_path: Path) -> list[str]:
    """
    Usa pdfplumber para extrair tabelas com precisão de coordenadas.
    Retorna uma lista de strings Markdown, uma por tabela encontrada.
    """
    if not pdfplumber:
        return []

    tables_md = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                for table_obj in page.find_tables():
                    data = table_obj.extract()
                    md = table_to_markdown(data)
                    if md and md.strip():
                        tables_md.append(md.strip())

        print(f"[pdfplumber] Extraídas {len(tables_md)} tabelas.")
        return tables_md

    except Exception as e:
        print(f"[pdfplumber] Erro: {e}")
        return []
