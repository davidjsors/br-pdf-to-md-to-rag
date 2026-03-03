"""
Tradutor OpenDataLoader JSON para Markdown Nato.
Age como um Parser para a Arquitetura de Mosaico (ADR-0001).
Varrerá a árvore do ODL `kids` extraindo o texto e as coordenadas num formato útil para os Juízes (Bounding Box tracking).
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class ODLNode:
    type: str
    text: str
    bbox: Optional[List[float]] = None
    id: Optional[int] = None
    # Armazena os sub-items caso seja uma lista ou tabela complexa
    children: List['ODLNode'] = field(default_factory=list)


class OpenDataLoaderParser:
    """
    Percorre a árvore ODL e as achata (flatten) num documento estruturado Markdown e BBoxes para o Comitê.
    """
    def __init__(self):
        self.nodes: List[ODLNode] = []
        
    def parse_odl_json(self, odl_dict: Dict[str, Any]) -> List[ODLNode]:
        """
        Ponto de entrada do documento JSON raíz `{"kids": [páginas...]}`.
        """
        self.nodes = []
        if "kids" not in odl_dict:
            return self.nodes
            
        for page_node in odl_dict.get("kids", []):
            self._traverse_page(page_node)
            
        return self.nodes
        
    def _traverse_page(self, page_node: Dict[str, Any]):
        """Desce num nó do tipo Page e avalia os seus filhos diretos."""
        if page_node.get("type") == "image": 
            # ODL às vezes categoriza página escaneada inteira como picture
            # Se for esse caso, não haverá texto estruturado, só a caixa.
            self.nodes.append(ODLNode(
                type="scanned_image_page", 
                text="", 
                bbox=page_node.get("bounding box"),
                id=page_node.get("id")
            ))
            return

        for child in page_node.get("kids", []):
            self._process_element(child)

    def _process_element(self, element: Dict[str, Any], parent_type: str = ""):
        node_type = element.get("type", "").lower()
        bbox = element.get("bounding box")
        node_id = element.get("id")
        
        # OpenDataLoader tem text properties diretamente no nó as vezes
        text = str(element.get("text", ""))
        
        # Se for um node composto (tem kids), junta o texto e busca recursivamente
        has_text_kids = False
        if "kids" in element:
            for inner in element["kids"]:
                if inner.get("type", "") in ["text", "line"]:
                    text += str(inner.get("text", ""))
                    has_text_kids = True
                    
            if not has_text_kids:
                 for inner in element["kids"]:
                     self._process_element(inner, parent_type=node_type)

        if node_type == "paragraph" or parent_type == "paragraph":
             if text.strip():
                 self.nodes.append(ODLNode("paragraph", text, bbox, node_id))
        
        elif "heading" in node_type:
             if text.strip():
                 self.nodes.append(ODLNode("heading", text, bbox, node_id))
             
        elif node_type == "table":
             # Placeholder pra tabelas, o Juiz de Dados (pdfplumber) tomará essa caixa depois
             self.nodes.append(ODLNode("table_anchor", "<!-- TABLE_ANCHOR_ODL -->", bbox, node_id))
             
        elif node_type == "list":
             if text.strip():
                 self.nodes.append(ODLNode("list", text, bbox, node_id))
             
        elif node_type == "image":
             self.nodes.append(ODLNode("image_anchor", "<!-- IMMAGE_ANCHOR_ODL -->", bbox, node_id))
             
        else:
             # Backup para texto indiscriminado
             if text.strip() != "":
                 self.nodes.append(ODLNode("raw_text", text, bbox, node_id))

    
    def nodes_to_markdown(self) -> str:
        """
        Reconstrói o documento PDF de forma linear usando as anotações semânticas.
        """
        md_lines = []
        for node in self.nodes:
            if node.type == "heading":
                # Convertendo generic heading para MD Header 2 caso ODL não dê nivel
                md_lines.append(f"\n## {node.text.strip()}\n")
            elif node.type == "paragraph" or node.type == "raw_text":
                md_lines.append(f"{node.text.strip()}\n")
            elif node.type == "list":
                md_lines.append(f"- {node.text.strip()}")
            elif node.type == "table_anchor":
                md_lines.append(node.text)
        
        return "\n".join(md_lines)
