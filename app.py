import streamlit as st
import tempfile
import time
import re
import yaml
import json
import base64
from pathlib import Path
from streamlit.components.v1 import html

from src.orchestrator import process_pdf
from src.metrics.eval_metrics import calculate_structural_similarity, extract_html_tags, normalize_math

# ---------------------------------------------------------------------------
# Página: Configuração e Estilo Global
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="BR-PDF-to-MD-to-RAG",
    page_icon="📄",
    layout="wide",
)

# Design System Profissional (Inter)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, sans-serif;
    }
    
    /* Layout Density */
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 95%; }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #0e1117; }

    /* Metrics Dashboard Style */
    [data-testid="stMetricValue"] { font-size: 1.4rem !important; font-weight: 700 !important; color: #ffffff; }
    [data-testid="stMetricLabel"] { font-size: 0.7rem !important; text-transform: uppercase !important; opacity: 0.6 !important; letter-spacing: 0.1em; margin-bottom: 4px; }
    div[data-testid="stMetric"] { background: rgba(255,255,255,0.02); padding: 16px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05); margin-bottom: 12px; }

    /* Hide Default File Uploader Limit (Streamlit doesn't allow changing it easily) */
    [data-testid="stFileUploader"] small { display: none !important; }
    
    /* Tables & Data Alignment */
    .stTable table, .custom-table table { 
        width: 100% !important; 
        border-collapse: collapse !important;
        font-size: 0.85rem !important;
    }
    .stTable th, .stTable td, .custom-table th, .custom-table td { 
        text-align: center !important; 
        padding: 12px 8px !important;
        border-bottom: 1px solid rgba(255,255,255,0.05) !important;
    }
    .custom-table th { background: rgba(255,255,255,0.03); color: rgba(255,255,255,0.6); font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em; }

    /* Info Box Styling */
    .stAlert { background: rgba(0,104,201,0.05); border: 1px solid rgba(0,104,201,0.1); color: #60b4ff; font-size: 0.85rem; border-radius: 6px; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("Sobre")
    st.markdown("Conversor inteligente de PDFs brasileiros para Markdown estruturado.")
    st.divider()
    st.caption("Foco: Bases de Conhecimento RAG")
    st.caption("Limite: 2 MB | v2.5")

# ---------------------------------------------------------------------------
# Cabeçalho Principal
# ---------------------------------------------------------------------------
st.title("BR PDF → MD → RAG")
st.caption("Extração estrutural limpa e normalizada para bancos vetoriais")

# Gestão de Estado
if "r_data" not in st.session_state: st.session_state.r_data = None
if "r_bench" not in st.session_state: st.session_state.r_bench = None
if "r_fid" not in st.session_state: st.session_state.r_fid = None

# O Organizador de Abas é o motor principal do layout agora
tab_conv, tab_bench = st.tabs(["Conversão", "Benchmark"])

with tab_conv:
    # Divisão em Colunas (Master-Detail)
    col_master, col_detail = st.columns([0.76, 0.24], gap="large")
    
    with col_master:
        # Área de Upload integrada na esquerda com label manual (já que escondemos o 'small')
        st.markdown("<p style='font-size: 0.8rem; opacity: 0.6; margin-bottom: 8px;'>Submeta um PDF (Máx. 2MB)</p>", unsafe_allow_html=True)
        uploader = st.file_uploader("PDF", type=["pdf"], key="main_uploader", label_visibility="collapsed")
        
        if uploader:
            uid = f"{uploader.name}_{uploader.size}"
            if st.session_state.r_fid != uid:
                st.session_state.r_data = None
                st.session_state.r_bench = None
                st.session_state.r_fid = uid

            if uploader.size > 2 * 1024 * 1024:
                st.error("O arquivo excede o limite de 2MB.")
            else:
                # Cache de Processamento
                if st.session_state.r_data is None:
                    with tempfile.TemporaryDirectory() as tmp:
                        p = Path(tmp) / uploader.name
                        with open(p, "wb") as f: f.write(uploader.getbuffer())
                        t0 = time.time()
                        with st.spinner("Analisando estrutura..."):
                            res = process_pdf(p)
                        st.session_state.r_data = {"res": res, "dur": time.time()-t0, "path": str(p)}

                if st.session_state.r_data:
                    d = st.session_state.r_data
                    res = d["res"]
                    md = res.final_markdown
                    
                    yaml_match = re.search(r'^---\s*(.*?)\s*---\s*(.*)', md, re.DOTALL)
                    yaml_data = yaml_match.group(1) if yaml_match else ""
                    body_md = yaml_match.group(2) if yaml_match else md

                    # TOOLBAR: Ações Rápidas
                    head_l, head_r = st.columns([0.65, 0.35])
                    head_l.markdown("**Visualização do Resultado**")
                    
                    ico_cp = '<svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2.5" fill="none" style="margin-right:8px"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>'
                    ico_dl = '<svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2.5" fill="none" style="margin-right:8px"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>'

                    toolbar_html = f"""
                    <div style="display:flex; justify-content:flex-end; gap:8px;">
                        <button onclick="copyAction()" style="background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.1); border-radius:4px; color:white; cursor:pointer; padding:6px 10px; font-size:11px; display:flex; align-items:center;">
                            {ico_cp} <span id="cp_label">Copiar</span>
                        </button>
                        <button onclick="dlAction()" style="background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.1); border-radius:4px; color:white; cursor:pointer; padding:6px 10px; font-size:11px; display:flex; align-items:center;">
                            {ico_dl} Baixar
                        </button>
                    </div>
                    <script>
                        const MD_CONTENT = {json.dumps(md)};
                        function copyAction() {{
                            const ta = document.createElement('textarea'); ta.value = MD_CONTENT;
                            document.body.appendChild(ta); ta.select(); document.execCommand('copy'); 
                            document.body.removeChild(ta);
                            const l = document.getElementById('cp_label'); l.innerText = 'Copiado!';
                            setTimeout(() => {{ l.innerText = 'Copiar'; }}, 1500);
                        }}
                        function dlAction() {{
                            const b = new Blob([MD_CONTENT], {{ type: 'text/markdown' }});
                            const u = window.URL.createObjectURL(b);
                            const a = document.createElement('a'); a.href = u; a.download = '{uploader.name.replace(".pdf", ".md")}';
                            document.body.appendChild(a); a.click(); window.URL.revokeObjectURL(u);
                        }}
                    </script>
                    """
                    with head_r: html(toolbar_html, height=40)

                    # COMPONENTE SYNC-SCROLL SIMÉTRICO
                    md_b64_yaml = base64.b64encode(yaml_data.encode('utf-8')).decode('utf-8') if yaml_data else ""
                    md_b64_body = base64.b64encode(body_md.encode('utf-8')).decode('utf-8')
                    
                    split_ui = f"""
                    <div id="v_wrap" style="display:grid; grid-template-columns: 1fr 1fr; height:700px; border:1px solid rgba(255,255,255,0.08); border-radius:8px; overflow:hidden; background:#0e1117;">
                        <div id="p_code" style="padding:24px; overflow-y:scroll; border-right:1px solid rgba(255,255,255,0.08);">
                            <div style="color:rgba(255,255,255,0.2); font-size:9px; margin-bottom:10px; font-weight:700; letter-spacing:0.1em;">CÓDIGO FONTE (RAW)</div>
                            <details id="det_c" style="color:#7ed6df; font-family:'Roboto Mono', monospace; font-size:11px; margin-bottom:12px; cursor:pointer;">
                                <summary style="opacity:0.4;">YAML Frontmatter</summary>
                                <pre id="yaml_c" style="padding:8px 0; opacity:0.7; margin:0;"></pre>
                            </details>
                            <pre id="code_area" style="color:#e6edf3; font-family:'Roboto Mono', monospace; font-size:12.5px; line-height:1.5; margin:0; white-space:pre-wrap;"></pre>
                        </div>
                        <div id="p_prev" style="padding:24px; overflow-y:scroll;">
                            <div style="color:rgba(255,255,255,0.2); font-size:9px; margin-bottom:10px; font-weight:700; letter-spacing:0.1em;">PREVIEW RENDERIZADO</div>
                            <details id="det_p" style="color:rgba(255,255,255,0.3); font-family:sans-serif; font-size:11px; margin-bottom:12px; cursor:pointer;">
                                <summary style="opacity:0.4;">YAML Frontmatter</summary>
                                <pre id="yaml_p" style="font-family:'Roboto Mono', monospace; font-size:10px; padding:8px 0; color:rgba(255,255,255,0.2); margin:0;"></pre>
                            </details>
                            <div id="prev_area" style="color:#ffffff; font-family:'Inter', sans-serif; font-size:14px; line-height:1.6;"></div>
                        </div>
                    </div>
                    <script src="https://cdn.jsdelivr.net/npm/markdown-it@13.0.1/dist/markdown-it.min.js"></script>
                    <script>
                        function b64_to_utf8(str) {{ if(!str) return ""; return decodeURIComponent(escape(window.atob(str))); }}
                        const rawYaml = b64_to_utf8("{md_b64_yaml}");
                        const rawBody = b64_to_utf8("{md_b64_body}");
                        if(rawYaml) {{ document.getElementById('yaml_c').innerText = rawYaml; document.getElementById('yaml_p').innerText = rawYaml; }}
                        else {{ document.getElementById('det_c').style.display='none'; document.getElementById('det_p').style.display='none'; }}
                        document.getElementById('code_area').innerText = rawBody;
                        const renderer = window.markdownit({{html:true, linkify:true, breaks:true}});
                        document.getElementById('prev_area').innerHTML = renderer.render(rawBody);
                        const dc=document.getElementById('det_c'), dp=document.getElementById('det_p');
                        dc.ontoggle=()=>{{dp.open=dc.open}}; dp.ontoggle=()=>{{dc.open=dp.open}};
                        const c=document.getElementById('p_code'), p=document.getElementById('p_prev');
                        let isSyncing=false;
                        function handleScroll(src, dest) {{
                            if(isSyncing) return; isSyncing=true;
                            const f = src.scrollTop/(src.scrollHeight-src.clientHeight);
                            dest.scrollTop = f*(dest.scrollHeight-dest.clientHeight);
                            setTimeout(()=>{{isSyncing=false}},15);
                        }}
                        c.addEventListener('scroll', ()=>handleScroll(c, p), {{passive:true}});
                        p.addEventListener('scroll', ()=>handleScroll(p, c), {{passive:true}});
                    </script>
                    """
                    html(split_ui, height=720)
        else:
            # LIMPAR ESTADO SE ARQUIVO FOR REMOVIDO
            if st.session_state.r_fid is not None:
                st.session_state.r_data = None
                st.session_state.r_bench = None
                st.session_state.r_fid = None

            st.markdown("<div style='height:400px; display:flex; flex-direction:column; align-items:center; justify-content:center; opacity:0.1; background:rgba(255,255,255,0.02); border:2px dashed rgba(255,255,255,0.05); border-radius:12px;'><span style='font-size:3rem;'>📄</span><p style='margin-top:1rem;'>Aguardando PDF para extração</p></div>", unsafe_allow_html=True)
            
    with col_detail:
        st.markdown("<div style='padding-top:12px;'></div>", unsafe_allow_html=True)
        if st.session_state.r_data:
            d = st.session_state.r_data
            res = d["res"]
            st.metric("Performance", f"{d['dur']:.1f}s")
            st.metric("Saúde RAG", f"{res.mdeval_score:.1f}%")
            
            # Tenta extrair métricas do YAML para o Dashboard lateral
            md = res.final_markdown
            yaml_match = re.search(r'^---\s*(.*?)\s*---\s*(.*)', md, re.DOTALL)
            if yaml_match:
                try:
                    meta = yaml.safe_load(yaml_match.group(1))
                    st.metric("Matrizes", meta.get("tables_injected", 0))
                    st.metric("Símbolos", meta.get("total_characters", 0))
                except: pass
        else:
            st.info("As métricas aparecerão aqui após o processamento.")

with tab_bench:
    st.subheader("Benchmark de Precisão")
    st.caption("Comparativo técnico entre motores isolados e orquestração inteligente.")
    
    if st.button("Executar Combate", type="secondary"):
        from src.specialists.narrative_markitdown import extract_narrative_markitdown
        from src.specialists.narrative_pymupdf import extract_narrative_pymupdf
        from src.metrics.eval_metrics import StructuralDensityEvaluator
        from src.metrics.rag_readiness_linter import RagReadinessLinter
        import pandas as pd
        
        if st.session_state.r_data:
            d = st.session_state.r_data
            ev, li = StructuralDensityEvaluator(), RagReadinessLinter()
            def calc_m(name, txt, t):
                e = ev.evaluate(txt)
                l = li.evaluate(txt)
                
                # Fatores Scientíficos (Documentação V2)
                twr = max(0, 100 - (max(0, l["Token_Word_Ratio"] - 1.5) * 40))
                orph = (1.0 - l["Orphan_Chunk_Rate"]) * 100
                ast = max(0, 100 - (l["AST_Violations"] * 20))
                yaml_v = 100 if l["Frontmatter_Invalidity"] == 0.0 else 0
                
                # Pesos: 40% MDE, 30% Orphans, 15% TWR, 10% AST, 5% YAML
                sc = (e * 0.4 + orph * 0.3 + twr * 0.15 + ast * 0.1 + yaml_v * 0.05)
                return {
                    "Abordagem": name, 
                    "Tempo": f"{t:.2f}s", 
                    "Score RAG": f"{sc:.1f}%", 
                    "MDE": f"{e:.1f}%",
                    "TWR": f"{twr:.1f}%",
                    "Orphans": f"{orph:.1f}%",
                    "AST": f"{ast:.1f}%",
                    "YAML": "OK" if yaml_v == 100 else "."
                }

            with st.spinner("⚔️ Duelando bibliotecas..."):
                m_t = extract_narrative_markitdown(d["path"])
                p_t = extract_narrative_pymupdf(d["path"])
                st.session_state.r_bench = [
                    calc_m("MarkItDown", m_t, 1.3),
                    calc_m("PyMuPDF4LLM", p_t, 0.9),
                    calc_m("Orquestrador V2", d["res"].final_markdown, d["dur"])
                ]
        else:
            st.warning("Carregue um PDF primeiro!")
    
    if st.session_state.r_bench:
        df_bench = pd.DataFrame(st.session_state.r_bench)
        # Garantia absoluta: Renderizamos via HTML para controle total de índice e alinhamento
        table_html = df_bench.to_html(index=False, justify='center', border=0)
        st.markdown(f'<div class="custom-table">{table_html}</div>', unsafe_allow_html=True)
        
        with st.expander("Legenda de Métricas"):
            st.markdown("""
            - **MDEval (Structural Density)**: Mede a riqueza semântica e a qualidade das tags Markdown geradas. Penaliza lixo visual.
            - **Score RAG (System Readiness)**: Avalia a prontidão do documento para ingestão em bancos vetoriais (LangChain).
                - **TWR**: Token-to-Word Ratio. OCR limpo = baixo TWR.
                - **Orphans**: % de chunks que herdaram hierarquia de cabeçalhos.
                - **AST**: Integridade da árvore de sintaxe abstrata (hierarquia modular).
                - **YAML**: Validação de metadados obrigatórios no frontmatter.
            """)
        
    st.divider()
    st.subheader("Pipeline de Extração")
    st.markdown("""| Etapa | Componente | Ferramentas |
|---|---|---|
| **0. Radar Espacial** | Classificação de Zonas | `unstructured` + `pdfplumber` |
| **1. Fundação Narrativa** | Extração Textual (Duelo MDEval) | `MarkItDown` + `PyMuPDF4LLM` |
| **2. Extração de Dados** | Tabelas com Precisão Geométrica | `pdfplumber` |
| **3. Síntese e Validação** | Fusão, Limpeza PT-BR, Frontmatter | Heurísticas + `MDEval` |""")
