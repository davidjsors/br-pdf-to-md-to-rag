import streamlit as st
import tempfile
import time
import markdown
from pathlib import Path

from src.parser import process_pdf
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
        with st.spinner('O Juiz está avaliando as extrações dos especialistas... ⚖️⚙️'):
            # Agora process_pdf retorna um dicionário com estatísticas do Ensemble
            result = process_pdf(file_path, output_dir)
                
        duration = time.time() - start_time
            
        if result.get("success"):
            md_path = result["md_path"]
            winner = result["winner"]
            ensemble_stats = result["stats"]
            
            if md_path.exists():
                with open(md_path, "r", encoding="utf-8") as f:
                    md_content = f.read()
                
                # Estatísticas
                num_chars = len(md_content)
                num_tables = md_content.count("| --- |")
                
                html_tags = extract_html_tags(markdown.markdown(normalize_math(md_content), extensions=['tables']))
                structural_density = min(100.0, float(len(html_tags)) * 1.5) if len(html_tags) > 0 else 0.0
                
                st.success(f"Concluído em {duration:.2f}s! ✨ Juiz escolheu: **{winner}**")
                
                # Layout de colunas para métricas (Visão Ensemble)
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Páginas PDF", ensemble_stats.get("total_pages", 0))
                m2.metric("Blocos de Texto", ensemble_stats.get("text_blocks_found", 0), help="Processados via MarkItDown.")
                m3.metric("Tabelas Injetadas", ensemble_stats.get("tables_identified", 0), help="Tabelas de alta precisão extraídas via pdfplumber.")
                m4.metric("Saúde Estrutural", f"{structural_density:.0f}%", help="Score MDEval: Riqueza de tags Markdown no arquivo final.")

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
                st.error("Erro interno: o arquivo MD não foi gerado.")
        else:
            st.error(f"Erro no processamento: {result.get('error', 'Erro desconhecido')}")
else:
    # Boas vindas/Placeholder
    st.info("Aguardando upload do PDF para aplicar o motor Ensemble... 🚀")
    st.image("https://img.icons8.com/clouds/200/000000/pdf.png")
