import sys
import os
from pathlib import Path
from markitdown import MarkItDown
import pymupdf4llm
from src.orchestrator import process_pdf
from src.metrics.eval_metrics import StructuralDensityEvaluator

corpus_dir = Path("tests/corpus")
pdf_files = list(corpus_dir.glob("*.pdf"))

if not pdf_files:
    print("Nenhum arquivo PDF encontrado no diretório tests/corpus.")
    sys.exit(0)

evaluator = StructuralDensityEvaluator()
md_engine = MarkItDown()

results = []

print(f"Iniciando benchmark em {len(pdf_files)} arquivos PDF do Corpus...\n")

for pdf_path in pdf_files:
    print(f"Processando: {pdf_path.name}")
    
    # 1. MarkItDown Pure
    try:
        res_md = md_engine.convert(str(pdf_path))
        m_text = res_md.text_content
        score_markitdown = evaluator.evaluate(m_text)
    except Exception as e:
        score_markitdown = -1.0 # Falha

    # 2. PyMuPDF Pure
    try:
        p_text = pymupdf4llm.to_markdown(str(pdf_path))
        score_pymupdf = evaluator.evaluate(p_text)
    except Exception as e:
        score_pymupdf = -1.0 # Falha

    # 3. Orquestrador V2
    try:
        res_orch = process_pdf(pdf_path)
        score_orchestrator = evaluator.evaluate(res_orch.final_markdown)
    except Exception as e:
        score_orchestrator = -1.0 # Falha

    results.append({
        "arquivo": pdf_path.name,
        "markitdown": score_markitdown,
        "pymupdf": score_pymupdf,
        "orquestrador": score_orchestrator
    })

print("\n\n" + "="*50)
print("RELATÓRIO FINAL DO CORPUS")
print("="*50)

with open("corpus_benchmark_report.md", "w", encoding="utf-8") as f:
    f.write("# Relatório de Benchmark do Corpus (MDEval V2)\n\n")
    f.write("| Arquivo PDF | MarkItDown | PyMuPDF | Orquestrador |\n")
    f.write("|---|---|---|---|\n")
    
    for r in results:
        f.write(f"| {r['arquivo']} | {r['markitdown']:.2f}% | {r['pymupdf']:.2f}% | **{r['orquestrador']:.2f}%** |\n")
        print(f"[{r['arquivo']}]")
        print(f"  └─ MarkItDown:   {r['markitdown']:.2f}%")
        print(f"  └─ PyMuPDF:      {r['pymupdf']:.2f}%")
        print(f"  └─ Orquestrador: {r['orquestrador']:.2f}%\n")

print("Resultados salvos em corpus_benchmark_report.md")
