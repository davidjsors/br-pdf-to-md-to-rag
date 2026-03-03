🇺🇸 English | [🇧🇷 Português](README.md)

# br-pdf-to-md-to-rag

Converter for Brazilian PDFs (government, technical, and corporate documents) to structured Markdown, optimized for ingestion into RAG (Retrieval-Augmented Generation) pipelines.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://pdf2md2rag.streamlit.app/)

## Problem

Generic PDF-to-Markdown tools produce outputs that, when applied to typical Brazilian documents (SEBRAE, Federal Revenue Service, official gazettes), introduce structural noise that degrades embedding quality and causes incorrect LLM responses:

- Chart axis number series interpreted as actual data.
- Empty financial scales (`R$ 0.00`) treated as factual context.
- Repetitive headers and footers diluting the semantic density of chunks.
- Hyphenated words from typesetting generating disconnected tokens.
- Tables converted into amorphous formats, incomprehensible for vector embeddings.

## Architecture

The project uses a sequentially orchestrated extraction pipeline, where each component is responsible for a specific processing phase:

| Stage | Component | Tools | Function |
|---|---|---|---|
| 0. Spatial Radar | `spatial_scanner` | `unstructured`, `pdfplumber` | Classifies zones on each page (text, table, image) and builds the document manifest. |
| 1. Narrative Foundation | `narrative_judge` | `MarkItDown`, `PyMuPDF4LLM` | Extracts the primary text flow. Evaluates the structural health of both engines via MDEval and selects the result with the best score. |
| 2. Data Extraction | `data_judge` | `pdfplumber` | Extracts tables with geometric precision from pages flagged by the Radar. |
| 3. Synthesis & Validation | `master_judge` | Custom heuristics | Merges tables into the narrative skeleton, applies morphological filters, and injects YAML metadata (frontmatter). |

> Detailed technical documentation at [docs/pipeline_architecture_v2.md](docs/pipeline_architecture_v2.md).

---

## Structural Health Evaluator (MDEval)

The core technical differentiator of this project is the Markdown quality evaluation system, implemented in `src/metrics/eval_metrics.py`. Inspired by the paper _MDEval: Evaluating Markdown Awareness of Large Language Models_ (SWUFE-DB-Group, WWW '25), the evaluator operates without a reference ground truth (Reference-Free):

1. **HTMLifying:** The Markdown is rendered as temporary HTML to separate textual content from the structural skeleton (`<table>`, `<h1>`, `<ul>`).
2. **RAG-Relevance Weights:** Structured data tags (`table`, `tr`, `td`) receive a weight of 25. Lists (`ul`, `li`) receive a weight of 10. Headings (`h1`-`h6`) receive a weight of 5. Formatting tags (`b`, `i`, `strong`) receive a weight of 1.
3. **Decay Rule (D-Rule):** Repeated cosmetic tags undergo exponential decay (γ=0.5), preventing extractors from inflating scores with redundant formatting. Real data tags (tables, lists) accumulate linearly.
4. **Visual Garbage Penalty:** Specialized regex patterns for Brazilian documents (page numbering, numeric rulers, consecutive `R$`) reduce the score of extractors that fail to filter residues.

### RagReadiness Linter

Complementing MDEval, `src/metrics/rag_readiness_linter.py` performs deterministic checks:

- **Token-to-Word Ratio (TWR):** Measures tokenization efficiency. Values near 1.0-1.5 indicate clean text.
- **Orphan Chunk Rate:** Uses LangChain's `MarkdownHeaderTextSplitter` to measure the percentage of chunks without header hierarchy.
- **AST Hierarchy Violations:** Analyzes the abstract syntax tree via `markdown-it-py` to detect hierarchy jumps (H1→H3) and embedded HTML.
- **Frontmatter Validity:** Validates the presence and integrity of the YAML metadata block.

---

## Usage

### Web Interface

Access the interface hosted on Streamlit Community Cloud:

**[pdf2md2rag.streamlit.app](https://pdf2md2rag.streamlit.app/)**

The interface has two tabs:
1. **Conversion:** Upload a PDF and download the processed Markdown with quality metrics.
2. **Benchmark:** Real-time comparison of extraction engines with detailed metrics.

### Local Installation

```bash
git clone https://github.com/davidjsors/br-pdf-to-md-to-rag.git
cd br-pdf-to-md-to-rag
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-lite.txt
```

### CLI

```bash
# Convert a single file
python cli.py path/to/document.pdf -o output/

# Convert a directory
python cli.py path/to/directory/ -o output/
```

### Local Interface

```bash
streamlit run app.py
```

### Library Usage

```python
from src.cleaner import clean_text_block

dirty_text = "O fluxo financeiro\ncon- tinuou operando as es-\ncalas\n1 2\n3 4 5"
clean_text = clean_text_block(dirty_text)
```

```python
from pathlib import Path
from src.orchestrator import process_pdf

result = process_pdf(Path("report.pdf"))
if result.success:
    print(f"MDEval Score: {result.mdeval_score}%")
    print(result.final_markdown)
```

## Core Dependencies

| Package | Function |
|---|---|
| `pdfplumber` | Geometric radar and table extraction |
| `markitdown` | Narrative extraction (semantic skeleton) |
| `pymupdf4llm` | Narrative extraction (text volume) |
| `unstructured` | Semantic zone classification of PDF pages |
| `tiktoken` | Tokenization for TWR calculation |
| `langchain-text-splitters` | Header-based splitting for orphan detection |
| `markdown-it-py` | AST parser for hierarchy validation |
| `beautifulsoup4` | DOM analysis for the MDEval evaluator |

## References

- MDEval-Benchmark (SWUFE-DB-Group, WWW '25) — theoretical basis for the structural evaluator.

## Governance

This repository is developed in pair with AI agents. Infrastructure rule: no autonomous agent is authorized to execute `git commit` or `git push` without explicit permission from the responsible engineer.

## License

[MIT](LICENSE)
