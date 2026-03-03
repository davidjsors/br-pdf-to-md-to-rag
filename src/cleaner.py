import re

def clean_text_block(text: str) -> str:
    """
    Aplica heurísticas de limpeza de texto focado em RAG para documentos PDF brasileiros.
    Remove "lixo" fixo como paginação, cabeçalhos de escalas de preço e formata quebras indesejadas.
    """
    if not text: return ""
    
    # 1. Remove markers de quebra de página (\x0c ou \f)
    text = text.replace('\x0c', '').replace('\f', '')

    # 2. Remove paginação (Página 1 de 10, pg. 5, etc)
    text = re.sub(r'(?i)(?:p[áa]gina|pg\.?)\s*\d+(?:\s?de\s?\d+)?', '', text)

    # 3. Remove sequências de números que parecem eixos de gráfico (ex: 1 2 3 ... 31)
    # Detecta padrões de números curtos (1-3 dígitos) repetidos com ou sem espaços
    # Evita 4 dígitos para não apagar anos (ex: 2024)
    # Garante que a sequência tenha pelo menos 4 números curtos seguidos
    text = re.sub(r'(?:\b\d{1,3}\b(?:\s+|,)?\s?){4,}', '', text)
    
    # 4. Remove escalas de preço (R$ 350,00 R$ 0,00 etc)
    text = re.sub(r'(?:R\$\s*\d+(?:[\.,]\d{0,2})?\s*){2,}', '', text)
    
    # 5. Remove escalas residuais (R$ R$ R$ ou 350,00 300,00)
    text = re.sub(r'\b(?:R\$\s*){2,}', '', text)
    text = re.sub(r'(?:\d+[\.,]\d{2}\s*){2,}', '', text)

    # Remove hífens de quebra de linha
    text = re.sub(r'(\w)-\s*\n\s*([a-zà-ú])', r'\1\2', text)
    
    # Une quebras de linha no meio de frases (letra minúscula após quebra)
    text = re.sub(r'([a-zà-ú,;])\n+([a-zà-ú])', r'\1 \2', text)
    
    # 7. Remove espaços duplos e resíduos
    text = re.sub(r' +', ' ', text)
    
    # 8. Limpeza final de pontuação repetida (ruído de extração)
    text = re.sub(r'([\.?!,;])\1+', r'\1', text)
    
    # 9. Injetar Headers em documentos "flat" (Heurística de Prontidão RAG)
    # Promove linhas ALL CAPS isoladas (10 a 120 caracteres) para H2
    def promote_caps_to_h2(match):
        line = match.group(0).strip()
        if len(line.split()) < 2:
            return line
        if re.match(r'^[\d\s\.,\-]+$', line):
            return line
        return f"\n## {line}\n"

    text = re.sub(r'^[A-ZÀ-Ú0-9\s,\.\-\/]{10,120}$', promote_caps_to_h2, text, flags=re.MULTILINE)
    
    # Promove "Assunto: " explícito para H3
    text = re.sub(r'^(Assunto:[^\n]+)$', r'\n### \1\n', text, flags=re.MULTILINE | re.IGNORECASE)

    # Promove linhas inteiras com Negrito (do PyMuPDF) para H3
    text = re.sub(r'^\*\*([^\*]{5,120})\*\*\s*$', r'\n### \1\n', text, flags=re.MULTILINE)
    
    return text.strip()
