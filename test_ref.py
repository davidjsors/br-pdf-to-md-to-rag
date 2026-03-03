from src.metrics.reference_evaluator import ReferenceEvaluator
evaluator = ReferenceEvaluator()
ref = "O Governo publicou a lei 5.000 que estabelece tabela de gastos R$50,00"
cand1 = "Governo publicou lei 5000 a tabela gastos  r$ 50,00" # Some miss
cand2 = "O Governo publicou a lei 5.000 que estabelece tabela de gastos R$50,00" # Perfect
print("Cand1:", evaluator.evaluate_all(ref, cand1))
print("Cand2:", evaluator.evaluate_all(ref, cand2))
