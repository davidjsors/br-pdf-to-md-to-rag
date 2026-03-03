import time
import csv
from pathlib import Path
import argparse

# Importa os especialistas isolados
from src.specialists.narrative_markitdown import extract_narrative_markitdown
from src.specialists.narrative_pymupdf import extract_narrative_pymupdf

# Importa o nosso novo Comitê Orquestrado (V2)
from src.orchestrator import process_pdf

# Importa o Juiz MDEval para avaliar a qualidade
from src.metrics.eval_metrics import StructuralDensityEvaluator

# Adapter para docling (pois docling especialista extrai só tabelas, precisamos ler a página inteira para benchmark)
def extract_docling_full(pdf_path: Path) -> str:
    try:
        from docling.document_converter import DocumentConverter
        converter = DocumentConverter()
        result = converter.convert(str(pdf_path))
        return result.document.export_to_markdown()
    except Exception as e:
        print(f"Erro docling: {e}")
        return ""

def extract_marker_full(pdf_path: Path) -> str:
    try:
        from marker.convert import convert_single_pdf
        from marker.models import load_all_models
        # Nota: Carregar os modelos demora. Num cenário real pre-carregaríamos fora do loop.
        models = load_all_models()
        full_text, _, _ = convert_single_pdf(str(pdf_path), models)
        return full_text if full_text else ""
    except Exception as e:
        print(f"Erro marker-pdf: {e}")
        return ""

def run_benchmark(corpus_dir: str, output_csv: str):
    base_path = Path(corpus_dir)
    pdf_files = list(base_path.glob("*.pdf"))
    
    if not pdf_files:
        print(f"⚠️ Nenhum PDF encontrado em '{corpus_dir}'.")
        print("-> Por favor, adicione alguns PDFs de teste nessa pasta e rode o script novamente.")
        return
        
    evaluator = StructuralDensityEvaluator()
    results = []
    
    print(f"🚀 Iniciando Benchmark do BR-PDF-to-MD-to-RAG em {len(pdf_files)} arquivos...\n")
    
    for pdf_path in pdf_files:
        print(f"--- 📄 Avaliando: {pdf_path.name} ---")
        
        # ----------------------------------------------------
        # 1. Baseline: MarkItDown (Isolado)
        # ----------------------------------------------------
        print("  -> Competidor 1: MarkItDown (Isolado)...", end="", flush=True)
        start_t = time.time()
        md_mit = extract_narrative_markitdown(pdf_path)
        time_mit = time.time() - start_t
        score_mit = evaluator.evaluate(md_mit)
        print(f" [{time_mit:.2f}s | Score: {score_mit:.1f}%]")
        
        # ----------------------------------------------------
        # 2. Baseline: pymupdf4llm (Isolado)
        # ----------------------------------------------------
        print("  -> Competidor 2: pymupdf4llm (Isolado)...", end="", flush=True)
        start_t = time.time()
        md_pym = extract_narrative_pymupdf(pdf_path)
        time_pym = time.time() - start_t
        score_pym = evaluator.evaluate(md_pym)
        print(f" [{time_pym:.2f}s | Score: {score_pym:.1f}%]")
        
        # ----------------------------------------------------
        # 3. Baseline: Docling (Isolado)
        # ----------------------------------------------------
        print("  -> Competidor 3: Docling (IBM)...", end="", flush=True)
        start_t = time.time()
        md_docling = extract_docling_full(pdf_path)
        time_docling = time.time() - start_t
        score_docling = evaluator.evaluate(md_docling) if md_docling else 0.0
        print(f" [{time_docling:.2f}s | Score: {score_docling:.1f}%]")

        # ----------------------------------------------------
        # 4. Baseline: Marker-PDF (Isolado)
        # ----------------------------------------------------
        print("  -> Competidor 4: Marker-PDF (IA)...", end="", flush=True)
        start_t = time.time()
        md_marker = extract_marker_full(pdf_path)
        time_marker = time.time() - start_t
        score_marker = evaluator.evaluate(md_marker) if md_marker else 0.0
        print(f" [{time_marker:.2f}s | Score: {score_marker:.1f}%]")
        
        # ----------------------------------------------------
        # 5. Solução Proposta: Comitê Orquestrado (V2)
        # ----------------------------------------------------
        print("  -> Nosso App: Comitê V2 Orquestrado...", end="", flush=True)
        start_t = time.time()
        
        # Usamos o orquestrador completo que roda as 4 etapas
        res_v2 = process_pdf(pdf_path)
        
        time_v2 = time.time() - start_t
        score_v2 = res_v2.mdeval_score if res_v2.success else 0.0
        
        if res_v2.success:
            print(f" [{time_v2:.2f}s | Score: {score_v2:.1f}% | Vencedor Prosa: {res_v2.stats.get('narrative_winner', 'Erro')}]")
        else:
            print(f" [FALHOU: {res_v2.error}]")
            
        print("") # Quebra de linha
        
        # Salva o log desta iteração na lista final
        results.append({
            "Arquivo PDF": pdf_path.name,
            "MarkItDown_Score(%)": f"{score_mit:.1f}",
            "MarkItDown_Tempo(s)": f"{time_mit:.2f}",
            "PyMuPDF_Score(%)": f"{score_pym:.1f}",
            "PyMuPDF_Tempo(s)": f"{time_pym:.2f}",
            "Docling_Score(%)": f"{score_docling:.1f}",
            "Docling_Tempo(s)": f"{time_docling:.2f}",
            "Marker_Score(%)": f"{score_marker:.1f}",
            "Marker_Tempo(s)": f"{time_marker:.2f}",
            "ComiteV2_Score(%)": f"{score_v2:.1f}",
            "ComiteV2_Tempo(s)": f"{time_v2:.2f}",
            "ComiteV2_Tabelas_Injetadas": res_v2.stats.get("tables_injected", 0) if res_v2.success else 0,
            "ComiteV2_Vencedor_Narrativa": res_v2.stats.get("narrative_winner", "Falha") if res_v2.success else "Falha"
        })
        
    # Exportar resultados para CSV
    keys = results[0].keys()
    with open(output_csv, 'w', newline='', encoding='utf-8') as output_file:
        dict_writer = csv.DictWriter(output_file, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(results)
        
    print(f"✅ Benchmark concluído com sucesso!")
    print(f"📊 Os resultados foram salvos no Excel/Planilha em: {output_csv}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script de Bateria de Testes Benchmark")
    parser.add_argument("--corpus", type=str, default="tests/corpus", help="Diretório onde os PDFs de teste estão")
    parser.add_argument("--output", type=str, default="resultados_benchmark.csv", help="Nome do arquivo CSV de saída")
    args = parser.parse_args()
    
    run_benchmark(args.corpus, args.output)
