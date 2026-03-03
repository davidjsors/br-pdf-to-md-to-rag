import os
from pathlib import Path

# Configuração para evitar warnings massivos do Langsmith/Ragas na tela
os.environ["RAGAS_DO_NOT_TRACK"] = "true"

from src.metrics.ragas_evaluator import RagasEvaluator

# Este é o nosso "Gabarito Sintético" (Golden Dataset).
# Criamos perguntas cruciais cuja resposta depende de extrair dados literais do PDF.
qa_dataset = [
    {
        "question": "Qual é a data e o horário da entrevista de David Jose Soares?",
        "ground_truth": "A entrevista de David Jose Soares ocorrerá no dia 25/02/2026, às 9:40."
    },
    {
        "question": "Qual o link da entrevista online de Leonardo Maximino Bernardo?",
        "ground_truth": "O link para a entrevista de Leonardo Maximino Bernardo é meet.google.com/edw-yviy-prd."
    },
    {
        "question": "O que o candidato está proibido de usar na cabeça durante a entrevista online?",
        "ground_truth": "O candidato não pode usar boné, chapéu, lenço, turbante, véu, burca, gorro, elástico, tiara ou quaisquer outros objetos que impossibilitem a verificação fenotípica."
    }
]

def run_semantic_eval():
    print("Inicializando o Juiz de Ragas Semântico...")
    
    try:
        evaluator = RagasEvaluator(model_name="gpt-4o-mini")
    except ValueError as e:
        print(f"ERRO DE AUTENTICAÇÃO: {e}")
        print("\nPara rodar a prova real de Extração RAG LLM-as-a-Judge, você precisa exportar a chave da OpenAI:")
        print("export OPENAI_API_KEY='sk-...'")
        return

    candidatos = {
        "PyMuPDF": Path("test_pymupdf.md"),
        "Orquestrador V2": Path("test_orchestrator.md")
    }

    print("\n" + "="*50)
    print("INICIANDO BATALHA RAGAS: AVALIAÇÃO ONDE O LLM É O JUIZ")
    print("="*50)

    for nome, path in candidatos.items():
        if not path.exists():
            print(f"Arquivo não encontrado: {path}")
            continue
            
        with open(path, "r", encoding="utf-8") as f:
            cand_text = f.read()

        print(f"\n--- Avaliando Concorrente: {nome} ---")
        
        # O Ragas vai ler o Markdown como 'Contexto Recuperado' e analisar
        # se o LLM consegue tirar a verdade exata dali de dentro.
        resultado = evaluator.evaluate_markdown(cand_text, qa_dataset)
        
        # O resultado é um tipo de dicionário do HuggingFace/Ragas
        print(f"{nome} | Context Recall (A Verdade sobreviveu no MD?): {resultado['context_recall']:.2f}/1.00")
        print(f"{nome} | Context Precision (Há lixo irrelevante que atrapalha?): {resultado['context_precision']:.2f}/1.00")

if __name__ == "__main__":
    run_semantic_eval()
