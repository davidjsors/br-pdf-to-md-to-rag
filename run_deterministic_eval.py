import sys
from pathlib import Path
from src.metrics.reference_evaluator import ReferenceEvaluator
from src.metrics.rag_readiness_linter import RagReadinessLinter

def run_eval():
    gabarito_path = Path("tests/ground_truth/gabarito_1.md")
    if not gabarito_path.exists():
        print(f"Erro: Gabarito não encontrado em {gabarito_path}")
        return

    with open(gabarito_path, "r", encoding="utf-8") as f:
        reference = f.read()

    candidatos = {
        "MarkItDown": Path("test_markitdown.md"),
        "PyMuPDF": Path("test_pymupdf.md"),
        "Orchestrator V2": Path("test_orchestrator.md")
    }

    ref_evaluator = ReferenceEvaluator()
    rag_linter = RagReadinessLinter()

    print("="*60)
    print("SUPER-DASHBOARD DE BENCHMARK FINAL (DETERMINÍSTICO)")
    print("O Fim das Caixas-Pretas de IA - Focado em RAG Puto")
    print("="*60)

    for nome, path in candidatos.items():
        if not path.exists():
            continue
            
        with open(path, "r", encoding="utf-8") as f:
            cand_text = f.read()

        # Eixo 1: NLP Reference Based (Jiwer / Evaluate)
        ref_scores = ref_evaluator.evaluate_all(reference, cand_text)
        
        # Eixo 2: MLOps RAG Linter (TikToken / LangChain / Markdown-It)
        rag_scores = rag_linter.evaluate(cand_text)
        
        print(f"\n[{nome.upper()}]")
        print("  EIXO 1: A Fidelidade (Texto vs Gabarito)")
        print(f"  └─ WER (Word Error Rate)..: {ref_scores['WER']:.2f} (Ideal: Próx 0.00)")
        print(f"  └─ ROUGE-L (Subsequência): {ref_scores['ROUGE_L']:.2f} (Ideal: Próx 1.00)")
        
        print("  EIXO 2: A Engenharia RAG (Saúde Estrutural)")
        print(f"  └─ Token/Word Ratio......: {rag_scores['Token_Word_Ratio']:.2f} tokens por palavra (Ideal: Menor)")
        print(f"  └─ Orphan Chunk Rate.....: {rag_scores['Orphan_Chunk_Rate']*100:.1f}% fatiados sem Header (Ideal: 0%)")
        print(f"  └─ AST Violations........: {rag_scores['AST_Violations']} saltos ilógicos/Tags estranhas (Ideal: 0)")
        print(f"  └─ Frontmatter Invalidity: {rag_scores.get('Frontmatter_Invalidity', 'N/A')} (Ideal: 0.0)")

if __name__ == "__main__":
    run_eval()
