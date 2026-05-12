import sys
import os
from pathlib import Path

print('Running basic checks...')
base = Path(__file__).resolve().parent.parent
print('Project root:', base)

# Check data files
files = [
    base / 'data' / 'serie_despesas_diarias_deputados.parquet',
    base / 'data' / 'deputados.parquet',
    base / 'data' / 'proposicoes_deputados.parquet',
]
for f in files:
    print(f.name, 'exists:', f.exists())

# Try importing generated_analysis and running the expense analysis (no external APIs)
try:
    sys.path.insert(0, str(base))
    from data import generated_analysis
    caminho = base / 'data' / 'serie_despesas_diarias_deputados.parquet'
    if not caminho.exists():
        print('SKIP: parquet file for expenses not found, cannot run analysis')
    else:
        print('Running analisar_despesas_deputados(...)')
        res = generated_analysis.analisar_despesas_deputados(str(caminho))
        if res is None:
            print('ERROR: analisar_despesas_deputados returned None')
        else:
            fig_tempo, fig_fornecedor, fig_correlacao = res
            outputs_dir = base / 'docs'
            outputs_dir.mkdir(exist_ok=True)
            if fig_tempo:
                fig_tempo.savefig(outputs_dir / 'test_fig_tempo.png')
                print('Saved test_fig_tempo.png')
            if fig_fornecedor:
                fig_fornecedor.savefig(outputs_dir / 'test_fig_fornecedor.png')
                print('Saved test_fig_fornecedor.png')
            if fig_correlacao:
                fig_correlacao.savefig(outputs_dir / 'test_fig_correlacao.png')
                print('Saved test_fig_correlacao.png')
            print('Analysis functions executed successfully')
except Exception as e:
    print('ERROR during checks:', e)
    raise

print('Basic checks finished.')
