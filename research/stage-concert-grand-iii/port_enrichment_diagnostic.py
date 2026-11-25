"""Enriched basis on the same 30-cell model; full-coordinate dry reference.
Wet proof uses a nested enriched space and two independent quadrature settings.
"""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from bridge_strings import centerline
from spline_plate import assemble
from structural_assembly import assemble as structure
from string_structure import setup
from condensation_precision import response as full_strings
from polygon_radiation import modes,SurfaceModes
from split_radiation import split_load,relative
from modal_string_radiation import response,truncate
from port_enrichment import enrich
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    l=layout_build(sc,read('layout_hypothesis.json'));mat=read('board_interface_hypothesis.json')
    c=contour_build(l,read('board_contour_hypothesis.json'),mat);rib=read('ribbed_plate_hypothesis.json')['rib']
    poly=np.array(c['contourXY_m']);centers={s:centerline(l['bridgeAttachmentNodes'][s]) for s in ('bass','treble')}
    m=assemble(poly,c['ribs'],mat['plate'],rib,30,14,False)
    z=structure(m,centers,read('bridge_hypothesis.json'),mat,read('rim_structure_hypothesis.json'),2,8,14,True)
    M=z['M'];K=z['K']+z['Jrim']+z['Jbridge'];D=z['D']
    rr={r['key']:r for r in sc['rows']};keys=[45,48];P,wires,labels=setup(z,centers,rr,keys,2,128)
    rear=sorted(set(w.rear for w in wires));E=np.zeros((len(M),len(rear)));E[rear,np.arange(len(rear))]=1.
    F=np.column_stack([P[:,len(keys):],E])
    freq=np.array([30.,50.,80.,110.,130.8128,150.]);q0=modes(M,K,D,P,192)
    q=enrich(M,K,D,P,q0['U'],F,96,(128,192))
    dry,ds,_=full_strings(M,K,D,P,wires,freq)
    mic=np.array([x['xyzM'] for x in l['capture']]);field=SurfaceModes(m,q['U'][:z['plateDofs']])
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'port_enrichment.json';dryRows=[]
    for n in q['sizes']:
        mm=truncate(q,n);ports=[q['U'][w.rear,:n] for w in wires]
        out=[response(mm,ports,wires,np.zeros((n,n)),np.zeros((2,n)),f) for f in freq]
        dryRows.append(dict(dofs=n,relative=relative([x[0] for x in out],dry),gate=all(x[2]['gate'] for x in out)))
    print('G3_ENRICHMENT_DRY '+json.dumps(dryRows),flush=True)
    path.write_text(json.dumps(dict(dry=dryRows,complete=False),indent=2,allow_nan=False))
    cases=[];outputs=[]
    for outer,inner,angle in [(24,36,28),(30,44,32)]:
        loads=split_load(poly,field,freq,mic,outer,inner,angle)
        for n in (q['sizes'][1:] if outer==24 else [q['sizes'][-1]]):
            mm=truncate(q,n);ports=[q['U'][w.rear,:n] for w in wires];Y=[];O=[];metrics=[];op=[]
            for f,(Z,H,rep) in zip(freq,loads):
                y,o,s=response(mm,ports,wires,Z[:n,:n],H[:,:n],f)
                Y.append(y);O.append(o);metrics.append(s);op.append(rep)
            row=dict(dofs=n,outer=outer,inner=inner,angle=angle,metrics=metrics,operatorMetrics=op,
                operatorGate=all(x['gate'] for x in op),rawOriginalGate=all(x['rawGate'] for x in op))
            row['gate']=all(x['gate'] for x in metrics) and row['operatorGate']
            cases.append(row);outputs.append((np.array(Y),np.array(O)))
            path.write_text(json.dumps(dict(dry=dryRows,cases=cases,complete=False),indent=2,allow_nan=False))
            print('G3_ENRICHMENT_CASE '+json.dumps(row),flush=True)
    checks=[]
    for (x,u),(y,v) in zip(outputs,outputs[1:]):
        a=relative(x,y);b=relative(u,v);checks.append(dict(mobility=a,pressure=b,gate=max(a,b)<=.05))
    eigGate=q0['massError']<=1e-5 and q0['scaledEigenResidual']<=1e-8 and q0['originalEigenResidual']<=1e-5
    summary=dict(dry=dryRows,dryReference=ds,eigenGate=eigGate,residualVectorRank=q['residualVectorRank'],
        massError=q['massError'],cases=cases,convergence=checks,gate=ds['gate'] and eigGate and dryRows[-1]['relative']<=.05 and dryRows[-1]['gate'] and all(x['gate'] for x in checks[-2:]) and cases[-1]['gate'],
        integratedReady=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,keys=keys,ports=labels,frequenciesHz=freq.tolist(),scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_ENRICHMENT_GATE '+json.dumps(summary),flush=True);assert summary['gate'],'enriched response convergence'
if __name__=='__main__':main()
