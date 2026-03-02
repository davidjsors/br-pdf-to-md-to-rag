import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from src.metrics.eval_metrics import calculate_structural_similarity, extract_html_tags, normalize_math
import markdown

# Gabarito ideal (Ground Truth)
perfect_md = """# Título do Documento
Este é um parágrafo introdutório que conta uma história.

## Tabela de Dados
| Coluna 1 | Coluna 2 |
| --- | --- |
| Valor A | R$ 10,00 |
| Valor B | 20% |

### Fórmula Matemática
A equação de Einstein é $E = mc^2$.
"""

# Extração Ruim (Faltam tags de tabela, formatação errada)
bad_extraction_md = """# Título do Documento
Este é um parágrafo introdutório que conta uma história.

## Tabela de Dados
Coluna 1 Coluna 2
Valor A R$ 10,00
Valor B 20%

### Fórmula Matemática
A equação de Einstein é E = mc2.
"""

# Extração Boa (Quase perfeita estruturalmente)
good_extraction_md = """# Título do Documento
Este é um parágrafo introdutório que conta uma história e tem um errinho de digiteção.

## Tabela de Dados
| C1 | C2 |
| --- | --- |
| A | 10 |
| B | 20 |

### Fórmula Matemática
A equação é $E = mc^2$.
"""

def main():
    print("--- Teste de Metricas MDEval ---")
    
    score_bad = calculate_structural_similarity(bad_extraction_md, perfect_md)
    print(f"Nota para Extração RUIM: {score_bad:.2%}")
    print("As tags da extração ruim perderam completamente as marcações de <table>, <tr>, <td>.\n")
    
    score_good = calculate_structural_similarity(good_extraction_md, perfect_md)
    print(f"Nota para Extração BOA: {score_good:.2%}")
    print("A extração boa manteve as tags de tabela e o math tag, mesmo com texto diferente dentro.\n")
    
    print("Tags do Gabarito:")
    print(extract_html_tags(markdown.markdown(normalize_math(perfect_md), extensions=['tables'])))

if __name__ == "__main__":
    main()
