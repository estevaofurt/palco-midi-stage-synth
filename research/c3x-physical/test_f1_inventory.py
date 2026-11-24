# Protocolo mínimo de consistência F1. Não testa fidelidade física.
from pathlib import Path
import csv,json

root=Path(__file__).resolve().parents[2]
with (root/'research/c3x-physical/F1_INVENTARIO_PARAMETROS_C3X.csv').open(encoding='utf-8-sig',newline='') as f:
    rows=list(csv.DictReader(f,delimiter=';'))
assert len(rows) >= 25
assert all(r['classe'] and r['fonte'] for r in rows if r['classe'] in ('estimativa_software','especificacao_oficial','derivado_do_alvo'))
assert not any(r['classe'] == 'medido_c3x_c4' for r in rows)
assert sum(r['classe']=='desconhecido' for r in rows)>=10
manifest=json.loads((root/'research/c3x-physical/F1_DIAGNOSTICO_REPRODUZIVEL.json').read_text(encoding='utf-8'))
assert manifest['f1_status']=='PENDENTE'
assert manifest['inventory_rows']==len(rows)
assert manifest['v10_c4']['linear_density_derived_kg_per_m']>0
print(f'F1 inventory: {len(rows)} linhas, parâmetros físicos não homologados, F1 pendente.')
