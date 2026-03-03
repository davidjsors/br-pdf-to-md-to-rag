"""
Orquestrador Central — Comitê de Especialistas v2.
Coordena a execução encadeada: Radar -> Narrativa -> Tabelas -> Visão -> Juiz Mestre.
"""
from pathlib import Path
from src.models import OrchestratorResult
from src.radar.spatial_scanner import scan_pdf
from src.judges.narrative_judge import judge_narrative
from src.judges.data_judge import judge_data
from src.judges.vision_judge import judge_vision
from src.judges.master_judge import synthesize_master

def process_pdf(pdf_path: Path) -> OrchestratorResult:
    """
    Roteador Central da Arquitetura de Orquestração Avançada.
    """
    try:
        print("\n" + "="*50)
        print(f"[Orquestrador] Iniciando Processamento: {pdf_path.name}")
        print("="*50)

        # Fase 0: Radar Espacial
        print("\n>>> FASE 0: Radar Espacial <<<")
        manifest = scan_pdf(pdf_path)
        print(f"[Orquestrador] Radar concluiu com {manifest.total_pages} páginas processadas.")

        # Etapa 1: Especialistas Narrativos (Execução Obrigatória)
        print("\n>>> ETAPA 1: Fundação Narrativa <<<")
        narrative_res = judge_narrative(pdf_path, manifest)

        # Etapa 2: Especialistas de Tabelas (Execução Condicional)
        print("\n>>> ETAPA 2: Tratamento de Tabelas <<<")
        data_res = judge_data(pdf_path, manifest)

        # Etapa 3: Especialistas de Visão (Execução Condicional)
        print("\n>>> ETAPA 3: Recuperação Visual/OCR <<<")
        vision_res = judge_vision(pdf_path, manifest)

        # Etapa 4: Síntese e Validação (Execução Obrigatória)
        print("\n>>> ETAPA 4: Síntese Final e Validação MDEval <<<")
        final_res = synthesize_master(narrative_res, data_res, vision_res)
        final_res.stats["total_pages"] = manifest.total_pages

        print("\n" + "="*50)
        print("[Orquestrador] Processo Concluído com Sucesso!")
        print("="*50 + "\n")

        return final_res

    except Exception as e:
        import traceback
        traceback.print_exc()
        return OrchestratorResult(
            success=False,
            error=str(e)
        )
