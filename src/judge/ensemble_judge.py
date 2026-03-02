import markdown
from pathlib import Path
from src.parsers.plumber_parser import parse_pdf_plumber_segmented
from src.parsers.markitdown_parser import parse_pdf_markitdown

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

class EnsembleJudge:
    """
    O Juiz 'Identificador-Delegador':
    1. Fase de Inventário: Mapeia o PDF (pdfplumber as sensor).
    2. Fase de Delegação: Cada parte vai para quem é forte.
    3. Fase de Reunião: Consolidação final.
    """

    def synthesize(self, pdf_path: Path) -> dict:
        # --- FASE 1: IDENTIFICAÇÃO (Rastreamento do Conteúdo) ---
        print("[Juiz] Iniciando Inventário de Conteúdo...")
        plumber_segments = parse_pdf_plumber_segmented(pdf_path)
        
        counts = {"text": 0, "table": 0, "total_pages": 0}
        table_mds = []
        
        if pdfplumber:
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    counts["total_pages"] = len(pdf.pages)
            except:
                pass

        for seg in plumber_segments:
            counts[seg["type"]] += 1
            if seg["type"] == "table":
                table_mds.append(seg["content"])
            if "page" in seg:
                counts["total_pages"] = max(counts["total_pages"], seg["page"])

        # --- FASE 2: DELEGAÇÃO (Distribuição por pontos fortes) ---
        print(f"[Juiz] Delegando Texto/Estrutura (Prosa) para MarkItDown...")
        prose_base = parse_pdf_markitdown(pdf_path)
        
        # --- FASE 3: REUNIÃO (O Juiz Reúne Tudo) ---
        print(f"[Juiz] Reunindo resultados: {counts['text']} blocos de texto e {counts['table']} tabelas.")
        
        if counts["table"] == 0:
            # Heurística: Se não há tabelas, o bloco único do MarkItDown é contado.
            return {
                "final_md": prose_base,
                "winner": "Especialista em Fluxo (MarkItDown)",
                "stats": {
                    "tables_identified": 0,
                    "text_blocks_found": max(counts["text"], 1), 
                    "total_pages": counts["total_pages"]
                }
            }

        # Síntese de 'Consenso': MarkItDown Flow + pdfplumber Grids
        synthesis = prose_base
        synthesis += "\n\n---\n## 🧪 Síntese de Dados Estruturados (Alta Precisão)\n\n"
        synthesis += "\n\n".join(table_mds)

        return {
            "final_md": synthesis,
            "winner": "Juiz Híbrido (MarkItDown Structure + pdfplumber Grids)",
            "stats": {
                "tables_identified": counts["table"],
                "text_blocks_found": counts["text"],
                "total_pages": counts["total_pages"]
            }
        }
