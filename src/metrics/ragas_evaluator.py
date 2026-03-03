import os
from langchain_openai import ChatOpenAI
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import context_recall, context_precision

class RagasEvaluator:
    """
    Evaluates the semantic quality of RAG parsed documents using LLM-as-a-Judge.
    Validates if the generated Markdown contains the factual truth needed to answer questions.
    """
    def __init__(self, model_name="gpt-4o-mini"):
        # We need an OpenAI API Key to run the judge model
        if "OPENAI_API_KEY" not in os.environ:
            raise ValueError("OPENAI_API_KEY is not set in environment variables.")
        
        # O GPT-4o-mini é super rápido e barato para atuar como Juiz Semântico
        self.llm = ChatOpenAI(model=model_name, temperature=0.0)
        
    def evaluate_markdown(self, markdown_content: str, qa_dataset: list[dict]) -> dict:
        """
        Avalia o markdown_content usando a lista de Ground Truths.
        qa_dataset format: [{"question": "...", "ground_truth": "..."}]
        """
        
        data = {
            "question": [],
            "ground_truth": [],
            "contexts": [],
            "answer": []
        }
        
        # Para Ragas avaliar a qualidade do Parser de PDF, injetamos o markdown inteiro 
        # como se fosse o "contexto recuperado" pelo banco vetorial.
        # Nós forçamos o Ragas a avaliar if este texto contém a verdade e nenhuma distorção.
        for item in qa_dataset:
            data["question"].append(item["question"])
            data["ground_truth"].append(item["ground_truth"])
            data["contexts"].append([markdown_content])
            # A 'answer' não importa tanto aqui pois estamos testando o CONTEXTO gerado pelo Parser (Context Recall),
            # mas o Ragas exige a key 'answer'. Vamos simular a ground_truth como answer para focar no Context.
            data["answer"].append(item["ground_truth"])
            
        dataset = Dataset.from_dict(data)
        
        print("Iniciando julgamento Ragas via API (Isso pode levar alguns segundos)...")
        # Avaliando se a informação vital sobreviveu dentro do Markdown (Context Recall)
        # e se o Markdown não tem ruído alienígena que atrapalhe o contexto (Context Precision)
        result = evaluate(
            dataset=dataset,
            metrics=[context_recall, context_precision],
            llm=self.llm,
        )
        
        return result
