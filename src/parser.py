import re
from pathlib import Path

from src.cleaner import clean_text_block
from src.formatter import table_to_markdown

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

def process_pdf(pdf_path: Path, output_dir: Path) -> bool:
    """
    Processa um PDF, extrai textos limpos e tabelas em Markdown e salva em um arquivo.
    """
    if pdfplumber is None:
        raise ImportError("Biblioteca pdfplumber não encontrada. Por favor instale: pip install -r requirements.txt")

    print(f"Processando: {pdf_path.name}...")
    
    full_content = []
    seen_titles = set()
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                # 1. Identificar áreas das tabelas para evitar duplicar texto
                tables_objects = page.find_tables()
                table_bboxes = [t.bbox for t in tables_objects]
                
                # 2. Extrair texto excluindo as áreas das tabelas
                non_table_text = page.filter(lambda obj: not any(
                    obj['x0'] >= b[0] and obj['top'] >= b[1] and 
                    obj['x1'] <= b[2] and obj['bottom'] <= b[3]
                    for b in table_bboxes
                )).extract_text()
                
                # 3. Processar o texto extraído
                if non_table_text:
                    lines = non_table_text.split('\n')
                    processed_lines = []
                    for line in lines:
                        ls = line.strip()
                        if not ls: continue
                        if ls.isdigit() and len(ls) <= 3: continue
                        
                        # Controle de cabeçalhos repetidos
                        clean_l = re.sub(r'[^\w]', '', ls).lower()
                        if len(ls) < 100:
                            if clean_l in seen_titles: continue
                            if clean_l: seen_titles.add(clean_l)
                        
                        processed_lines.append(line)
                    
                    text_out = clean_text_block('\n'.join(processed_lines))
                    if text_out:
                        full_content.append(text_out)
                
                # 4. Adicionar as tabelas reais
                for t_obj in tables_objects:
                    table_data = t_obj.extract()
                    md_table = table_to_markdown(table_data)
                    if md_table:
                        full_content.append("\n" + md_table)
                
        # Salva o arquivo final
        md_filename = pdf_path.stem + ".md"
        md_path = output_dir / md_filename
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(f"# {pdf_path.stem}\n\n")
            f.write(f"> Fonte Original: {pdf_path.name}\n\n")
            f.write("\n\n".join(full_content))
            
        print(f"Sucesso! Gerado: {md_path}")
        return True
        
    except Exception as e:
        print(f"Erro ao processar {pdf_path.name}: {e}")
        return False
