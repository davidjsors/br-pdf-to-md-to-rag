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

- ✅ **Limpador de Eixos e Escalas:** Regex calibrado para detectar e remover irrelevâncias estruturais que são muito comuns em pdfs.
- ✅ **Sanitização Semântica pt-BR:** Repara união de palavras que foram cortadas pelo design e faz o "glue" de frases quebradas no meio.
- ✅ **Extração Integrada Tabela-para-Markdown:** O contexto tabular mantém seus grids originais extraídas via *pdfplumber*.
- ✅ **Modular (Limpador "Standalone"):** Você já possui seu pipeline de parser? Ok! Utilize apenas `cleaner` puxando a camada de sanitização das strings e pronto.

---

## 🌐 Como Acessar a Interface Web (Demo ao Vivo)

Para você que quer usar a ferramenta sem instalar nada:

[ ![Abra no Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg) ](https://share.streamlit.io/)

> **Nota:** Se você for o dono do repo, basta conectar seu GitHub ao [Streamlit Community Cloud](https://streamlit.io/cloud) e apontar para o arquivo `app.py`. A hospedagem para projetos open-source é **gratuita**.

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

## Licença
[MIT](LICENSE)
