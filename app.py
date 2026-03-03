import streamlit as st
import tempfile
import time
import markdown
from pathlib import Path

from src.orchestrator import process_pdf
from src.metrics.eval_metrics import calculate_structural_similarity, extract_html_tags, normalize_math

st.set_page_config(
    page_title="BR-PDF-to-MD-to-RAG", 
    page_icon="🇧🇷", 
    layout="wide"
)

# Sidebar - Sobre e Instruções
with st.sidebar:
    st.image("https://img.icons8.com/clippy/100/000000/cleaning-a-surface.png", width=100)
    st.title("Sobre o Projeto")
    st.markdown("""
    Este conversor foi criado para resolver o problema de **"lixo de layout"** em PDFs brasileiros.
    
    ### O que limpamos:
    - 🧹 **Página X de Y**: Removemos numeração de páginas automática.
    - 🧹 **Eixos de Gráficos**: Sequências numéricas que poluem o RAG.
    - 🧹 **Hifenização**: Reconstruímos palavras cortadas no fim da linha.
    - 🧹 **Cabeçalhos Repetidos**: Evitamos duplicidade de títulos.
    
    ### Métrica de Qualidade:
    Utilizamos métricas de densidade estrutural inspiradas no framework acadêmico **MDEval-Benchmark (WWW '25)**.
    
    ### Por que Markdown?
    Markdown é o formato ideal para **LLMs** e **Vector Databases**, pois preserva a estrutura (tabelas, títulos) sem o overhead visual do PDF.
    """)
    st.divider()
    st.info("Desenvolvido para a comunidade de IA do Brasil. 🇧🇷")

# Main Content
st.title("BR-PDF-to-MD-to-RAG 🇧🇷📄")
st.markdown("#### Conversor e Limpador de PDFs brasileiros para Markdown otimizado para RAG")

uploaded_file = st.file_uploader("Arraste ou selecione seu PDF aqui", type=["pdf"])

MAX_FILE_SIZE_MB = 1
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

