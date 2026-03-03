import argparse
import sys
from pathlib import Path

from src.orchestrator import process_pdf

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
        
    def process_file(pdf_path: Path):
        MAX_SIZE = 1 * 1024 * 1024
        if pdf_path.stat().st_size > MAX_SIZE:
             print(f"❌ Erro: {pdf_path.name} excede o limite de 1 MB.")
             return False
             
        print(f"Processando: {pdf_path.name} ...")
        result = process_pdf(pdf_path)
        if result.success:
            md_path = output_dir / f"{pdf_path.stem}.md"
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(result.final_markdown)
            print(f"✅ Sucesso: Salvo em {md_path}")
            return True
        else:
            print(f"❌ Erro ao processar {pdf_path.name}: {result.error}")
            return False

    if input_path.is_file() and input_path.suffix.lower() == '.pdf':
        process_file(input_path)
    elif input_path.is_dir():
        pdf_files = list(input_path.glob("*.pdf"))
        print(f"Encontrados {len(pdf_files)} PDFs no diretório '{input_path}'.\n")
        success_count = 0
        for pdf in pdf_files:
            if process_file(pdf):
                success_count += 1
        print(f"\nResumo: {success_count}/{len(pdf_files)} PDFs convertidos com sucesso.")
    else:
        print(f"Erro: A entrada '{input_path}' não é um arquivo PDF válido ou um diretório.")
        sys.exit(1)

if __name__ == "__main__":
    main()
