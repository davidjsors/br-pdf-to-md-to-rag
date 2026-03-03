# Arquitetura da Pipeline de Extração — V2

Documentação técnica do fluxo de processamento do `br-pdf-to-md-to-rag`.

## Visão Geral

O documento PDF passa por uma pipeline de 4 etapas sequenciais. Cada etapa é implementada como um módulo independente (`src/judges/`) coordenado pelo orquestrador central (`src/orchestrator.py`).

```
PDF → Radar Espacial → Narrativa → Tabelas → Síntese → Markdown RAG-Ready
```

---

## Etapa 0: Radar Espacial

**Arquivo:** `src/radar/spatial_scanner.py`  
**Ferramentas:** `unstructured`, `pdfplumber`

O Radar analisa cada página do PDF e constrói um `DocumentManifest` contendo a classificação de zonas detectadas (texto, tabela, imagem, cabeçalho, rodapé).

**Orquestração complementar:** Cada motor contribui com sua especialidade:

| Motor | Especialidade | Contribuição |
|---|---|---|
| `unstructured` | Classificação semântica | Identifica o **tipo** de cada elemento (NarrativeText, Table, Image, Title) via análise de layout. |
| `pdfplumber` | Precisão geométrica | Enriquece o manifesto com **bounding boxes** e detecta tabelas/imagens nativas não capturadas. |

**Fluxo de execução:**
1. O `unstructured` processa o PDF e classifica semanticamente cada zona da página.
2. O `pdfplumber` percorre as mesmas páginas e adiciona dados geométricos (coordenadas de imagens, detecção nativa de tabelas) ao manifesto já classificado.
3. Se o `unstructured` não estiver disponível, o `pdfplumber` opera isoladamente no modo geométrico.

**Decisão de roteamento:** O manifesto resultante informa às etapas seguintes quais páginas contêm tabelas (acionando o Juiz de Dados) e quais contêm imagens.

---

## Etapa 1: Fundação Narrativa

**Arquivo:** `src/judges/narrative_judge.py`  
**Ferramentas:** `MarkItDown`, `PyMuPDF4LLM`  
**Especialistas:** `src/specialists/narrative_markitdown.py`, `src/specialists/narrative_pymupdf.py`

O Juiz Narrativo executa dois motores de extração em paralelo e seleciona o resultado com melhor saúde estrutural.

**Funcionamento:**
1. Executa `MarkItDown` e `PyMuPDF4LLM` sobre o PDF.
2. Submete ambas as saídas ao avaliador MDEval (`src/metrics/eval_metrics.py`).
3. Seleciona o motor com maior pontuação de saúde estrutural.
4. Em caso de empate (ambos com score 0), desempata por volume de texto.
5. Insere âncoras posicionais (`<!-- TABLE_ANCHOR_pX_tY -->`) nos pontos onde o Radar detectou tabelas.

**Saída:** Esqueleto narrativo com marcadores de posição para injeção posterior de tabelas.

---

## Etapa 2: Extração de Tabelas

**Arquivo:** `src/judges/data_judge.py`  
**Ferramentas:** `pdfplumber`  
**Especialista:** `src/specialists/table_plumber.py`

O Juiz de Dados extrai tabelas com precisão geométrica.

**Funcionamento:**
1. Itera sobre todas as páginas do PDF usando `pdfplumber`.
2. Detecta tabelas nativas via `page.find_tables()`.
3. Converte cada tabela para Markdown formatado via `src/formatter.py`.
4. Retorna a lista de tabelas em formato Markdown para injeção na Etapa 3.

---

## Etapa 3: Síntese e Validação

**Arquivo:** `src/judges/master_judge.py`  
**Ferramentas:** Heurísticas customizadas, `src/cleaner.py`

O Juiz Mestre consolida os resultados de todas as etapas anteriores.

**Funcionamento:**
1. **Injeção de tabelas:** Substitui as âncoras `<!-- TABLE_ANCHOR_pX_tY -->` no esqueleto narrativo pelas tabelas Markdown extraídas na Etapa 2. Cada tabela recebe um header (`### [Tabela Detectada]`) para evitar chunks órfãos no RAG.
2. **Filtros morfológicos:** Aplica o `clean_text_block()` para remover lixo visual específico de documentos brasileiros (numeração de página, hifenização, séries numéricas, escalas vazias).
3. **Validação MDEval:** Submete o resultado final ao avaliador de saúde estrutural.
4. **Frontmatter YAML:** Injeta um bloco de metadados no topo do documento contendo título, data de processamento, score MDEval, contagem de tabelas e blocos visuais.

---

## Sistema de Métricas

### MDEval (Avaliador de Saúde Estrutural)

**Arquivo:** `src/metrics/eval_metrics.py`

Avaliador Reference-Free que converte Markdown para HTML e analisa a densidade e qualidade das tags estruturais. Utiliza regra de decaimento exponencial para tags cosméticas e acumulação linear para tags de dados (tabelas, listas). Aplica penalidades por padrões de lixo visual brasileiros.

### RagReadiness Linter

**Arquivo:** `src/metrics/rag_readiness_linter.py`

Validador determinístico que mede:
- **TWR (Token-to-Word Ratio):** Eficiência de tokenização via `tiktoken`.
- **Orphan Chunk Rate:** Proporção de chunks sem hierarquia via `langchain-text-splitters`.
- **AST Violations:** Violações de hierarquia de headers via `markdown-it-py`.
- **Frontmatter Validity:** Integridade do bloco YAML via `pyyaml`.

---

## Limpeza Léxica PT-BR

**Arquivo:** `src/cleaner.py`

Módulo de heurísticas para remoção de artefatos específicos de documentos brasileiros:
- Reunião de palavras hifenizadas pela diagramação (`con-\ntinuou` → `continuou`).
- Remoção de séries numéricas de eixos de gráficos.
- Filtragem de cabeçalhos/rodapés repetitivos.
- Remoção de escalas financeiras vazias.

---

## Estrutura de Diretórios

```
src/
├── orchestrator.py          # Coordenador central da pipeline
├── cleaner.py               # Filtros morfológicos PT-BR
├── formatter.py             # Conversor tabela → Markdown
├── models.py                # Modelos de dados (Manifesto, Zonas, Resultados)
├── radar/
│   └── spatial_scanner.py   # Classificação de zonas (Etapa 0)
├── judges/
│   ├── narrative_judge.py   # Seleção de motor narrativo (Etapa 1)
│   ├── data_judge.py        # Extração de tabelas (Etapa 2)
│   ├── vision_judge.py      # Processamento visual (reservado)
│   └── master_judge.py      # Síntese final (Etapa 3)
├── specialists/
│   ├── narrative_markitdown.py  # Extrator MarkItDown
│   ├── narrative_pymupdf.py     # Extrator PyMuPDF4LLM
│   └── table_plumber.py        # Extrator pdfplumber
└── metrics/
    ├── eval_metrics.py          # Avaliador MDEval
    └── rag_readiness_linter.py  # Linter RAG determinístico
```
