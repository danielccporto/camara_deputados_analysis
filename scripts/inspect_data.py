import json
import yaml
from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"

print('DATA dir:', DATA)

# config.yaml
cfg = DATA / 'config.yaml'
print('\n-- config.yaml: exists=', cfg.exists())
try:
    txt = cfg.read_text(encoding='utf-8')
    print('config preview:\n', txt[:1000])
    print('yaml load ->', yaml.safe_load(txt))
except Exception as e:
    print('config load error ->', repr(e))

# insights
ins = DATA / 'insights_distribuicao_deputados.json'
print('\n-- insights file:', ins.exists())
if ins.exists():
    try:
        data = json.loads(ins.read_text(encoding='utf-8'))
        print('insights keys:', list(data.keys()))
        first = data.get('insights', [None])[0]
        print('first insight preview:', repr(first)[:500])
    except Exception as e:
        print('insights load error ->', repr(e))

# proposicoes parquet
p = DATA / 'proposicoes_deputados.parquet'
print('\n-- proposicoes exists=', p.exists())
if p.exists():
    try:
        df = pd.read_parquet(p)
        print('proposicoes columns:', df.columns.tolist())
        if 'dataApresentacao' in df.columns:
            print('dataApresentacao sample:', df['dataApresentacao'].dropna().head(3).tolist())
    except Exception as e:
        print('proposicoes read error ->', repr(e))

# despesas series parquet
s = DATA / 'serie_despesas_diarias_deputados.parquet'
print('\n-- series despesas exists=', s.exists())
if s.exists():
    try:
        df2 = pd.read_parquet(s)
        print('despesas columns:', df2.columns.tolist())
        if 'dataDocumento' in df2.columns:
            print('dataDocumento sample:', df2['dataDocumento'].dropna().head(3).tolist())
    except Exception as e:
        print('despesas read error ->', repr(e))
