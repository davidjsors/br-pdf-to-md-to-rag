import argparse
import sys
from pathlib import Path

from src.parser import process_pdf

def main():
    parser = argparse.ArgumentParser(
        description="BR-PDF-to-MD-to-RAG: Conversor e Limpador de PDFs brasileiros para Markdown otimizado para RAG."
    )
    
    parser.add_argument(
        "input", 
        type=str, 
        help="Caminho para o arquivo PDF ou diretório contendo arquivos PDF."
    )
    
    parser.add_argument(
        "-o", "--output", 
        type=str, 
        default=".", 
        help="Diretório de saída para os arquivos Markdown gerados (padrão: diretório atual)."
    )

    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_dir = Path(args.output)
    
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
        
    if input_path.is_file() and input_path.suffix.lower() == '.pdf':
        process_pdf(input_path, output_dir)
    elif input_path.is_dir():
        pdf_files = list(input_path.glob("*.pdf"))
        print(f"Encontrados {len(pdf_files)} PDFs no diretório '{input_path}'.")
        success_count = 0
        for pdf in pdf_files:
            if process_pdf(pdf, output_dir):
                success_count += 1
        print(f"\nProcessamento concluído. {success_count}/{len(pdf_files)} PDFs convertidos com sucesso.")
    else:
        print(f"Erro: A entrada '{input_path}' não é um arquivo PDF válido ou um diretório.")
        sys.exit(1)

if __name__ == "__main__":
    main()
