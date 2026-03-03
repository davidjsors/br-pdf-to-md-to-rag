"""
Fase 0 — Radar Espacial (LITE).
Usa Unstructured para classificação primária e pdfplumber como fallback geométrico.
"""
import tempfile
from pathlib import Path
from src.models import DocumentManifest, PageManifest, Zone, ZoneType

try:
    from unstructured.partition.pdf import partition_pdf
    HAS_UNSTRUCTURED = True
except ImportError:
    HAS_UNSTRUCTURED = False

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False


def _map_unstructured_type(element_type: str) -> ZoneType:
    mapping = {
        "Title": ZoneType.TITLE,
        "NarrativeText": ZoneType.TEXT,
        "ListItem": ZoneType.LIST,
        "Table": ZoneType.TABLE,
        "Image": ZoneType.IMAGE,
        "Header": ZoneType.HEADER,
        "Footer": ZoneType.FOOTER,
        "FigureCaption": ZoneType.TEXT,
    }
    return mapping.get(element_type, ZoneType.UNKNOWN)

def scan_with_unstructured(pdf_path: Path) -> DocumentManifest:
    """Varredura via unstructured (AI Radar Principal)."""
    elements = partition_pdf(
        filename=str(pdf_path),
        strategy="fast",
        infer_table_structure=True,
    )

    pages_dict: dict[int, PageManifest] = {}

    for el in elements:
        page_num = getattr(el.metadata, 'page_number', 1)
        if page_num not in pages_dict:
            pages_dict[page_num] = PageManifest(page_number=page_num)

        zone = Zone(
            zone_type=_map_unstructured_type(type(el).__name__),
            page_number=page_num,
            content=str(el),
            metadata={"source": "unstructured", "category": type(el).__name__}
        )
        pages_dict[page_num].zones.append(zone)

    manifest = DocumentManifest(
        pdf_path=pdf_path,
        pages=sorted(pages_dict.values(), key=lambda p: p.page_number),
        total_pages=len(pages_dict)
    )
    return manifest


def scan_with_pdfplumber(pdf_path: Path) -> DocumentManifest:
    """Varredura via pdfplumber (Fallback Geométrico)."""
    if not HAS_PDFPLUMBER:
        return DocumentManifest(pdf_path=pdf_path)

    pages_list = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            pm = PageManifest(page_number=page.page_number)
            # Imagens e tabelas nativas
            for img in page.images:
                 pm.zones.append(Zone(ZoneType.IMAGE, page.page_number, bbox=(img['x0'], img['top'], img['x1'], img['bottom'])))
            pages_list.append(pm)
            
    return DocumentManifest(pdf_path=pdf_path, pages=pages_list, total_pages=len(pages_list))


def scan_pdf(pdf_path: Path) -> DocumentManifest:
    """
    Ponto de entrada do Radar.
    Tenta Unstructured. Se falhar, pdfplumber.
    """
    if HAS_UNSTRUCTURED:
        try:
            print("[Radar] Usando Unstructured (AI Radar)...")
            return scan_with_unstructured(pdf_path)
        except Exception as e:
            print(f"[Radar] Falha no unstructured: {e}. Fallback pdfplumber.")

    print("[Radar] Usando pdfplumber (Fallback Geométrico)...")
    return scan_with_pdfplumber(pdf_path)

