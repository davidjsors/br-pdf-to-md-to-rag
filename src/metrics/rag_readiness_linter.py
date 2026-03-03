import re
import tiktoken
import yaml
from markdown_it import MarkdownIt
from langchain_text_splitters import MarkdownHeaderTextSplitter

class RagReadinessLinter:
    """
    Verifica matematicamente o quão 'saudável' o Markdown é para ser ingerido por RAG.
    Zero IA. Apenas parsing estrutural (AST), vetorização espacial e contagem de Tokens.
    """
    
    def __init__(self):
        self.md_parser = MarkdownIt()
        # Header splitter padrão do LangChain
        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
            ("####", "Header 4"),
        ]
        self.text_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
        self.encoder = tiktoken.get_encoding("cl100k_base") # Encoder do GPT-4 / Langchain
        
    def _count_words(self, text: str) -> int:
        # Conta palavras brutos sem tags MD para o ratio (Token/Word)
        clean_text = re.sub(r'[#\*_\|`\~\[\]\(\)]', ' ', text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        return len(clean_text.split())

    def check_token_efficiency(self, markdown_text: str) -> float:
        """
        Token-to-Word Ratio (TWR).
        Mede a inflação do Espaço Latente (OCR sujo gasta muitos tokens).
        Quanto menor for o número (próximo de 1.0 a 1.5), melhor o RAG.
        Cenários de lixo/caracteres isolados podem jogar isso para 4.0+.
        """
        word_count = self._count_words(markdown_text)
        if word_count == 0:
            return 0.0
            
        token_count = len(self.encoder.encode(markdown_text))
        return token_count / word_count

    def check_orphan_chunks_rate(self, markdown_text: str) -> float:
        """
        Usa o Splitter do LangChain.
        Docs estruturados herdam metadados {"Header 1": "..."}.
        Mede a porcentagem de chunks (pedaços fatiados) que *não* possuem nenhum metadata de hierarquia.
        Docs sem Headers claros viram um bloco amorfo gigante.
        Quanto Menor a porcentagem de órfãos (0.0), melhor.
        """
        # Remove Frontmatter YAML block for pure text processing
        # if the file starts with it, as it breaks the first chunk header inheritance
        clean_for_split = markdown_text
        if clean_for_split.lstrip().startswith("---"):
            parts = clean_for_split.split("---", 2)
            if len(parts) >= 3:
                clean_for_split = parts[2].lstrip()
                
        splits = self.text_splitter.split_text(clean_for_split)
        if not splits:
            return 1.0 # 100% órfão / vazio
            
        orphan_count: float = 0.0
        total_chunks: float = float(len(splits))
        
        for chunk in splits:
            # Metadata contém os headers herdados
            if not getattr(chunk, "metadata", None):
                orphan_count += 1.0 # type: ignore
                
        return float(orphan_count / total_chunks) # type: ignore

    def check_ast_hierarchy_violations(self, markdown_text: str) -> int:
        """
        Gera a Árvore de Sintaxe Abstrata.
        Punições:
        - Pular de H1 pra H3 (Header Skipping).
        - Elementos HTML espúrios no bloco que deveriam ser Markdown.
        Retorna o número de "violações" no AST. Quanto mais próximo de 0, melhor.
        """
        tokens = self.md_parser.parse(markdown_text)
        
        violations = 0
        last_heading_level = 0
        
        for token in tokens:
            if token.type == 'heading_open':
                try:
                    level = int(token.tag.replace('h', ''))
                    # Pular do H1 direto pro H3 quebra hierarquia RAG
                    if last_heading_level != 0 and level > last_heading_level + 1:
                        violations += 1
                    last_heading_level = level
                except:
                    pass
            elif token.type == 'html_block':
                # HTML embutido sujo penaliza (já que o ideal é Markdown puro)
                # A menos que seja um de nossos Anchor controlados, mas vamos aplicar penalidade dura.
                if 'TABLE_ANCHOR' not in token.content:
                    violations += 1
                    
        return violations
        
    def check_frontmatter_validity(self, markdown_text: str) -> float:
        """
        Teste de Roteamento Determinístico (Frontmatter).
        Valida se o Markdown inicia com um bloco válido YAML (--- ... ---).
        Retorna 0.0 (Sem violações, válido) ou 1.0 (Inválido/Inexistente).
        Ideal para garantir extração de metadados padrão pelo orquestrador.
        """
        stripped_text = markdown_text.strip()
        if not stripped_text.startswith("---"):
            return 1.0
            
        parts = stripped_text.split("---")
        if len(parts) < 3:
            return 1.0 # Faltou fechamento do bloco
            
        yaml_content = parts[1]
        try:
            parsed = yaml.safe_load(yaml_content)
            if isinstance(parsed, dict) and len(parsed) > 0:
                return 0.0 # Válido e possui metadados (como title)
            return 1.0
        except Exception:
            return 1.0

    def evaluate(self, markdown_text: str) -> dict:
        """Roda a suíte completa de testes Determinísticos MLOps."""
        return {
            "Token_Word_Ratio": self.check_token_efficiency(markdown_text),
            "Orphan_Chunk_Rate": self.check_orphan_chunks_rate(markdown_text),
            "AST_Violations": self.check_ast_hierarchy_violations(markdown_text),
            "Frontmatter_Invalidity": self.check_frontmatter_validity(markdown_text)
        }
