"""
Juiz Mestre — Etapa 4 (Síntese e Validação).
Pega o Esqueleto Narrativo (com âncoras), injeta as Tabelas (Docling/Plumber),
acopla Fragmentos Visuais (Marker/Tesseract) e valida no MDEval.
"""
from src.models import StageResult, OrchestratorResult
from src.cleaner import clean_text_block
from src.metrics.eval_metrics import StructuralDensityEvaluator
import re

def synthesize_master(
    narrative_res: StageResult, 
    data_res: StageResult, 
    vision_res: StageResult
) -> OrchestratorResult:
    """
    Consolidador Universal da Arquitetura.
    """
    print("[Juiz Mestre] Iniciando Processo de Síntese Final...")
    master_text = narrative_res.content

    # 1. Substituição de Âncoras Espaciais por Tabelas de Alta Precisão
    # Na Etapa 1 as âncoras foram injetadas como <!-- TABLE_ANCHOR_pX_tY -->
    # O regex ajuda a achar as âncoras na ordem em que aparecem no fluxo linear
    tables_to_inject = data_res.tables
    
    for table_md in tables_to_inject:
        # A injeção funciona localizando a primeira âncora disponível
        # e substituindo-a com o markup puro da tabela.
        master_text = re.sub(
            r'<!-- TABLE_ANCHOR_p\d+_t\d+ -->', 
            f"\n\n{table_md}\n\n<!-- TABELA_CONSOLIDADA -->", 
            master_text, 
            count=1
        )

    # Remove âncoras que sobraram caso número de tabelas identificadas pelo plumper 
    # não combinem com a varredura do parser
    master_text = re.sub(r'<!-- TABLE_ANCHOR_p\d+_t\d+ -->', '', master_text)

    # 2. Acoplar Elementos Visuais Escaneados (Se houver contingência/Marker)
    if vision_res.visuals:
        master_text += "\n\n---\n## 🔍 Elementos Gráficos Reconstruídos\n\n"
        for v_block in vision_res.visuals:
            master_text += f"{v_block}\n\n"

    # 3. Passar pelo Cleaner Semântico (Lixeira PT-BR)
    print("[Juiz Mestre] Aplicando Filtros Morfológicos (PT-BR)...")
    final_output = clean_text_block(master_text)

    # 4. Validador Obrigatório MDEval
    print("[Juiz Mestre] Submetendo ao Validador de Saúde Estrutural (MDEval)...")
    evaluator = StructuralDensityEvaluator()
    score = evaluator.evaluate(final_output)

    # 5. Injeção de Roteamento Determinístico (Frontmatter YAML)
    print("[Juiz Mestre] Acoplando metadados estruturais para RAG (Frontmatter YAML)...")
    from datetime import datetime
    original_filename = narrative_res.metadata.get("filename", "documento_extraido.pdf").replace(".pdf", "")
    safe_title = re.sub(r'[^A-Za-z0-9_ -]', '', original_filename)
    
    frontmatter = (
        "---\n"
        f"title: {safe_title}\n"
        "extraction_engine: Orquestrador V2 - BR-PDF-to-MD-to-RAG\n"
        f"source_file: {original_filename}\n"
        f"processing_date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"total_characters: {len(final_output)}\n"
        f"tables_injected: {len(data_res.tables)}\n"
        f"visual_blocks: {len(vision_res.visuals)}\n"
        f"mdeval_score: {score}\n"
        "---\n\n"
    )
    final_output = frontmatter + final_output

    # Levantar compilação de Winners para o front
    narrative_winner = narrative_res.metadata.get("winner", "N/A")
    data_winner = data_res.metadata.get("winner", "N/A") if not data_res.metadata.get("skipped") else "Skipped (Sem Matrizes)"
    vision_winner = vision_res.metadata.get("winner", "N/A") if not vision_res.metadata.get("skipped") else "Skipped (Sem Blocos Visuais)"

    print(f"[Juiz Mestre] CONCLUÍDO | Saúde: {score:.0f}%")
    
    return OrchestratorResult(
        final_markdown=final_output,
        winner_description="Comitê de Especialistas Orquestrado",
        stats={
            "narrative_winner": narrative_winner,
            "data_winner": data_winner,
            "vision_winner": vision_winner,
            "tables_injected": len(data_res.tables),
            "visual_blocks": len(vision_res.visuals)
        },
        mdeval_score=score,
        success=True
    )
