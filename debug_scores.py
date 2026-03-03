from src.metrics.eval_metrics import StructuralDensityEvaluator
with open("test_pymupdf.md", "r") as f:
    pymu = f.read()
with open("test_orchestrator.md", "r") as f:
    orch = f.read()
evaluator = StructuralDensityEvaluator()
tags_p = evaluator.htmlify_and_extract_tags(pymu)
s_p = evaluator.calculate_d_rule_bonus(tags_p)
tags_o = evaluator.htmlify_and_extract_tags(orch)
s_o = evaluator.calculate_d_rule_bonus(tags_o)
print(f"PyMu Raw Points: {s_p}")
print(f"Orch Raw Points: {s_o}")
