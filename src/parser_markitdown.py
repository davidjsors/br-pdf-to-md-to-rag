import os
from pathlib import Path
from markitdown import MarkItDown
from openai import OpenAI

from src.cleaner import clean_text_block

def process_with_markitdown(file_path: Path, output_dir: Path, llm_api_key: str = None) -> bool:
    """
    Processa um documento usando a biblioteca MarkItDown da Microsoft.
    Suporta OCR e análise de imagens caso a chave do LLM seja passada.
    """
    print(f"Processando com MarkItDown: {file_path.name}...")
    
    try:
        # Configurar motor com ou sem OCR
        if llm_api_key:
            # Recomenda-se um modelo focado em visão para OCR (ex: gpt-4o)
            client = OpenAI(api_key=llm_api_key)
            md = MarkItDown(llm_client=client, llm_model="gpt-4o")
        else:
            # Extração padrão sem OCR avançado
            md = MarkItDown()
            
        result = md.convert(str(file_path))
        
        if not result or not result.text_content:
            print("MarkItDown retornou um resultado vazio.")
            return False

        # Aplica nossa camada de limpeza BR Híbrida 
        # (remove resquícios de R$, páginas vazadas pelo OCR, etc)
        raw_markdown = result.text_content
        cleaned_markdown = clean_text_block(raw_markdown)
        
        # Salva o arquivo final
        md_filename = file_path.stem + ".md"
        md_path = output_dir / md_filename
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(f"# {file_path.stem}\n\n")
            f.write(f"> Fonte Original: {file_path.name} (Extraído via MarkItDown)\n")
            if llm_api_key:
                f.write("> Aviso: OCR via LLM Ativado.\n\n")
            else:
                f.write("\n")
                
            f.write(cleaned_markdown)
            
        print(f"Sucesso! Gerado: {md_path}")
        return True
        
    except Exception as e:
        print(f"Erro ao processar {file_path.name} com MarkItDown: {e}")
        return False
