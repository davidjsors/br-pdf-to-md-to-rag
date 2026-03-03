# br-pdf-to-md-to-rag

Conversor especializado de PDFs governamentais, técnicos e empresariais brasileiros para Markdown limpo, estruturado e otimizado para uso em pipelines de RAG (Retrieval-Augmented Generation).

## O Problema que Resolvemos

Ferramentas generalistas abordam a conversão mapeando o conteúdo visual para o MD fielmente (como o Microsoft MarkItDown, PyMuPDF, pdf2image). O problema disso para o cenário brasileiro é que documentos do SEBRAE, Receita Federal, diários oficiais e cartilhas técnicas geram uma base poluída com "lixo" fixo, que frequentemente causa **alucinações graves em modelos LLM**:

- ❌ Séries numéricas de eixos de gráficos (ex: `1 2 3 ... 31`) interpretadas como dados reais no contexto.
- ❌ Escalas de preços vazias (`R$ 0,00`, ou até repetitivos `R$`) alimentadas como sendo contextos financeiros absolutos.
- ❌ Cabeçalhos e rodapés repetitivos em todas as páginas, poluindo a densidade do texto ("chunking").
- ❌ Palavras separadas com hífens pela quebra na diagramação de páginas virando palavras desconexas no banco vetorial.
- ❌ Tabelas textuais transformadas de forma amorfa e incompreensível para embeddings.

## Nossa Solução USP (Unique Selling Proposition)

O **BR-PDF-to-MD** não extrai tudo "assim como está", mas sim aplicando uma camada super densa de limpeza (**cleaner semantic**) voltada unicamente à **sanitização em português pt-BR**.

## ⚖️ O Comitê de Especialistas (Arquitetura de Orquestração v2)

Em vez de depender de um único motor, utilizamos **8 ferramentas lideradas por 4 Juízes** em etapas sequenciais:

1.  **Fase 0 (Radar)**: O *unstructured* varre a página e identifica as posições de parágrafos, tabelas e imagens.
2.  **Etapa 1 (Narrativa)**: *MarkItDown* e *pymupdf4llm* reconstroem a prosa e a hierarquia de títulos. O Juiz Narrativo insere *âncoras* onde havia tabelas.
3.  **Etapa 2 (Tabelas)**: *docling* (IBM) entende a semântica pesada das matrizes, enquanto o *pdfplumber* garante a precisão das coordenadas BR. (Só acionado se o Radar detectar tabelas).
4.  **Etapa 3 (Visual)**: *marker-pdf* usa IA pesada para transformar layouts de imagem em Markdown, com *Tesseract OCR* como fallback rápido. (Só acionado se houver blocos de imagem).
5.  **Etapa 4 (Síntese e Validação)**: O **Juiz Mestre** junta tudo. Ele substitui as âncoras da Etapa 1 pelas Tabelas da Etapa 2, aplica regras de filtragem BR (`cleaner.py`) e roda **obrigatoriamente** o algoritmo **MDEval** para aprovar a Saúde Estrutural final.
---

## 🌐 Como Acessar a Interface Web (Demo ao Vivo)

Para você que quer usar a ferramenta sem instalar nada:

[ ![Abra no Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg) ](https://pdf2md2rag.streamlit.app/)

> **Nota:** Este app está hospedado no [Streamlit Community Cloud](https://streamlit.io/cloud). A hospedagem para projetos open-source é **gratuita**.

## 💻 Instalação Local e CLI

```bash
git clone https://github.com/davidjsors/br-pdf-to-md-to-rag.git
cd br-pdf-to-md-to-rag
pip install -r requirements.txt
```

## Como Usar a Ferramenta CLI

Você pode extrair arquivos definidos, ou rodar por diretório via CLI `argparse`. Não há mais "caminhos hardcore no código"!

```bash
# Converter apenas um arquivo PDF
python cli.py caminho/para/documento.pdf -o resultados/

# Converter todos os arquivos PDF de um diretório
python cli.py caminho/para/diretorio_com_pdfs/ -o resultados/
```

## 🌐 Interface Web (Web App)

Criamos uma interface visual para os usuários subirem seus PDFs no navegador de forma simples e compararem o **render visual do Markdown** com o seu **código bruto** extraído, ambos já livres do lixo do documento.

Basta rodar na pasta raiz do projeto:

```bash
streamlit run app.py
```

O seu navegador padrão abrirá a plataforma (em geral, na porta `localhost:8501`).

## Como Usar Como Biblioteca (Modularizado)

Para times que desenvolvem bibliotecas ou outros pipelines de extração, importando somente sua lógica de tratamento.

```python
from src.cleaner import clean_text_block

texto_sujo_do_SEBRAE = "O fluxo financeiro\ncon- tinuou operando as es-\ncalas\n1 2\n3 4 5\ncom ganhos de R$ 0,00"
texto_limpo = clean_text_block(texto_sujo_do_SEBRAE)

print(texto_limpo)
# Output: O fluxo financeiro continuou operando as escalas com ganhos de
```

### Contribuindo

Pull requests são super bem-vindos. Fique à vontade para submeter suas heurísticas `regex` pra filtrar ainda mais casos "exóticos" dos PDFs de cartilhas contábeis BR.

## Referências e Créditos

Este projeto integra heurísticas e métricas inspiradas no **MDEval-Benchmark**, um framework acadêmico para avaliar a consciência de Markdown em LLMs.

**Citação Original:**
```bibtex
@inproceedings{chen2025mdeval,
  title={MDEval: Evaluating and Enhancing Markdown Awareness in Large Language Models},
  author={Zhongpu Chen and Yinfeng Liu and Long Shi and Zhi-Jie Wang and Xingyan Chen and Yu Zhao and Fuji Ren},
  booktitle={Proceedings of the ACM Web Conference},
  year={2025}
}
```

Agradecemos ao grupo **SWUFE-DB-Group** pelo compartilhamento do benchmark [MDEval](https://github.com/SWUFE-DB-Group/MDEval-Benchmark).

## Licença
[MIT](LICENSE)
