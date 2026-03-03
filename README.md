[🇺🇸 English](README.en.md) | 🇧🇷 Português

# Transforme PDF em Markdown otimizado para o seu RAG

Conversor de PDFs para Markdown estruturado, otimizado para ingestão em pipelines de RAG (Retrieval-Augmented Generation).

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://pdf2md2rag.streamlit.app/)

## Problema

Ferramentas genéricas de conversão PDF-para-Markdown produzem saídas que, quando aplicadas a determinados tipos de documentos, introduzem ruído estrutural que degrada a qualidade de embeddings e causa respostas incorretas em modelos LLM:

- Séries numéricas de eixos de gráficos interpretadas como dados reais.
- Escalas financeiras vazias  tratadas como contexto factual.
- Cabeçalhos e rodapés repetitivos diluindo a densidade semântica dos chunks.
- Palavras hifenizadas pela diagramação gerando tokens desconexos.
- Tabelas convertidas de forma amorfa, incompreensível para embeddings vetoriais.

## Arquitetura

O projeto utiliza uma pipeline de extração orquestrada em etapas sequenciais, onde cada componente é responsável por uma fase específica do processamento:

| Etapa | Componente | Ferramentas | Função |
|---|---|---|---|
| 0. Radar Espacial | `spatial_scanner` | `unstructured`, `pdfplumber` | Classifica as zonas de cada página (texto, tabela, imagem) e constrói o manifesto do documento. |
| 1. Fundação Narrativa | `narrative_judge` | `MarkItDown`, `PyMuPDF4LLM` | Extrai o fluxo textual primário. Avalia a saúde estrutural de ambos os motores via MDEval e seleciona o resultado com melhor pontuação. |
| 2. Extração de Dados | `data_judge` | `pdfplumber` | Extrai tabelas com precisão geométrica das páginas sinalizadas pelo Radar. |
| 3. Síntese e Validação | `master_judge` | Heurísticas customizadas | Funde tabelas no esqueleto narrativo, aplica filtros morfológicos PT-BR e injeta metadados YAML (frontmatter). |

> Documentação técnica detalhada em [docs/pipeline_architecture_v2.md](docs/pipeline_architecture_v2.md).

---

## Avaliador de Saúde Estrutural (MDEval)

O diferencial técnico deste projeto é o sistema de avaliação da qualidade do Markdown gerado, implementado em `src/metrics/eval_metrics.py`. Inspirado no paper __ 
[MDEval: Evaluating Markdown Awareness of Large Language Models](https://doi.org/10.48550/arXiv.2501.15000):

1. **HTMLifying:** O Markdown é renderizado como HTML temporário para separar o conteúdo textual do esqueleto estrutural (`<table>`, `<h1>`, `<ul>`).
2. **Pesos por Relevância RAG:** Tags de dados estruturados (`table`, `tr`, `td`) recebem peso 25. Listas (`ul`, `li`) recebem peso 10. Títulos (`h1`-`h6`) recebem peso 5. Tags de formatação (`b`, `i`, `strong`) recebem peso 1.
3. **Regra de Decaimento (D-Rule):** Tags cosméticas repetidas sofrem decaimento exponencial (γ=0.5), impedindo que extratores inflem a pontuação com formatação redundante. Tags de dados reais (tabelas, listas) acumulam linearmente.
4. **Penalidade de Lixo Visual:** Regex especializado em padrões brasileiros (numeração de página, réguas numéricas, `R$` consecutivos) reduz a pontuação de extratores que não filtram resíduos.

### RagReadiness Linter

Complementando o MDEval, o `src/metrics/rag_readiness_linter.py` executa verificações determinísticas:

- **Token-to-Word Ratio (TWR):** Mede a eficiência de tokenização. Valores próximos de 1.0-1.5 indicam texto limpo.
- **Orphan Chunk Rate:** Usa o `MarkdownHeaderTextSplitter` do LangChain para medir a porcentagem de chunks sem hierarquia de headers.
- **AST Hierarchy Violations:** Analisa a árvore de sintaxe abstrata via `markdown-it-py` para detectar saltos de hierarquia (H1→H3) e HTML embutido.
- **Frontmatter Validity:** Valida a presença e integridade do bloco YAML de metadados.

---

## Uso

### Interface Web

Acesse a interface hospedada no Streamlit Community Cloud:

**[pdf2md2rag.streamlit.app](https://pdf2md2rag.streamlit.app/)**

A interface possui duas abas:
1. **Conversão:** Upload de PDF e download do Markdown processado com métricas de qualidade.
2. **Benchmark:** Comparação em tempo real dos motores de extração com métricas detalhadas.

### Instalação Local

```bash
git clone https://github.com/davidjsors/br-pdf-to-md-to-rag.git
cd br-pdf-to-md-to-rag
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-lite.txt
```

### CLI

```bash
# Converter um arquivo
python cli.py caminho/para/documento.pdf -o resultados/

# Converter um diretório
python cli.py caminho/para/diretorio/ -o resultados/
```

### Interface Local

```bash
streamlit run app.py
```

### Uso como Biblioteca

```python
from src.cleaner import clean_text_block

texto_sujo = "O fluxo financeiro\ncon- tinuou operando as es-\ncalas\n1 2\n3 4 5"
texto_limpo = clean_text_block(texto_sujo)
```

```python
from pathlib import Path
from src.orchestrator import process_pdf

resultado = process_pdf(Path("relatorio.pdf"))
if resultado.success:
    print(f"Score MDEval: {resultado.mdeval_score}%")
    print(resultado.final_markdown)
```

## Dependências Principais

| Pacote | Função |
|---|---|
| `pdfplumber` | Radar geométrico e extração de tabelas |
| `markitdown` | Extração narrativa (esqueleto semântico) |
| `pymupdf4llm` | Extração narrativa (volume textual) |
| `unstructured` | Classificação semântica de zonas do PDF |
| `tiktoken` | Tokenização para cálculo de TWR |
| `langchain-text-splitters` | Splitting por headers para detecção de órfãos |
| `markdown-it-py` | Parser AST para validação de hierarquia |
| `beautifulsoup4` | Análise DOM para o avaliador MDEval |

## Referências

- MDEval-Benchmark ([SWUFE-DB-Group](https://github.com/SWUFE-DB-Group/MDEval-Benchmark)) — base teórica para o avaliador estrutural.

## Governança

Este repositório foi desenvolvido em par com agentes de IA.

## Licença

[MIT](LICENSE)
