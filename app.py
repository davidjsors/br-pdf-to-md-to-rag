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

tab_prod, tab_arena = st.tabs(["🚀 Conversor (Produção)", "⚔️ Arena de Benchmark"])

with tab_prod:
    if uploaded_file is not None:
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
                    score = result.mdeval_score
                    
                    st.success(f"Concluído em **{duration:.2f}s**! ✨ Orquestração finalizada com sucesso.")
                    
                    # Layout de colunas para métricas (Visão Quantitativa + Qualitativa)
                    m1, m2, m3, m4 = st.columns(4)
                    
                    # Resumo Estatístico Requisitado pelo Usuário
                    m1.metric("Páginas Lidas", stats.get("total_pages", 0), help="Extensão detectada pelo Radar Espacial.")
                    m2.metric("Caracteres (Volume)", f"{len(md_content):,}", help="Volume bruto final do Markdown convertido.")
                    m3.metric("Tabelas/Imagens", f'{stats.get("tables_injected", 0)} / {stats.get("visual_blocks", 0)}', help="Matrizes e Fragmentos visuais consolidados.")
                    m4.metric("Saúde Estrutural", f"{score:.0f}%", help="Validação MDEval pelo Juiz Mestre (percentual de tags).")

                    st.info(f"🏆 **Motores Vencedores (Comitê):** Narrativa: `{stats.get('narrative_winner', 'N/A')}` | Matrizes: `{stats.get('data_winner', 'N/A')}` | Visão: `{stats.get('vision_winner', 'N/A')}`")

                    st.divider()
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("👀 Renderizado (Preview)")
                        with st.container(height=500, border=True):
                            st.markdown(md_content)
                    
                    with col2:
                        st.subheader("📝 Código Markdown")
                        with st.container(height=500, border=True):
                            st.code(md_content, language="markdown")
                    
                    # Download button
                    st.download_button(
                        label="Baixar Markdown Limpo 📥",
                        data=md_content,
                        file_name=md_path.name,
                        mime="text/markdown",
                        use_container_width=True,
                        type="primary"
                    )
                else:
                    st.error("Erro interno: o arquivo MD não foi salvo no servidor.")
            else:
                st.error(f"Erro Crítico do Orquestrador: {result.error}")
    else:
        # Boas vindas/Placeholder
        st.info("Aguardando upload do PDF para aplicar o motor Ensemble... 🚀")
        st.image("https://img.icons8.com/clouds/200/000000/pdf.png")

with tab_arena:
    st.subheader("Batalha de Ferramentas (Comparação)")
    
    st.markdown("""
    Esta arena testa o seu PDF nos motores isolados e em nosso **Comitê V2**, exibindo qual ferramenta lida melhor com o desafio.
    Nosso arsenal atual engloba 8 ferramentas independentes sendo orquestradas:
    """)
    
    st.markdown("""
    | Ferramenta | Etapa | Papel na aplicação |
    |---|---|---|
    | **unstructured** | Radar (0) | Identifica as coordenadas e delimita zonas (tabelas, parágrafos, imagens) para roteamento inteligente. |
    | **MarkItDown** | Narrativa (1) | Reconstrói o fluxo de texto primário preservando a semântica de cabeçalhos. |
    | **pymupdf4llm** | Narrativa (1) | Scanner secundário para garantir cobertura completa do texto e tapar buracos do primário. |
    | **docling** | Tabelas (2) | IA primária para semântica de matrizes complexas, células mescladas e ordem de dados. |
    | **pdfplumber** | Tabelas (2) | Validador geométrico secundário para garantir coordenadas matemáticas rígidas de caixas. |
    | **marker-pdf** | Visão (3) | IA pesada para transformar imagens escaneadas profundas em Markdown estruturado. |
    | **pytesseract** | Visão (3) | Contingência OCR secundária ultra-rápida (para impedir sobrecarga de VRAM). |
    | **MDEval** | Validação (4)| Auditor final matemático que converte e compara as tags estruturais injetadas. |
    """)
    
    # Removeremos o uploader separado e usaremos o global
    if uploaded_file is not None:
        if st.button("🥊 Iniciar Batalha de Benchmark neste Documento", type="primary"):
            from src.metrics.eval_metrics import StructuralDensityEvaluator
            from src.specialists.narrative_markitdown import extract_narrative_markitdown
            from src.specialists.narrative_pymupdf import extract_narrative_pymupdf
            import pandas as pd
            
            # Wrappers das IAs pesadas
            def run_docling(p):
                try:
                    from docling.document_converter import DocumentConverter
                    return DocumentConverter().convert(str(p)).document.export_to_markdown()
                except: return ""

            def run_marker(p):
                try:
                    from marker.convert import convert_single_pdf
                    from marker.models import load_all_models
                    full_text, _, _ = convert_single_pdf(str(p), load_all_models())
                    return full_text if full_text else ""
                except: return ""

            evaluator = StructuralDensityEvaluator()
            
            with tempfile.TemporaryDirectory() as temp_dir:
                file_path = Path(temp_dir) / uploaded_file.name
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                    
                resultados = []
                
                with st.spinner("⚔️ Roda 1/5: MarkItDown isolado..."):
                    t0 = time.time()
                    md1 = extract_narrative_markitdown(file_path)
                    resultados.append({"Motor": "MarkItDown (Microsoft)", "Tempo (s)": time.time()-t0, "Saúde Estrutural (%)": evaluator.evaluate(md1)})

                with st.spinner("⚔️ Roda 2/5: PyMuPDF4LLM isolado..."):
                    t0 = time.time()
                    md2 = extract_narrative_pymupdf(file_path)
                    resultados.append({"Motor": "PyMuPDF4LLM", "Tempo (s)": time.time()-t0, "Saúde Estrutural (%)": evaluator.evaluate(md2)})
                
                with st.spinner("⚔️ Roda 3/5: Docling (IA) isolado..."):
                    t0 = time.time()
                    md3 = run_docling(file_path)
                    resultados.append({"Motor": "Docling (IBM)", "Tempo (s)": time.time()-t0, "Saúde Estrutural (%)": evaluator.evaluate(md3)})
                    
                with st.spinner("⚔️ Roda 4/5: Marker-PDF (IA) isolado..."):
                    t0 = time.time()
                    md4 = run_marker(file_path)
                    resultados.append({"Motor": "Marker-PDF", "Tempo (s)": time.time()-t0, "Saúde Estrutural (%)": evaluator.evaluate(md4)})

                with st.spinner("🛡️ Roda 5/5: Comitê de Especialistas V2 (Orquestrador)"):
                    t0 = time.time()
                    res = process_pdf(file_path)
                    t_final = time.time()-t0
                    sc_final = res.mdeval_score if res.success else 0.0
                    resultados.append({"Motor": "👑 Comitê V2 (Orquestrado)", "Tempo (s)": t_final, "Saúde Estrutural (%)": sc_final})
                
                st.success("Batalha Finalizada!")
                
                df = pd.DataFrame(resultados)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Desempenho (Score MDEval - Maior é melhor)**")
                    st.bar_chart(df.set_index("Motor")["Saúde Estrutural (%)"], color="#2ecc71")
                
                with col2:
                    st.write("**Custo Computacional (Segundos - Menor é melhor)**")
                    st.bar_chart(df.set_index("Motor")["Tempo (s)"], color="#e74c3c")
                
                st.dataframe(df.style.highlight_max(subset=["Saúde Estrutural (%)"], color='lightgreen').highlight_min(subset=["Tempo (s)"], color='lightgreen'), use_container_width=True)

