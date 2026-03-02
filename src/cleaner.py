import re

def clean_text_block(text: str) -> str:
    """
    Aplica heurísticas de limpeza de texto focado em RAG para documentos PDF brasileiros.
    Remove "lixo" fixo como paginação, cabeçalhos de escalas de preço e formata quebras indesejadas.
    """
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
