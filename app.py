import streamlit as st
import tempfile
import time
from pathlib import Path

from src.parser import process_pdf

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
    
    ### Por que Markdown?
    Markdown é o formato ideal para **LLMs** e **Vector Databases**, pois preserva a estrutura (tabelas, títulos) sem o overhead visual do PDF.
    """)
    st.divider()
    st.info("Desenvolvido para a comunidade de IA do Brasil. 🇧🇷")

# Main Content
st.title("BR-PDF-to-MD-to-RAG 🇧🇷📄")
st.markdown("#### Conversor e Limpador de PDFs brasileiros para Markdown otimizado para RAG")

uploaded_file = st.file_uploader("Arraste ou selecione seu PDF aqui", type="pdf")

if uploaded_file is not None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        pdf_path = temp_dir_path / uploaded_file.name
        output_dir = temp_dir_path / "output"
        output_dir.mkdir(exist_ok=True)
        
        # Salvando PDF enviado
        with open(pdf_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        start_time = time.time()
        with st.spinner('Limpando ruídos e estruturando Markdown... 🧹⚙️'):
            success = process_pdf(pdf_path, output_dir)
        duration = time.time() - start_time
            
        if success:
            md_filename = pdf_path.stem + ".md"
            md_path = output_dir / md_filename
            
            if md_path.exists():
                with open(md_path, "r", encoding="utf-8") as f:
                    md_content = f.read()
                
                # Estatísticas simples
                num_chars = len(md_content)
                num_tables = md_content.count("| --- |") # Heurística simples
                
                st.success(f"Concluído em {duration:.2f}s! ✨")
                
                # Layout de colunas para métricas
                m1, m2, m3 = st.columns(3)
                m1.metric("Caracteres extraídos", f"{num_chars:,}")
                m2.metric("Tabelas identificadas", num_tables)
                m3.metric("Status", "Limpo 🧹")

                st.divider()
                
                # Exibir colunas com Resultados
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### 👀 Renderizado (Preview)")
                    with st.container(height=500, border=True):
                        st.markdown(md_content)
                    
                with col2:
                    st.markdown("### 📝 Código Markdown")
                    with st.container(height=500, border=True):
                        st.code(md_content, language="markdown")
                
                st.divider()
                
                # Botão de download de destaque
                st.download_button(
                    label="📥 Baixar Markdown (.md) Otimizado",
                    data=md_content,
                    file_name=md_filename,
                    mime="text/markdown",
                    use_container_width=True,
                    type="primary"
                )
            else:
                st.error("Erro interno: o arquivo MD não foi gerado.")
        else:
            st.error("Falha na interpretação e conversão do PDF.")
else:
    # Boas vindas/Placeholder
    st.info("Aguardando upload de arquivo PDF para iniciar a limpeza...")
    st.image("https://img.icons8.com/clouds/200/000000/pdf.png")
