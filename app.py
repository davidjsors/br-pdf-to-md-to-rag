import streamlit as st
import tempfile
from pathlib import Path

from src.parser import process_pdf

st.set_page_config(
    page_title="BR-PDF-to-MD-to-RAG", 
    page_icon="🇧🇷", 
    layout="wide"
)

st.title("BR-PDF-to-MD-to-RAG 🇧🇷📄")
st.subheader("Conversor e Limpador de PDFs brasileiros para Markdown otimizado para RAG")

st.markdown("""
Faça upload de um PDF com layouts "problemáticos" (como editais, tabelas do SEBRAE, Notas Fiscais, cartilhas). 
Nossa ferramenta irá higienizar ruídos (eixos repetidos de gráficos, quebras de hifenização invisíveis, cabeçalhos das páginas) e te retornar Markdown limpo pra você injetar no seu Vector DB/RAG.
""")

uploaded_file = st.file_uploader("Envie seu arquivo PDF", type="pdf")

if uploaded_file is not None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        pdf_path = temp_dir_path / uploaded_file.name
        output_dir = temp_dir_path / "output"
        output_dir.mkdir(exist_ok=True)
        
        # Salvando PDF envidado no diretório temporário
        with open(pdf_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        with st.spinner('Lendo PDFs, sanitizando "lixo de layout" e gerando tabelas MD... 🧹⚙️'):
            success = process_pdf(pdf_path, output_dir)
            
        if success:
            md_filename = pdf_path.stem + ".md"
            md_path = output_dir / md_filename
            
            if md_path.exists():
                with open(md_path, "r", encoding="utf-8") as f:
                    md_content = f.read()
                
                st.success("Conversão e Limpeza concluídas com sucesso! ✨")
                
                # Exibir colunas com Resultados (Renderizado vs Código Bruto)
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### Markdown Renderizado")
                    with st.container(height=600):
                        st.markdown(md_content)
                    
                with col2:
                    st.markdown("### Código Markdown Puro")
                    with st.container(height=600):
                        st.code(md_content, language="markdown")
                
                # Botão de download
                st.download_button(
                    label="📥 Baixar arquivo Markdown (.md) Otimizado",
                    data=md_content,
                    file_name=md_filename,
                    mime="text/markdown"
                )
            else:
                st.error("Erro interno. O arquivo MD não foi gerado no diretório temporário.")
        else:
            st.error("Falha na interpretação e conversão do PDF.")
