import re
from pathlib import Path
from src.cleaner import clean_text_block
from src.formatter import table_to_markdown

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

def parse_pdf_plumber_segmented(pdf_path: Path) -> list:
    """
    Especialista: pdfplumber.
    Retorna uma lista de blocos identificados: 
    [{ 'type': 'text', 'content': '...'}, { 'type': 'table', 'content': '...'}]
    """
    if pdfplumber is None:
        return [{"type": "error", "content": "pdfplumber não instalado"}]

    segments = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                # Localizar tabelas
                tables_objects = page.find_tables()
                table_bboxes = [t.bbox for t in tables_objects]
                
                # Extrair texto excluindo áreas de tabelas
                # (Isso preserva o 'buraco' onde a tabela deveria estar)
                non_table_text = page.filter(lambda obj: not any(
                    obj['x0'] >= b[0] and obj['top'] >= b[1] and 
                    obj['x1'] <= b[2] and obj['bottom'] <= b[3]
                    for b in table_bboxes
                )).extract_text()
                
                # Por simplicidade na primeira versão da síntese:
                # 1. Adicionamos o texto limpo da página
                if non_table_text:
                    segments.append({
                        "type": "text",
                        "content": clean_text_block(non_table_text),
                        "page": page.page_number
                    })
                
                # 2. Adicionamos as tabelas com alta precisão
                for t_obj in tables_objects:
                    table_data = t_obj.extract()
                    md_table = table_to_markdown(table_data)
                    if md_table:
                        segments.append({
                            "type": "table",
                            "content": md_table,
                            "page": page.page_number
                        })
        
        return segments
        
    except Exception as e:
        return [{"type": "error", "content": str(e)}]
