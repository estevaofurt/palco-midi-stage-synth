"""Valida apenas a integridade do planejamento F1; NAO aprova a fisica."""
import csv,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def read_csv(filename):
    with (ROOT/filename).open(encoding='utf-8-sig',newline='') as f:
        return list(csv.DictReader(f,delimiter=';'))

def test_f1_2():
    m=json.loads((ROOT/'F1_ESTADO_E_GATES_V2.json').read_text(encoding='utf-8'))
    sources=read_csv('F1_FONTE_STATUS_V2.csv')
    capture=read_csv('F1_SESSOES_C4_PLANEJADAS.csv')
    params=read_csv('F1_PARAMETROS_C4_PENDENTES.csv')
    assert m['fase']=='F1' and m['status']=='PENDENTE'
    assert len(sources)==m['source_count']==8
    assert len(capture)==m['planned_capture_count']==24
    assert len(params)==m['pending_parameter_count']==16
    assert m['physical_c4_measured_count']==0
    assert m['physical_c4_audio_acquired_count']==0
    assert len({s['id'] for s in sources})==len(sources)
    assert len({s['id_tomada'] for s in capture})==len(capture)
    assert len([s for s in capture if s['tipo']=='nota_isolada'])==15
    assert all(s['estado']=='PENDENTE' and s['arquivo_pcm']=='nao_coletado' and not s['sha256'] for s in capture)
    assert all(p['status']=='desconhecido' and not p['valor'] and not p['hash_dado_base'] for p in params)
    assert not any(s['estado_aquisicao']=='arquivo_verificado' for s in sources)
    assert any(s['id']=='KEMP_OSF_TBZDC' and 'sem_inspecao' in s['classe_evidencia'] for s in sources)
    print('F1.2: fontes=8, C4 planejados=24, parametros pendentes=16; NENHUMA medida C4 aprovada.')

if __name__=='__main__':test_f1_2()
