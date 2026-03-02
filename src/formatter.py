def table_to_markdown(table: list) -> str:
    """
    Converte uma lista de listas (representando uma tabela extraída) em uma tabela Markdown.
    """
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
