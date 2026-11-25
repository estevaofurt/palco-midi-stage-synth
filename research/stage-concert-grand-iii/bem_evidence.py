"""Read immutable run artifacts and distinguish completed solver proofs
from partial evidence, missing artifacts and diagnostic-only gates.
No solver promotion or ranking across incompatible audit rules.
"""
import argparse,json,math
from pathlib import Path
ROOT=Path(__file__).parent
METRICS=('heldoutResidual','heldoutWorstColumn','reciprocity','powerRelative')
LIMITS=dict(heldoutResidual=.05,heldoutWorstColumn=.05,reciprocity=.01,powerRelative=.01)
def read(p):return json.loads(p.read_text())
def finite(v):return isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v)
def maxima(reports,key):
    if not reports:return None
    out={}
    for k in METRICS:
        vals=[r.get(key,{}).get(k) for r in reports]
        if not all(finite(v) and v>=0 for v in vals):return None
        out[k]=max(vals)
    return out
def summarize(m,angle,job,doc,freq):
    row=dict(method=m['key'],angleDeg=angle,runId=m['run'],role=m['role'],
        auditFamily=m.get('family'),jobStatus=job.get('status','unknown'),
        jobConclusion=job.get('conclusion'),artifactAvailable=doc is not None)
    row['state']='missing-artifact' if doc is None else 'partial'
    row['solverApproved']=False
    if doc is None:return row
    if not isinstance(doc,dict):raise ValueError('invalid artifact')
    summary=doc.get('summary',{})
    complete=(isinstance(summary,dict) and summary.get('angleDeg')==angle and isinstance(summary.get('gate'),bool))
    row['artifactComplete']=complete
    row['reportedGate']=summary.get('gate') if complete else None
    row['scaleSha256']=doc.get('scaleSha256')
    if m['role']=='diagnostic':
        cases=doc.get('cases',[])
        row['diagnosticCases']=len(cases)
        row['partition']=[dict(frequencyHz=c.get('frequencyHz'),method=c.get('method'),
            reliable=c.get('diagnosticReliable'),**{k:c['cases'][-1].get(k) for k in
            ('totalPowerRelative','boundaryWorkRelative','computedWorkRelative','partitionClosure','errorAlignment')})
            for c in cases if c.get('cases')]
        row['state']='diagnostic-complete' if complete else 'diagnostic-partial'
        return row
    cases=doc.get('cases',[])
    if m.get('rowKind'):cases=[c for c in cases if c.get('kind')==m['rowKind']]
    if not cases:return row
    last=cases[-1];reports=last.get('reports',[])
    metrics=maxima(reports,m['audit'])
    row['elements']=last.get('elements');row['unknowns']=last.get('unknowns',last.get('elements'))
    row['metrics']=metrics
    row['frequencyCoverageComplete']=sorted(r.get('frequencyHz') for r in reports)==sorted(freq)
    if m.get('control'):
        row['sameMeshControl']=maxima(reports,m['control'])
    if metrics is not None:
        row['exceedsLimits']=[k for k,v in metrics.items() if v>LIMITS[k]]
    if not complete:return row
    row['state']='reported-pass' if summary['gate'] else 'reported-fail'
    row['solverApproved']=bool(summary['gate'] and row['frequencyCoverageComplete'] and metrics is not None
        and not row['exceedsLimits'] and row['jobStatus']=='completed' and row['jobConclusion']=='success'
        and isinstance(row['scaleSha256'],str) and len(row['scaleSha256'])==64)
    if summary['gate'] and not row['solverApproved']:row['state']='inconsistent-pass'
    return row
def collect(manifest,root):
    rows=[]
    for m in manifest['methods']:
        meta=root/str(m['run'])/'jobs.json'
        jobs=read(meta).get('jobs',[]) if meta.is_file() else []
        for angle in manifest['angles']:
            job=next((j for j in jobs if j.get('name')==f'proof ({angle})'),{})
            path=root/str(m['run'])/f"{m['artifact']}-{angle}"/m['file']
            rows.append(summarize(m,angle,job,read(path) if path.is_file() else None,manifest['frequenciesHz']))
    # A pass on a subset cannot certify the combined cabinet. No comparison
    # of raw residuals across different quadrature families is made.
    return dict(rows=rows,physicalLimits=LIMITS,fullCabinetReady=False,radiationReady=False,
        evidenceOnly=True,solverCasesApproved=sum(r['solverApproved'] for r in rows))
def markdown(report):
    out=['# BEM — evidências verificadas','',
         '| Método | Ângulo | Estado | Triângulos | Resíduo | Pior coluna | Reciprocidade | Potência |',
         '|---|---:|---|---:|---:|---:|---:|---:|']
    pct=lambda x:f'{100*x:.3f}%' if finite(x) else '—'
    for r in report['rows']:
        m=r.get('metrics') or {}
        out.append(f"| {r['method']} | {r['angleDeg']}° | {r['state']} | {r.get('elements') or '—'} | "+' | '.join(pct(m.get(k)) for k in METRICS)+' |')
    out+=['','## Notas','',
          'Métodos com famílias de auditoria diferentes não são comparações controladas.',
          'Diagnósticos energéticos não aprovam o solucionador.',
          'Arquivos parciais, ausentes ou sem conclusão do job não certificam nenhum caso.',
          'A radiação integral do gabinete não está aprovada.','']
    return '\n'.join(out)
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--manifest',type=Path,default=ROOT/'bem_evidence_manifest.json');a=p.parse_args()
    report=collect(read(a.manifest),a.root);a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'bem_evidence.json').write_text(json.dumps(report,indent=2,allow_nan=False))
    (a.out/'bem_evidence.md').write_text(markdown(report))
    print('G3_BEM_EVIDENCE '+json.dumps(dict(cases=len(report['rows']),solverCasesApproved=report['solverCasesApproved'],radiationReady=False)))
if __name__=='__main__':main()
