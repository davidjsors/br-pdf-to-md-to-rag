import os
import re
from pathlib import Path
try:
    import pdfplumber
except ImportError:
    print("Biblioteca pdfplumber não encontrada. Por favor instale: pip install pdfplumber")
    exit(1)

# Configuração de Caminhos
BASE_DIR = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = BASE_DIR / 'knowledge'

def table_to_markdown(table):
    """Converte uma lista de listas (representando uma tabela) em Markdown."""
    if not table or not any(table):
        return ""
    
    # Remove linhas vazias e limpa None
    table = [[(str(cell).replace('\n', ' ').strip() if cell is not None else "") for cell in row] for row in table]
    table = [row for row in table if any(cell.strip() for cell in row)]
    
    if not table: return ""

    cols = len(table[0])
    md_table = []
    
    # Cabeçalho
    md_table.append("| " + " | ".join(table[0]) + " |")
    # Separador
    md_table.append("| " + " | ".join(["---"] * cols) + " |")
    
    # Dados
    for row in table[1:]:
        if len(row) < cols:
            row.extend([""] * (cols - len(row)))
        md_table.append("| " + " | ".join(row[:cols]) + " |")
        
    return "\n".join(md_table) + "\n\n"

def clean_text_block(text):
    """Aplica heurísticas de limpeza de texto para Markdown."""
    if not text: return ""
    
    # Remove Form Feed (FF) - marcador de quebra de página (\x0c ou \f)
    text = text.replace('\x0c', '').replace('\f', '')

    # Remove sequências de números que parecem eixos de gráfico (ex: 1 2 3 ... 31)
    # Detecta padrões de números curtos (1-4 dígitos) repetidos com ou sem espaços
    text = re.sub(r'\b(?:\d{1,4}(?:\s+|,)?\s?){3,}\b', '', text)
    
    # Remove escalas de preço (R$ 350,00 R$ 0,00 etc)
    text = re.sub(r'(?:R\$\s*\d+(?:[\.,]\d{0,2})?\s*){2,}', '', text)
    
    # Remove escalas residuais (R$ R$ R$ ou 350,00 300,00)
    text = re.sub(r'(?:R\$\s*){3,}', '', text)
    text = re.sub(r'(?:\d+[\.,]\d{2}\s*){2,}', '', text)

    # Remove hífens de quebra de linha
    text = re.sub(r'(\w)-\s*\n\s*([a-zà-ú])', r'\1\2', text)
    
    # Une quebras de linha no meio de frases (letra minúscula após quebra)
    text = re.sub(r'([a-zà-ú,;])\n+([a-zà-ú])', r'\1 \2', text)
    
    # Remove espaços duplos e resíduos
    text = re.sub(r' +', ' ', text)
    
    return text.strip()

def process_pdf(pdf_path):
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
                # Filtra caracteres que não estão dentro de nenhuma tabela
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
        md_path = KNOWLEDGE_DIR / md_filename
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(f"# {pdf_path.stem}\n\n")
            f.write(f"> Fonte Original: {pdf_path.name}\n\n")
            f.write("\n\n".join(full_content))
            
        print(f"Sucesso! Gerado: {md_filename}")
        return True
        
    except Exception as e:
        print(f"Erro ao processar {pdf_path.name}: {e}")
        return False

def main():
    if not KNOWLEDGE_DIR.exists():
        return
    pdf_files = list(KNOWLEDGE_DIR.glob('*.pdf'))
    print(f"Encontrados {len(pdf_files)} PDFs.")
    for pdf in pdf_files:
        process_pdf(pdf)

if __name__ == "__main__":
    main()
