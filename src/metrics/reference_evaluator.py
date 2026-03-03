import re
import jiwer
import evaluate

class ReferenceEvaluator:
    """
    Deterministically evaluates the generated Markdown against a ground-truth reference Markdown
    using standard NLP metrics (WER, ROUGE).
    Focuses on RAG applicability: preserving logical text sequences and avoiding hallucinated noise.
    """
    def __init__(self):
        # Carrega a métrica ROUGE da biblioteca Evaluate (HuggingFace)
        self.rouge = evaluate.load("rouge")
        
    def clean_text_for_eval(self, text: str) -> str:
        """
        Para avaliar o conteúdo bruto (semântica lexical), removemos caracteres puramente visuais do Markdown,
        focando apenas nas palavras resultantes para que ROUGE e WER façam um alinhamento justo.
        """
        # Remove caracteres do Markdown: #, *, _, |, `, ~, [, ], (, )
        text = re.sub(r'[#\*_\|`\~\[\]\(\)]', ' ', text)
        # Normaliza espaços
        text = re.sub(r'\s+', ' ', text)
        return text.strip().lower()

    def compute_wer(self, reference: str, candidate: str) -> float:
        """
        Word Error Rate (WER) via Jiwer.
        Mede a porcentagem de palavras que precisam ser inseridas, deletadas ou substituídas
        para o candidato virar a referência.
        Quanto MENOR (mais próximo de 0.0), MELHOR.
        """
        ref_clean = self.clean_text_for_eval(reference)
        cand_clean = self.clean_text_for_eval(candidate)
        
        if not ref_clean or not cand_clean:
            return 1.0 # Punição máxima se a string for vazia
            
        return jiwer.wer(ref_clean, cand_clean)

    def compute_rouge(self, reference: str, candidate: str) -> dict:
        """
        ROUGE Scores (Recall-Oriented Understudy for Gisting Evaluation).
        Mede a sobreposição de sequências (n-gramas) entre o texto gerado e a referência.
        ROUGE-L é crucial pois mede a maior subsequência comum (preservação de blocos inteiros).
        Quanto MAIOR (mais próximo de 1.0), MELHOR.
        """
        ref_clean = self.clean_text_for_eval(reference)
        cand_clean = self.clean_text_for_eval(candidate)
        
        if not ref_clean or not cand_clean:
            return {"rouge1": 0.0, "rouge2": 0.0, "rougeL": 0.0, "rougeLsum": 0.0}
            
        results = self.rouge.compute(predictions=[cand_clean], references=[ref_clean])
        return results

    def evaluate_all(self, reference: str, candidate: str) -> dict:
        """Executa a bateria completa de testes baseados em referência."""
        wer_score = self.compute_wer(reference, candidate)
        rouge_scores = self.compute_rouge(reference, candidate)
        
        return {
            "WER": wer_score,
            "ROUGE_L": rouge_scores.get("rougeL", 0.0),
            "ROUGE_1": rouge_scores.get("rouge1", 0.0)
        }
