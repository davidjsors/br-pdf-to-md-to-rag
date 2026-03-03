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
    
    # 2. Convert to HTML
    # We use extensions to support tables, fenced code blocks, etc.
    extensions = ['tables', 'fenced_code', 'nl2br', 'sane_lists']
    pred_html = markdown.markdown(pred_md, extensions=extensions)
    ref_html = markdown.markdown(ref_md, extensions=extensions)
    
    # 3. Extract tag sequences (skeletons)
    pred_tags = extract_html_tags(pred_html)
    ref_tags = extract_html_tags(ref_html)
    
    # 4. Calculate Levenshtein Distance
    # Represent tags as joined strings to use Levenshtein
    # or use Levenshtein distance on lists (if library supports it, python-Levenshtein typically works on strings)
    # Since tags can be multi-character, we map them to unique characters or use a generic list distance.
    # We'll use sequence matcher or editops for list-based distance, but for simplicity, 
    # joining them is a fast approximation if tags don't overlap uniquely.
    # A safer way is to use difflib or a custom edit distance for lists.
    import difflib
    matcher = difflib.SequenceMatcher(None, pred_tags, ref_tags)
    
    # Ratio gives 2*M / (T) which is similar to 1 - (distance / max(len))
    # We'll stick to a strict Edit Distance calculation for exact MDEval parity.
    distance = sum(1 for tag, i1, i2, j1, j2 in matcher.get_opcodes() if tag != 'equal' for _ in range(max(i2-i1, j2-j1)))
    
    max_len = max(len(pred_tags), len(ref_tags))
    
    if max_len == 0:
        return 1.0 # Both are completely empty structurally
        
    similarity = 1.0 - (distance / max_len)
    
    # Ensure it's bounded between 0 and 1
    return max(0.0, min(1.0, similarity))

class StructuralDensityEvaluator:
    """
    Avalia a saúde estrutural de um Markdown com base na riqueza de tags geradas.
    Retorna um score de 0 a 100%.
    """
    def evaluate(self, md_content: str) -> float:
        if not md_content or not md_content.strip():
            return 0.0
            
        # Extrair tags HTML usando a lógica interna do MDEval
        html_tags = extract_html_tags(markdown.markdown(normalize_math(md_content), extensions=['tables']))
        
        # Heurística que estava no app.py legado
        structural_density = min(100.0, float(len(html_tags)) * 1.5) if len(html_tags) > 0 else 0.0
        
        return structural_density