if uploaded_file is not None:
    if uploaded_file.size > MAX_FILE_SIZE_BYTES:
        st.error(f"❌ O arquivo excede o limite de {MAX_FILE_SIZE_MB} MB. Por favor, envie um arquivo menor para garantir a estabilidade do processamento lite.")
    else:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            
            file_path = temp_dir_path / uploaded_file.name
            output_dir = temp_dir_path / "output"
            output_dir.mkdir(exist_ok=True)
            
            # Salvando arquivo enviado
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            start_time = time.time()
            with st.spinner("⏳ O Comitê de Especialistas v2 está analisando seu documento... (Radar, Narrativa, Tabelas, Visão e Juiz Mestre em execução)"):
                # Agora process_pdf retorna um OrchestratorResult
                result = process_pdf(file_path)
                
            duration = time.time() - start_time
                
            if result.success:
                md_content = result.final_markdown
                md_path = output_dir / (uploaded_file.name.replace(".pdf", "") + ".md")
                
                with open(md_path, "w", encoding="utf-8") as f:
                    f.write(md_content)
                    
                if md_path.exists():
                    stats = result.stats
                    score_orquestrador = result.mdeval_score
                    
                    # --- SEÇÃO 1: O MELHOR RESULTADO ---
                    st.subheader("1. Seu Markdown Otimizado (Resultado Final) 🏆")
                    st.success(f"Conversão concluída em **{duration:.2f}s** com o Comitê V2!")
                    
                    col1, col2 = st.columns(2)
                    
                    # Lógica para limpar o preview (remove YAML gigante)
                    import re
                    yaml_match = re.match(r'^---\s*(.*?)\s*---\s*(.*)', md_content, re.DOTALL)
                    if yaml_match:
                        yaml_data = yaml_match.group(1)
                        body_content = yaml_match.group(2)
                    else:
                        yaml_data = ""
                        body_content = md_content

                    with col1:
                        # Toolbar de Ações Customizada (Minimalista)
                        t_col, b_col1, b_col2 = st.columns([0.7, 0.1, 0.1])
                        t_col.markdown("**📝 Código Fonte**")
                        
                        # Botões de Ícone Compactos
                        # Nota: st.code já tem um botão de cópia nativo, mas colocamos este por redundância estética
                        b_col1.button("📋", help="Cópia rápida disponível no bloco", disabled=True)
                        b_col2.download_button(
                            label="📥",
                            data=md_content,
                            file_name=md_path.name,
                            mime="text/markdown",
                            help="Baixar Markdown RAG-Ready",
                        )
                        
                        with st.container(height=500, border=True):
                            st.code(md_content, language="markdown")
                    with col2:
                        st.markdown("**👀 Renderizado (Preview)**")
                        with st.container(height=500, border=True):
                            if yaml_data:
                                import yaml
                                try:
                                    meta = yaml.safe_load(yaml_data)
                                    # Cabeçalho Visual de Metadados
                                    st.markdown(f"#### {meta.get('title', 'Documento Extraído')}")
                                    m1, m2, m3 = st.columns(3)
                                    m1.metric("Score RAG", f"{meta.get('mdeval_score', 0)}%")
                                    m2.metric("Tabelas", meta.get('tables_injected', 0))
                                    m3.metric("Chars", meta.get('total_characters', 0))
                                    st.caption(f"📅 {meta.get('processing_date', '')} | 📂 {meta.get('source_file', 'N/A')}")
                                    st.divider()
                                except Exception:
                                    with st.expander("📊 Metadados Brutos"):
                                        st.code(yaml_data, language="yaml")
                            
                            st.markdown(body_content)
                            
                    st.divider()
                    
                    # --- SEÇÃO 2: OS BASTIDORES (BENCHMARK) ---
                    st.subheader("2. Os Bastidores: Por que este é o melhor resultado? 📊")
                    st.markdown("""
                    Nos bastidores, nosso **Orquestrador V2** executa múltiplas bibliotecas e aplica Heurísticas Brasileiras de Limpeza para evitar a poluição de Bancos Vetoriais (RAG).
                    Abaixo, testamos o seu documento agora mesmo nas bibliotecas puras (cruas) e compararmos a **Saúde Estrutural (MDEval)** delas com a nossa.
                    """)
                    
                    if st.button("🥊 Executar Comparação (Benchmark) neste Documento", type="secondary"):
                        from src.metrics.eval_metrics import StructuralDensityEvaluator
                        from src.specialists.narrative_markitdown import extract_narrative_markitdown
                        from src.specialists.narrative_pymupdf import extract_narrative_pymupdf
                        from src.metrics.rag_readiness_linter import RagReadinessLinter
                        import pandas as pd
                        
                        evaluator = StructuralDensityEvaluator()
                        linter = RagReadinessLinter()
                        
                        def build_metrics(motor, md_text, build_time):
                            eval_sc = evaluator.evaluate(md_text)
                            linter_sc = linter.evaluate(md_text)
                            
                            ocr = linter_sc["Orphan_Chunk_Rate"] * 100
                            twr = max(0, 100 - (max(0, linter_sc["Token_Word_Ratio"] - 1.5) * 40))
                            ast = max(0, 100 - (linter_sc["AST_Violations"] * 20))
                            fmt = 100 if linter_sc["Frontmatter_Invalidity"] == 0.0 else 0
                            
                            # Score Global RAG (100 pts)
                            score = (eval_sc * 0.40) + ((100 - ocr) * 0.30) + (twr * 0.15) + (ast * 0.10) + (fmt * 0.05)
                            
                            return {
                                "Motor": motor,
                                "Tempo (s)": build_time,
                                "SCORE RAG": score,
                                "MDE": eval_sc,
                                "OCR": ocr,
                                "TWR": linter_sc["Token_Word_Ratio"],
                                "AST": linter_sc["AST_Violations"],
                                "FMT": "❌" if linter_sc["Frontmatter_Invalidity"] else "✅"
                            }

                        resultados = []
                        
                        with st.spinner("⚔️ Roda 1/2: Testando MarkItDown isolado..."):
                            t0 = time.time()
                            md1 = extract_narrative_markitdown(file_path)
                            resultados.append(build_metrics("MarkItDown (puro)", md1, time.time() - t0))

                        with st.spinner("⚔️ Roda 2/2: Testando PyMuPDF4LLM isolado..."):
                            t0 = time.time()
                            md2 = extract_narrative_pymupdf(file_path)
                            resultados.append(build_metrics("PyMuPDF4LLM (puro)", md2, time.time() - t0))
                        
                        with st.spinner("🛡️ Construindo métricas do Orquestrador..."):
                            # Reaproveitamos o md e a duração
                            resultados.append(build_metrics("👑 Nosso Orquestrador V2", md_content, duration))
                        
                        df = pd.DataFrame(resultados)
                        
                        st.info("""**Qual é o diferencial dessa aplicação na prática?**  
                        Enquanto bibliotecas "cruas" focam apenas em copiar as palavras do documento, nosso Sistema atua como Engenheiro de Dados RAG. Nós computamos 5 variáveis MLOps simultâneas (avaliando Poluição Visual, Custo de Token da LLM e Estrutura Lógica) para gerar o **Score RAG Global de Prontidão**. Veja o detalhamento na tabela abaixo.
                        """)

                        # Tabela Simples
                        df_display = pd.DataFrame({
                            "Abordagem": [r["Motor"] for r in resultados],
                            "SCORE RAG": [f"🏆 {r['SCORE RAG']:.1f}" for r in resultados],
                            "MDE (%)": [f"{r['MDE']:.1f}%" for r in resultados],
                            "OCR (%)": [f"{r['OCR']:.1f}%" for r in resultados],
                            "TWR": [f"{r['TWR']:.2f}" for r in resultados],
                            "AST": [f"{r['AST']}" for r in resultados],
                            "FMT": [r["FMT"] for r in resultados]
                        })
                        st.table(df_display)
                        
                        st.caption("""
                        **📚 Legenda de Qualidade RAG:**  
                        **SCORE RAG:** Pontuação Final de Grau de Prontidão para Agentes LLM (0-100). Combinação ponderada das variáveis abaixo.  
                        **MDE (Densidade MDEval):** Estrutura da formatação visual (Tabelas e marcações sem lixo OCR). (Peso 40%).  
                        **OCR (Orphan Chunks):** Taxa de fragmentação vazando sem Metadados Hierárquicos. Ideal = 0%. (Peso 30%).  
                        **TWR (Token/Word):** Eficiência de Espaço Latente (quantos Tokens a IA gasta por Palavra real). Ideal é ~1.0 a 1.5. (Peso 15%).  
                        **AST (Violações de Árvore):** Saltos Ilógicos de títulos (H1 para H3) ou poluição via HTML Embutido inútil. (Peso 10%).  
                        **FMT (Frontmatter YAML):** Presença de metadados rígidos de roteamento no cabeçalho do arquivo global. (Peso 5%).
                        """)
                        
                        # Gráficos Didáticos
                        st.markdown("#### Matriz Visual de Impacto")
                        g1, g2, g3 = st.columns(3)
                        with g1:
                            st.markdown("**Pontuação SCORE RAG (0-100🏆)**")
                            st.bar_chart(df.set_index("Motor")["SCORE RAG"], color="#f1c40f")
                            st.caption("Visão Holística. O vencedor garante sucesso no Vector DB.")
                        
                        with g2:
                            st.markdown("**MDEval: Estrutura Visual (%)**")
                            st.bar_chart(df.set_index("Motor")["MDE"], color="#2ecc71")
                            st.caption("Capacidade de preservar matrizes sem vazar rodapés lixo.")

                        with g3:
                            st.markdown("**Custo Computacional (s)**")
                            st.bar_chart(df.set_index("Motor")["Tempo (s)"], color="#e74c3c")
                            st.caption("Esforço gasto unindo Heurísticas para o melhor arquivo.")
                            
                    st.divider()
                    
                    # --- SEÇÃO 3: DICIONÁRIO DE FERRAMENTAS LITE ---
                    st.subheader("🛠️ Dicionário de Ferramentas (Stack Lite)")
                    st.markdown("Nosso arsenal da versão *Padrão (Lite)* engloba 6 ferramentas independentes core:")
                    st.markdown("""
                    | Ferramenta | Etapa | Papel na aplicação |
                    |---|---|---|
                    | **unstructured** | Radar (0) | Identifica as coordenadas e mapeia páginas vazias/poluídas. |
                    | **MarkItDown** | Narrativa (1) | Reconstrói o fluxo de texto primário preservando a semântica de cabeçalhos. |
                    | **pymupdf4llm** | Narrativa (1) | Scanner secundário para garantir cobertura completa do texto e tapar buracos do primário. |
                    | **pdfplumber** | Tabelas (2) | Validador geométrico secundário para garantir matrizes lógicas em HTML. |
                    | **MDEval** | Validação (4)| Auditor final matemático que converte e nota tags estruturais injetadas. |
                    | **RagLinter** | RAG (5)| Módulo Analítico Heurístico que remove *Orphan Chunks* e injeta Root-YAMLs. |
                    """)
                else:
                    st.error("Erro interno: o arquivo MD não foi salvo no servidor.")
            else:
                st.error(f"Erro Crítico do Orquestrador: {result.error}")
else:
    # Boas vindas/Placeholder
    st.info("Faça o upload do PDF acima para aplicar o motor Ensemble e transformar o lixo em Dados! 🚀")
    st.image("https://img.icons8.com/clouds/200/000000/pdf.png")

