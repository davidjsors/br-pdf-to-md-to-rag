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


from src.models import DocumentManifest, ZoneType

def extract_tables_plumber(pdf_path: Path, manifest: DocumentManifest) -> list[str]:
    """
    Usa pdfplumber para extrair tabelas com base cirúrgica nas coordenadas BBox do Mosaico (ODL).
    Retorna uma lista de strings Markdown.
    """
    if not pdfplumber:
        return []

    tables_md = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_manifest in manifest.pages:
                # Índice de PDFPlumber é zero-based, manifest.page_number é 1-based
                if page_manifest.page_number < 1 or page_manifest.page_number > len(pdf.pages):
                     continue
                     
                pdf_page = pdf.pages[page_manifest.page_number - 1]
                
                table_zones = [z for z in page_manifest.zones if z.zone_type == ZoneType.TABLE]
                
                for zone in table_zones:
                    if zone.bbox:
                        try:
                            # ODL devolve (x0, y0, x1, y1), equivalente p/ crop
                            cropped_page = pdf_page.within_bbox(zone.bbox)
                            extracted = cropped_page.extract_tables()
                            # `extract_tables` numa bounding box limitada, geralmente traz 1 tabela
                            for tab_data in extracted:
                                md = table_to_markdown(tab_data)
                                if md and md.strip():
                                    tables_md.append(md.strip())
                        except Exception as crop_err:
                            print(f"[pdfplumber] Erro no crop via Mosaico: {crop_err}")
                            # Fallback nativo
                            _extract_native_tables(pdf_page, tables_md)
                    else:
                        # Tabelas sem bbox (descobertas pelo pipeline puro)
                        _extract_native_tables(pdf_page, tables_md)

        print(f"[pdfplumber] Extraídas {len(tables_md)} tabelas BBox direcionadas.")
        return tables_md

    except Exception as e:
        print(f"[pdfplumber] Erro global: {e}")
        return []

def _extract_native_tables(pdf_page, tables_md: list[str]):
    for table_obj in pdf_page.find_tables():
         data = table_obj.extract()
         md = table_to_markdown(data)
         if md and md.strip():
             tables_md.append(md.strip())
