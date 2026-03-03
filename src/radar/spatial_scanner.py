"""
Fase 0 — Radar Espacial (HÍBRIDO - Mosaico Espacial).
Integra a exatidão geométrica do OpenDataLoader-PDF (Bounding Boxes) e a classificação raster do Unstructured.
Fallback: Se o ambiente não der suporte, recai para pdfplumber.
"""
import tempfile
import json
from pathlib import Path
from src.models import DocumentManifest, PageManifest, Zone, ZoneType
from src.radar.json_to_md_parser import OpenDataLoaderParser

try:
    import opendataloader_pdf
    HAS_ODL = True
except ImportError:
    HAS_ODL = False

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


def _map_odl_type(node_type: str) -> ZoneType:
    """Mapeia os nós do ODL para os tipos do nosso manifesto de zonas."""
    mapping = {
        "heading": ZoneType.TITLE,
        "paragraph": ZoneType.TEXT,
        "raw_text": ZoneType.TEXT,
        "list": ZoneType.LIST,
        "table_anchor": ZoneType.TABLE,
        "image_anchor": ZoneType.IMAGE,
        "scanned_image_page": ZoneType.IMAGE
    }
    return mapping.get(node_type, ZoneType.UNKNOWN)


def scan_with_odl(pdf_path: Path) -> DocumentManifest:
    """
    Rastreio primário: Dispara o Java/OpenDataLoader para buscar Coordenadas Precisas.
    Converte a árvore ODL JSON em objetos Zone do Comitê.
    """
    with tempfile.TemporaryDirectory() as td:
        opendataloader_pdf.convert(
            input_path=str(pdf_path),
            output_dir=td,
            format="json",
            quiet=True
        )
        base_name = pdf_path.stem
        out_file = Path(td) / f"{base_name}.json"
        
        if not out_file.exists():
            raise FileNotFoundError(f"OpenDataLoader não gerou o JSON esperado em {out_file}")
            
        with open(out_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        # Percorre usando nosso Parser construído
        parser = OpenDataLoaderParser()
        parser.parse_odl_json(data)
        
        # O parser achata (flatten) todos os nós sequencialmente sem hierarquia de paginas, 
        # mas nós no parser nao inserimos a página neles. Vamos simplificar criando os Manifests.
        # (Idealmente atualizar parser depois pra carregar página). Por enquanto,
        # ODL devolve paginas nos elements base.
        
        manifest = DocumentManifest(pdf_path=pdf_path)
        
        # Vamos re-processar pegando pages direto daqui para separar os Manifests
        for idx, page_node in enumerate(data.get("kids", [])):
            page_num = idx + 1
            pm = PageManifest(page_number=page_num)
            
            # Aproveitamos a lógica isolada do parser pra só essa página
            page_parser = OpenDataLoaderParser()
            page_parser._traverse_page(page_node)
            
            for node in page_parser.nodes:
                zone = Zone(
                    zone_type=_map_odl_type(node.type),
                    page_number=page_num,
                    content=node.text,
                    bbox=tuple(node.bbox) if node.bbox else None,
                    metadata={"source": "odl", "node_id": node.id}
                )
                pm.zones.append(zone)
                
            manifest.pages.append(pm)
            
        manifest.total_pages = len(manifest.pages)
        return manifest


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
    """Varredura via unstructured (Fallback / Scan fallback)."""
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
    """Varredura sub-básica via pdfplumber (fallback total)."""
    if not HAS_PDFPLUMBER:
        return DocumentManifest(pdf_path=pdf_path)

    pages_list = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            pm = PageManifest(page_number=page.page_number)
            # Imagens
            for img in page.images:
                 pm.zones.append(Zone(ZoneType.IMAGE, page.page_number, bbox=(img['x0'], img['top'], img['x1'], img['bottom'])))
            pages_list.append(pm)
            
    return DocumentManifest(pdf_path=pdf_path, pages=pages_list, total_pages=len(pages_list))


def scan_pdf(pdf_path: Path) -> DocumentManifest:
    """
    Ponto de entrada do Radar Híbrido.
    Tenta ODL para recuperar vetores geométricos (BBox). Se falhar, Unstructured.
    """
    if HAS_ODL:
        try:
            print("[Radar] Usando OpenDataLoader (Bounding Box)...")
            return scan_with_odl(pdf_path)
        except Exception as e:
            print(f"[Radar] Falha no OpenDataLoader: {e}. Fallback unstructured.")

    if HAS_UNSTRUCTURED:
        try:
            print("[Radar] Usando Unstructured (AI Fallback)...")
            return scan_with_unstructured(pdf_path)
        except Exception as e:
            print(f"[Radar] Falha no unstructured: {e}. Fallback pdfplumber.")

    print("[Radar] Usando pdfplumber (Fallback Critico)...")
    return scan_with_pdfplumber(pdf_path)
