"""
Etapa 2 — Especialista de Tabelas: pdfplumber.
Garante precisão geométrica e matemática das matrizes em Markdown.
"""
from pathlib import Path
from src.formatter import table_to_markdown

try:
    import pdfplumber
except ImportError:
    pdfplumber = None


from src.models import DocumentManifest, ZoneType

def extract_tables_plumber(pdf_path: Path, manifest: DocumentManifest) -> list[str]:
    """
    Usa pdfplumber para extração nativa de tabelas de forma robusta.
    """
    if not pdfplumber:
        return []

    tables_md = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                # Extração nativa em cada página
                for table_obj in page.find_tables():
                    try:
                        data = table_obj.extract()
                        md = table_to_markdown(data)
                        if md and md.strip():
                            tables_md.append(md.strip())
                    except Exception as e:
                        print(f"[pdfplumber] Erro ao extrair tabela na pág {page.page_number}: {e}")

        print(f"[pdfplumber] Extraídas {len(tables_md)} tabelas nativas.")
        return tables_md

    except Exception as e:
        print(f"[pdfplumber] Erro global: {e}")
        return []

