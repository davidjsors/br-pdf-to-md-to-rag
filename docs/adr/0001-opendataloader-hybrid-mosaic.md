# ADR-0001: Adoção do OpenDataLoader-PDF (ODL) para Bounding Boxes e Parser Híbrido

## Status

Accepted

## Context

Historicamente, o `br-pdf-to-md-to-rag` orquestrava a biblioteca `unstructured` como "Radar Espacial" para identificar a presença de tabelas. Na Fase seguinte, o Juiz submetia o texto às bibliotecas de OCR concorrentes (`MarkItDown`, `PyMuPDF`) escolhendo a melhor saída por uma política implacável de "O Vencedor Leva Tudo" (*Winner Takes All*).

Isso causava um problema catastrófico de retenção de dados: Se a biblioteca vencedora apagasse silenciosamente 2 parágrafos inteiros devido a um erro algorítmico num OCR mal formatado, a nossa ferramenta deletava essa informação do Banco Vetorial, pois descartava a saída da biblioteca perdedora. Não era possível fundir trechos porque nenhuma delas devolvia coordenadas léxicas pareadas em JSON.

Além disso, tínhamos ferramentas pesadíssimas de Inteligência Artificial VLM (Vision Language Models, como `Docling`, `Marker` e `LlamaParse`) sugeridas no core, inviáveis de executar estritamente em CPU e Cloud Serverless gratuitos.

## Decision Drivers

* **Manter arquitetura Lite (CPU-Only)** para fácil deploy em clouds genéricas.
* **Preservar 100% da integridade da informação** evitando que OCRs falhos sumam com parágrafos.
* **Resolução Geométrica Cirúrgica** (XY coords) que viabilize o recorte exato do PDF para os Especialistas.

## Considered Options

### Option 1: MinerU / Marker / Docling
- **Pros**: Qualidade absoluta (State of the Art) para leitura matemática e layouts sujos.
- **Cons**: Exigem GPU, estouram a Memória RAM, baixam Gigabytes de dependências Torch/VLM. Quebram o viés gratuito da aplicação corporativa local.

### Option 2: pdf2md (Script heurístico simples)
- **Pros**: Super leve, rodando em regex puro.
- **Cons**: Destrói tabelas, funde colunas erradas e perde as complexidades estruturais.

### Option 3: OpenDataLoader-PDF (ODL)
- **Pros**: Retorna JSON riquíssimo com hierarquia inferida via algoritmo e `[bbox]` cirúrgicos para cada nó. Não usa Rede Neural Pesada. Roda liso no LangChain nativamente. Resolve o problema de células mescladas.
- **Cons**: Não "monta" o markdown para visualização humana out-of-the-box (demanda um novo parser construído por nós no backend).

## Decision

Nós vamos adotar o **OpenDataLoader-PDF (ODL)** acoplado estrategicamente à fase de Radar e ao Juiz de Decisão, e criaremos um conversor Nativo `json_to_md_parser` para absorvê-lo.

O modelo deixa de ser *"Winner Takes All"* e passa para a arquitetura de **"Comitê Mosaico Espacial"**:
O ODL extrai o JSON da página. O Orquestrador mapeia onde estão os Títulos (mandando recortes precisos do PDF para o `MarkItDown`) e onde estão Parágrafos e Tabelas (cruzando caixas vetoriais com `unstructured` e `pdfplumber`).

## Rationale

O ODL devolve Bounding Boxes. A matemática do *Bounding Box* permite fazer um Merge perfeito. Como sabemos *exatamente* em quais cordenadas um parágrafo habita na tela, podemos obrigar o MarkItDown só ler ali. Isso transforma as outras APIs de ferramentas de *Page-Extraction* em ferramentas de *Crop-Extraction*. 

A dependência `unstructured` é "rebaixada" apenas para Defesa Contra Imagens: Servirá de gatilho fallback exclusivo para alertar quando a página atual for um scanner puro, uma vez que o ODL e o PyMuPDF perdem controle total quando o texto está rasterizado e não vetorizado.

## Consequences

### Positive
- Garantia massiva (RAG-Ready Score quase 100%) contra remoção indesejada de texto no pipeline.
- Queda drástica de consumo de VRAM e processamento em nuvem.
- Lidaremos nativamente com PDFs de layouts complexos (3 colunas, revistas).

### Negative
- Aumento drástico na complexidade da lógica em Python do `narrative_judge.py` e do `spatial_scanner.py`.
- Nosso time precisa escrever um construtor recursivo em Python capaz de "montar" MarkDown iterando JSON em árvore originado do ODL.
