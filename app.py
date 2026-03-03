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
                tables_injected = stats.get("tables_injected", 0)
                
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
