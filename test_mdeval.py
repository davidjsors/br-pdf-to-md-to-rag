from src.metrics.eval_metrics import StructuralDensityEvaluator

evaluator = StructuralDensityEvaluator()

vandalism_md = """
# TITLE
# TITLE
**bold** **bold** **bold** **bold**
<pre>code</pre>
<pre>code</pre>
<pre>code</pre>
<pre>code</pre>
"""

data_md = """
# TITLE
| Col 1 | Col 2 |
|---|---|
| A | B |
| C | D |
| E | F |
| G | H |
* Item 1
* Item 2
* Item 3
"""

tags_vand = evaluator.htmlify_and_extract_tags(vandalism_md)
tags_data = evaluator.htmlify_and_extract_tags(data_md)

print("--- RAW SCORES ---")
print(f"Vandalism Raw: {evaluator.calculate_d_rule_bonus(tags_vand)}")
print(f"Data Raw: {evaluator.calculate_d_rule_bonus(tags_data)}")

# The normalized curve
print(f"Alucinação/Vandalismo Normalized Score: {evaluator.evaluate(vandalism_md)}%")
print(f"Extração de Dados Rica Normalized Score: {evaluator.evaluate(data_md)}%")
