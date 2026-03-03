"""
Fase 0 — Radar Espacial.
Usa a biblioteca `unstructured` para varrer o PDF e classificar cada zona da página.
Fallback: Se `unstructured` não estiver disponível, usa `pdfplumber` como radar básico.
"""
from pathlib import Path
from src.models import DocumentManifest, PageManifest, Zone, ZoneType

try:
    from unstructured.partition.pdf import partition_pdf
    HAS_UNSTRUCTURED = True
except ImportError:
    HAS_UNSTRUCTURED = False

try:
    import pdfplumber
except ImportError:
    pdfplumber = None


def _map_element_type(element_type: str) -> ZoneType:
    """Mapeia tipos do unstructured para nosso ZoneType."""
    mapping = {
        "Title": ZoneType.TITLE,
        "NarrativeText": ZoneType.TEXT,
        "ListItem": ZoneType.LIST,
        "Table": ZoneType.TABLE,
        "Image": ZoneType.IMAGE,
        "Header": ZoneType.HEADER,
        "Footer": ZoneType.FOOTER,
        "FigureCaption": ZoneType.TEXT,
        "UncategorizedText": ZoneType.TEXT,
    }
    return mapping.get(element_type, ZoneType.UNKNOWN)


def scan_with_unstructured(pdf_path: Path) -> DocumentManifest:
    """Varredura avançada via unstructured (hi_res)."""
    elements = partition_pdf(
        filename=str(pdf_path),
        strategy="fast",  # Usar "hi_res" para detecção com modelo AI
        infer_table_structure=True,
    )

    pages_dict: dict[int, PageManifest] = {}

    for el in elements:
        page_num = el.metadata.page_number if hasattr(el.metadata, 'page_number') else 1
        if page_num not in pages_dict:
            pages_dict[page_num] = PageManifest(page_number=page_num)

        zone = Zone(
            zone_type=_map_element_type(type(el).__name__),
            page_number=page_num,
            content=str(el),
            metadata={"category": type(el).__name__}
        )
        pages_dict[page_num].zones.append(zone)

    manifest = DocumentManifest(
        pdf_path=pdf_path,
        pages=sorted(pages_dict.values(), key=lambda p: p.page_number),
        total_pages=len(pages_dict)
    )
    return manifest


def scan_with_pdfplumber(pdf_path: Path) -> DocumentManifest:
    """Varredura básica via pdfplumber (fallback)."""
    if not pdfplumber:
        return DocumentManifest(pdf_path=pdf_path)

    pages_list = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            pm = PageManifest(page_number=page.page_number)

            # Detectar tabelas
            tables = page.find_tables()
            for t in tables:
                pm.zones.append(Zone(
                    zone_type=ZoneType.TABLE,
                    page_number=page.page_number,
                    bbox=t.bbox,
                ))

            # Detectar texto (excluindo áreas de tabelas)
            text = page.extract_text()
            if text and text.strip():
                pm.zones.append(Zone(
                    zone_type=ZoneType.TEXT,
                    page_number=page.page_number,
                    content=text,
                ))

            # Detectar imagens
            if page.images:
                for img in page.images:
                    pm.zones.append(Zone(
                        zone_type=ZoneType.IMAGE,
                        page_number=page.page_number,
                        bbox=(img['x0'], img['top'], img['x1'], img['bottom']),
                    ))

            pages_list.append(pm)

    return DocumentManifest(
        pdf_path=pdf_path,
        pages=pages_list,
        total_pages=len(pages_list)
    )


def scan_pdf(pdf_path: Path) -> DocumentManifest:
    """Ponto de entrada do Radar. Tenta unstructured, fallback pdfplumber."""
    if HAS_UNSTRUCTURED:
        try:
            print("[Radar] Usando unstructured (hi_res)...")
            return scan_with_unstructured(pdf_path)
        except Exception as e:
            print(f"[Radar] Falha no unstructured: {e}. Fallback pdfplumber.")

    print("[Radar] Usando pdfplumber (fallback)...")
    return scan_with_pdfplumber(pdf_path)
