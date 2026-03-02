import os
from pathlib import Path
from src.judge.ensemble_judge import EnsembleJudge

def process_pdf(pdf_path: Path, output_dir: Path) -> dict:
    """
    O 'Super-Motor' com Juiz:
    1. Instancia o Juiz do Ensemble.
    2. Executa múltiplos especialistas (MarkItDown, Plumber).
    3. Sintetiza o resultado final.
    """
    print(f"Iniciando Processamento Ensemble Judged: {pdf_path.name}")
    
    try:
        judge = EnsembleJudge()
        result = judge.synthesize(pdf_path)
        
        md_content = result["final_md"]
        winner = result["winner"]
        
        # Gerar arquivo final
        md_filename = pdf_path.stem + ".md"
        md_path = output_dir / md_filename
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
            
        print(f"Sucesso! Juiz escolheu: {winner}")
        
        # Retorna sucesso e metadados para a UI
        return {
            "success": True,
            "md_path": md_path,
            "winner": winner,
            "stats": result["stats"]
        }

    except Exception as e:
        print(f"Erro no Processamento Ensemble: {e}")
        return {"success": False, "error": str(e)}
