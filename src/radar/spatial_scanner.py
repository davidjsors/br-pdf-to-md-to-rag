"""
Etapa 0 — Radar Espacial.

Orquestração complementar de dois motores:
- unstructured: classificação semântica de zonas (texto, tabela, imagem, título).
- pdfplumber: enriquecimento geométrico (bounding boxes, detecção nativa de tabelas/imagens).

Cada motor contribui com sua especialidade. O manifesto final combina ambas as camadas.
"""
import logging
from pathlib import Path
from src.models import DocumentManifest, PageManifest, Zone, ZoneType

logger = logging.getLogger(__name__)

try:
    from unstructured.partition.pdf import partition_pdf
    HAS_UNSTRUCTURED = True
except ImportError:
    HAS_UNSTRUCTURED = False
    logger.info("unstructured não disponível. Radar operará apenas com pdfplumber.")

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False
    logger.warning("pdfplumber não disponível. Detecção geométrica desabilitada.")


# --- Mapeamento de tipos do unstructured para ZoneType ---
_UNSTRUCTURED_TYPE_MAP = {
    "Title": ZoneType.TITLE,
    "NarrativeText": ZoneType.TEXT,
    "ListItem": ZoneType.LIST,
    "Table": ZoneType.TABLE,
    "Image": ZoneType.IMAGE,
    "Header": ZoneType.HEADER,
    "Footer": ZoneType.FOOTER,
    "FigureCaption": ZoneType.TEXT,
}


def _classify_with_unstructured(pdf_path: Path) -> dict[int, PageManifest]:
    """
    Camada Semântica: o unstructured classifica cada elemento da página por tipo.
    Ponto forte: identificação precisa de NarrativeText vs Table vs Image.
    """
    elements = partition_pdf(
        filename=str(pdf_path),
        strategy="fast",
        infer_table_structure=True,
    )

    pages: dict[int, PageManifest] = {}
    for el in elements:
        page_num = getattr(el.metadata, "page_number", 1)
        if page_num not in pages:
            pages[page_num] = PageManifest(page_number=page_num)

        zone = Zone(
            zone_type=_UNSTRUCTURED_TYPE_MAP.get(type(el).__name__, ZoneType.UNKNOWN),
            page_number=page_num,
            content=str(el),
            metadata={"source": "unstructured", "category": type(el).__name__},
        )
        pages[page_num].zones.append(zone)

    return pages


def _enrich_with_pdfplumber(pdf_path: Path, pages: dict[int, PageManifest]) -> dict[int, PageManifest]:
    """
    Camada Geométrica: o pdfplumber adiciona dados de coordenadas (bounding boxes)
    para imagens e tabelas que o unstructured pode ter classificado sem precisão espacial.
    Ponto forte: localização exata de elementos na página e detecção nativa de tabelas.
    """
    if not HAS_PDFPLUMBER:
        return pages

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_num = page.page_number
            if page_num not in pages:
                pages[page_num] = PageManifest(page_number=page_num)

            pm = pages[page_num]

            # Enriquecimento: imagens com coordenadas geométricas
            for img in page.images:
                bbox = (img["x0"], img["top"], img["x1"], img["bottom"])
                # Verifica se o unstructured já registrou uma imagem nesta página
                has_image_zone = any(
                    z.zone_type == ZoneType.IMAGE for z in pm.zones
                )
                if not has_image_zone:
                    pm.zones.append(
                        Zone(ZoneType.IMAGE, page_num, bbox=bbox, metadata={"source": "pdfplumber"})
                    )

            # Enriquecimento: tabelas nativas não detectadas pelo unstructured
            native_tables = page.find_tables()
            has_table_zone = any(z.zone_type == ZoneType.TABLE for z in pm.zones)
            if native_tables and not has_table_zone:
                for table_obj in native_tables:
                    pm.zones.append(
                        Zone(
                            ZoneType.TABLE,
                            page_num,
                            metadata={"source": "pdfplumber", "bbox": str(table_obj.bbox)},
                        )
                    )

    return pages


def _scan_pdfplumber_only(pdf_path: Path) -> dict[int, PageManifest]:
    """
    Modo degradado: quando o unstructured não está disponível,
    o pdfplumber opera sozinho com detecção geométrica básica.
    """
    if not HAS_PDFPLUMBER:
        logger.error("Nenhum motor de Radar disponível. Retornando manifesto vazio.")
        return {}

    pages: dict[int, PageManifest] = {}
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            pm = PageManifest(page_number=page.page_number)
            for img in page.images:
                pm.zones.append(
                    Zone(
                        ZoneType.IMAGE,
                        page.page_number,
                        bbox=(img["x0"], img["top"], img["x1"], img["bottom"]),
                    )
                )
            pages[page.page_number] = pm

    return pages


def scan_pdf(pdf_path: Path) -> DocumentManifest:
    """
    Ponto de entrada do Radar Espacial.

    Orquestração complementar:
    1. unstructured classifica semanticamente (tipo de cada elemento).
    2. pdfplumber enriquece com dados geométricos (bboxes de imagens/tabelas).
    3. Se unstructured falhar ou não estiver instalado, pdfplumber opera sozinho.
    """
    pages: dict[int, PageManifest] = {}

    if HAS_UNSTRUCTURED:
        try:
            logger.info("Radar: classificação semântica via unstructured...")
            pages = _classify_with_unstructured(pdf_path)
            logger.info("Radar: enriquecimento geométrico via pdfplumber...")
            pages = _enrich_with_pdfplumber(pdf_path, pages)
        except (OSError, ValueError, RuntimeError) as e:
            logger.warning("Falha no unstructured (%s). Usando pdfplumber isolado.", e)
            pages = _scan_pdfplumber_only(pdf_path)
    else:
        logger.info("Radar: operando com pdfplumber (modo geométrico)...")
        pages = _scan_pdfplumber_only(pdf_path)

    sorted_pages = sorted(pages.values(), key=lambda p: p.page_number)

    return DocumentManifest(
        pdf_path=pdf_path,
        pages=sorted_pages,
        total_pages=len(sorted_pages),
    )
