# br-pdf-to-md-to-rag 🇧🇷📄

> Conversor especializado de PDFs governamentais, técnicos e empresariais brasileiros para Markdown limpo, estruturado e otimizado para uso em pipelines de RAG (Retrieval-Augmented Generation).

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://pdf2md2rag.streamlit.app/)

## O Problema que Resolvemos

Ferramentas generalistas (como Microsoft MarkItDown, PyMuPDF, pdf2image) abordam a conversão mapeando o conteúdo visual para o MD fielmente. O problema no cenário brasileiro é que documentos do SEBRAE, Receita Federal, diários oficiais e cartilhas técnicas geram uma base poluída com "lixo" fixo, causando **alucinações graves em modelos LLM**:

- ❌ Séries numéricas de eixos de gráficos (`1 2 3 ... 31`) interpretadas como dados reais.
- ❌ Escalas vazias (`R$ 0,00`) sendo tratadas como sendo contextos financeiros absolutos.
- ❌ Cabeçalhos e rodapés repetitivos, diluindo a densidade do texto ("chunking").
- ❌ Palavras separadas com hífens pela diagramação virando palavras desconexas.
- ❌ Tabelas textuais transformadas de forma amorfa e incompreensível para embeddings.

## ⚙️ A Solução: Arquitetura "Comitê de Especialistas V2"

Nossa abordagem não extrai tudo "assim como está". Nós utilizamos **8 ferramentas lideradas por 4 Juízes de IA** orquestradas sequencialmente para extrair e filtrar os dados perfeitos:

| Etapa | Juiz Responsável | Ferramentas (Motores) | Ação Principal |
|---|---|---|---|
| **0. Radar** | `Spatial Scanner` | `unstructured[pdf]` | Varre a página, identifica delimitadores e roteia blocos (imagens vs. tabelas vs. parágrafos). |
| **1. Narrativa** | `Narrative Judge` | `MarkItDown`, `pymupdf4llm` | Reconstrói a prosa primária, preservando títulos e pondo *âncoras* onde havia matrizes. |
| **2. Tabelas** | `Data Judge` | `docling`, `pdfplumber` | Extrai a semântica pesada de matrizes/células e garante coordenadas geométricas brutas. |
| **3. Visual** | `Vision Judge` | `marker-pdf`, `pytesseract` | Opcional: Processa páginas escaneadas puras através de Visão Computacional. |
| **4. Validação** | `Master Judge` | `MDEval` (Algoritmo) | Funde as tabelas da Etapa 2 dentro da Narrativa da Etapa 1. Calcula a **Saúde Estrutural** na métrica acadêmica e aprova. |

---

## 🚀 Quick Start (Usando na Web)

Acesse a nossa Interface Web (Hospedada no Streamlit Community Cloud gratuito):

👉 **[Acessar br-pdf-to-md-to-rag Online](https://pdf2md2rag.streamlit.app/)**

A interface possui duas abas:
1. **Conversor (Produção):** Suba seu PDF e receba o Markdown limpo e as métricas.
2. **Arena de Benchmark:** Teste o seu PDF em tempo real contra todas as ferramentas de mercado simultaneamente e veja gráficos provando quem extrai a melhor estrutura (Score MDEval).

---

## 💻 Instalação Local e Uso CLI

Se você quiser rodar localmente no seu computador ou servidor para automatizar massas de dados:

### 1. Clonar o projeto
```bash
git clone https://github.com/davidjsors/br-pdf-to-md-to-rag.git
cd br-pdf-to-md-to-rag
```

### 2. Escolher o Ambiente (Cuidado com o peso!)
A arquitetura V2 usa modelos de Inteligência Artificial potentes. Selecione a versão de requirements:

* **Modo HARDCORE (Recomendado / Nuvem):** Baixa o `docling`, `marker` etc. Requer vários GBs de download de modelos na primeira execução.
  ```bash
  python -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  ```

* **Modo LITE (Rápido / Fallback Local):** Instala apenas `MarkItDown` e `PyMuPDF`. O orquestrador detecta que não há IA visual, pula as IAs pesadas da IBM, usa as heurísticas locais e entrega resultado no melhor tempo possível.
  ```bash
  python -m venv .venv
  source .venv/bin/activate
  pip install -r requirements-lite.txt
  ```

### 3. Rodar Ferramenta CLI em Massa
Use o script CLI criado para conversões em lotes na esteira de dados RAG da sua empresa. Sem hardcodes.

```bash
# Converter apenas um arquivo
python cli.py caminho/para/documento.pdf -o resultados/

# Converter todos os arquivos de um diretório
python cli.py caminho/para/diretorio_com_pdfs/ -o resultados/
```

### 4. Subir a Interface Local
Para ter a experiência visual na sua rede local:
```bash
streamlit run app.py
```

---

## 🧩 Uso como Biblioteca Python (Modularizado)

Para times desenvolvendo outras bibliotecas que só querem alavancar a limpeza léxica PT-BR:

```python
from src.cleaner import clean_text_block

texto_sujo_do_SEBRAE = "O fluxo financeiro\ncon- tinuou operando as es-\ncalas\n1 2\n3 4 5\ncom ganhos de R$ 0,00"
texto_limpo = clean_text_block(texto_sujo_do_SEBRAE)

print(texto_limpo)
# Output: O fluxo financeiro continuou operando as escalas com ganhos de
```

Ou usando o Orquestrador Completo no seu código:
```python
from pathlib import Path
from src.orchestrator import process_pdf

resultado = process_pdf(Path("relatorio.pdf"))
if resultado.success:
    print(f"Nota de Qualidade Estrutural: {resultado.mdeval_score}%")
    print(resultado.final_markdown)
```

## 📚 Referências e Créditos
Este projeto integra métricas inspiradas no **MDEval-Benchmark**, que usamos no estágio de validação estrutural do Juiz Mestre. Agradecimentos ao grupo **SWUFE-DB-Group** (WWW '25).

## 📄 Licença
[MIT](LICENSE)
