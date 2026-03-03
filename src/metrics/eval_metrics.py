import re
import markdown
from bs4 import BeautifulSoup
import Levenshtein

def extract_html_tags(html_content: str) -> list:
    """
    Extracts only the HTML tags in sequence, ignoring the text content.
    This creates a structural "skeleton" of the document.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    tags = []
    
    # Iterate through all elements and get their tag names
    # excluding the implicit html/body wrappers added by BeautifulSoup
    for tag in soup.find_all(True):
        if tag.name not in ['html', 'body']:
            tags.append(f"<{tag.name}>")
            
    return tags

def normalize_math(markdown_text: str) -> str:
    """
    Replaces LaTeX math expressions with a standard <math> tag
    to prevent structural degradation during HTML conversion.
    Based on MDEval logic.
    """
    # Block math: $$...$$
    pattern_display = r'\$\$.*?\$\$'
    markdown_text = re.sub(pattern_display, '<math>', markdown_text, flags=re.DOTALL)
    
    # Inline math: $...$
    pattern_inline = r'\$(.*?)\$'
    # Avoid replacing single dollars that might be prices (e.g., R$ 10)
    # Only replace if there's no space right after the first dollar
    # and no space right before the second dollar.
    # This is a simplified heuristic.
    markdown_text = re.sub(r'(?<!R)\$([^ \n].*?[^ \n]?)\$', '<math>', markdown_text)
    
    return markdown_text

def calculate_structural_similarity(predicted_md: str, reference_md: str) -> float:
    """
    Calculates the MDEval structural similarity score.
    Returns a score between 0.0 and 1.0.
    """
    # 1. Normalize Math
    pred_md = normalize_math(predicted_md)
    ref_md = normalize_math(reference_md)
    
class StructuralDensityEvaluator:
    """
    Motor Reference-Free de Avaliação Estrutural (Inspirado no MDEval-Benchmark).
    Calcula a aderência e riqueza do Markdown extraído convertendo para HTML e
    aplicando a regra de Decaimento (D-Rule) para evitar inflação por prolixidade,
    seguida de uma penalidade rigorosa de Lixo Visual (Regex BR).
    """
    
    def __init__(self, gamma: float = 0.5):
        """
        :param gamma: Fator de decaimento para tags repetidas (evita viés prolixo).
                      O 1º tag vale 1.0, o 2º vale 0.5, o 3º vale 0.25, etc.
        """
        self.gamma = gamma
        
        # Tags de Dados Reais (Volume de Matrizes e Tópicos) -> Sem Decaimento (Linear)
        self.linear_tags = {'table', 'tr', 'th', 'td', 'ul', 'ol', 'li'}
        
        # Tags de Hierarquia e Cosmética -> Com Decaimento (Punição por Vandalismo/Repetição)
        # Blocos de código, aspas falsas e excesso de formatação indicam quebra de leitura de OCR
        self.decay_tags = {'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'b', 'strong', 'i', 'em', 'hr', 'pre', 'code', 'blockquote', 'math'}
        
        self.valuable_tags = self.linear_tags.union(self.decay_tags)
        
        # Padrões de Lixo Visual Brasileiro compilados para a penalidade
        self.garbage_patterns = [
            r'(?i)(?:p[áa]gina|pg\.?)\s*\d+(?:\s?de\s?\d+)?', # Numeração de página
            r'(?:\b\d{1,3}\b(?:\s+|,)?\s?){4,}',             # Eixos de gráfico / réguas numéricas
            r'(?:R\$\s*\d+(?:[\.,]\d{0,2})?\s*){2,}',        # Tabelas de preço vazando R$ R$
            r'\b(?:R\$\s*){2,}'                              # R$ vazio consecutivo
        ]

    def htmlify_and_extract_tags(self, md_text: str) -> list[str]:
        """Converte Markdown para HTML e isola a estrutura de tags."""
        html_content = markdown.markdown(md_text, extensions=['tables', 'fenced_code'])
        soup = BeautifulSoup(html_content, "html.parser")
        
        extracted_tags = []
        for tag in soup.find_all(True):
            if tag.name in self.valuable_tags:
                extracted_tags.append(tag.name)
        return extracted_tags

    def calculate_d_rule_bonus(self, tags: list[str]) -> float:
        """
        Calcula o Score Estrutural base considerando a natureza da tag (Linear vs Decaimento).
        """
        bonus_score = 0.0
        tag_counts: dict[str, int] = defaultdict(int)
        
        for tag in tags:
            current_count = tag_counts[tag]
            
            # Se a tag for estrutural linear (Dados/Tabelas/Listas), peso sempre 1.0 (sem decaimento)
            if tag in self.linear_tags:
                weight = 1.0
                # Super-bônus para o início de uma tabela ou linha pura, pois isso é o Santo Graal do extrator
                base_multiplier = 2.0 if tag in ['table', 'tr'] else 1.0
                
            # Se a tag for cosmética/hierárquica, sofre o Decaimento D-Rule ($ \gamma^{repetições} $)
            else:
                weight = self.gamma ** current_count
                base_multiplier = 1.0
            
            bonus_score += (weight * base_multiplier)
            tag_counts[tag] += 1
            
        return bonus_score

    def calculate_garbage_penalty(self, text: str) -> float:
        """
        Aplica o pente fino das heurísticas BR para arrancar pontos de modelos 
        que vazam lixo visual do PDF (páginas, rodapés vazios).
        """
        penalty = 0.0
        
        for pattern in self.garbage_patterns:
            matches = len(re.findall(pattern, text))
            penalty += (matches * 1.5)  # Cada vazamento custa 1.5 de saúde
            
        # Penaliza blocos massivos sem parágrafos (sopa de letras amórfica)
        if len(text) > 1000 and text.count('\n\n') < 2:
            penalty += 5.0
            
        return penalty

    def evaluate(self, md_text: str) -> float:
        """
        Retorna o Score Final (0 a 100%) baseado no HTMLifying e Heurísticas de Defesa.
        Como é Reference-Free (Sem Gabarito de Teto), usamos uma função de achatamento.
        """
        if not md_text or len(md_text.strip()) < 5:
            return 0.0
            
        # 1. Extração Estrutural
        tags = self.htmlify_and_extract_tags(md_text)
        
        # 2. Cálculo do Bônus (D-Rule)
        bonus = self.calculate_d_rule_bonus(tags)
        
        # 3. Cálculo do Lixo
        penalty = self.calculate_garbage_penalty(md_text)
        
        raw_score = bonus - penalty
        if raw_score <= 0:
            return 0.0
            
        # Curva de achatamento para converter a pontuação infinita em um Percentual 0-100%
        # Quanto maior o score cru, mais ele tende a 100%. Uma tabela linda ou 5 títulos geram ~80%+
        # score = 100 * (1 - e^(-raw_score / constante_fator))
        normalized_percentage = 100.0 * (1.0 - math.exp(-raw_score / 15.0))
        
        return float(round(normalized_percentage, 2))

# Compatibilidade com APIs legadas do projeto
def calculate_structural_similarity(generated: str, reference: str) -> float:
    # Como abolimos o reference no pipeline, apenas redirecionamos
    return StructuralDensityEvaluator().evaluate(generated)

def extract_html_tags(md_text: str) -> list:
    return StructuralDensityEvaluator().htmlify_and_extract_tags(md_text)

def normalize_math(text: str) -> str:
    # Mantida para compatibilidade passiva
    return text
