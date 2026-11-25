"""Reuse spatial proof matrices; never rerun FEM or exterior quadrature.
Evaluate nested aperture modes on every completed spatial configuration.
"""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from recess_envelope import build as envelope
from nested_acoustic_ports import reduced_panels,embedding
from dual_cavity_spatial_diagnostic import FREQ,CONFIGS,compare_spatial
from acoustic_matrix_archive import read_npz,validate_manifest,replay_full,modal_replay
from split_radiation import relative
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--archive',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--angle',type=float,required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sha=hashlib.sha256(raw).hexdigest();sc=json.loads(raw)
    assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    doc=json.loads((a.archive/'dual_cavity_spatial.json').read_text());rows=validate_manifest(doc,a.angle,sha,FREQ,CONFIGS)
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.asarray(q['contourXY_m']);g=geometry(poly,l,read('cabinet_geometry_hypothesis.json'))
    def field(xy):
        x,y=(2*(xy-poly.min(0))/np.ptp(poly,axis=0)-1).T
        return np.stack([np.ones(len(x)),x,y,x*y],axis=1)
    _,ext,_,geo=envelope(poly,g['rimTopZ_m'],g['rimBottomZ_m'],a.angle,36,field,36)
    counts=[x.basis.count for x in ext];areas=np.array([x.basis.area for x in ext]);assert counts==[36]*7
    nf=len(FREQ);nb=4;nu=216+nb;nl=36+nb;ne=252;nm=len(g['microphonesXYZ_m'])
    shared=read_npz(a.archive,doc['shared'],dict(areas=(7,),Zl=(nf,nl,nl),Pl=(nf,2,nl),Ze=(nf,ne,ne),Pe=(nf,2,ne)),FREQ)
    if relative(shared['areas'],areas)>1e-10:raise ValueError('physical port area mismatch')
    maps={}
    for n,m in [(15,21),(21,21),(28,28),(36,36),(21,36),(36,21)]:
        low=reduced_panels(ext,[n]*6+[m])
        Tu,_=embedding(ext[:-1],low[:-1]);Tl,_=embedding(ext[-1:],low[-1:]);maps[n,m]=(Tu,Tl)
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'dual_cavity_modal_replay.json';results=[]
    for row in rows:
        u=read_npz(a.archive,row['archive'],dict(Zu=(nf,nu,nu),Pu=(nf,nm,nu),Y=(nf,nb,nb),flow=(nf,ne,nb)),FREQ)
        mats=[tuple(x[i] for x in (u['Zu'],u['Pu'],shared['Zl'],shared['Pl'],shared['Ze'],shared['Pe'])) for i in range(nf)]
        full=[];checks=[]
        for i,x in enumerate(mats):
            y,d=replay_full(*x,u['Y'][i],u['flow'][i],nb);full.append(y);checks.append(d)
        cases=[];outputs={}
        for (n,m),(Tu,Tl) in maps.items():
            vals=[];reports=[]
            for f,x,y in zip(FREQ,mats,full):
                v,r=modal_replay(x,Tu,Tl,nb,counts,areas,y);vals.append(v);reports.append(dict(frequencyHz=f,**r))
            outputs[n,m]=vals
            cases.append(dict(upperModesPerPanel=n,lowerModes=m,reports=reports,against252=compare_spatial(FREQ,vals,full,counts,areas)))
        seq=[(15,21),(21,21),(28,28),(36,36)]
        convergence=[compare_spatial(FREQ,outputs[x],outputs[y],counts,areas) for x,y in zip(seq,seq[1:])]
        result=dict(planarN=row['planarN'],boundaryN=row['boundaryN'],wedgeLayers=row['wedgeLayers'],
            minimumCapture36=row['minimumCapture36'],replayMax=max(max(x.values()) for x in checks),
            modalConvergence=convergence,cases=cases,modalGate=convergence[-1]['gate'])
        results.append(result)
        path.write_text(json.dumps(dict(cases=results,complete=False),indent=2,allow_nan=False))
        print('G3_MODAL_REPLAY_CASE '+json.dumps({**{k:v for k,v in result.items() if k not in ('cases','modalConvergence')},
            'modalConvergence':[x['maximum'] for x in convergence]}),flush=True)
    summary=dict(gate=True,angleDeg=a.angle,diagnosticOnly=True,sourceSpatialGate=doc['summary']['gate'],
        reusedMatrices=True,maximumReplayDifference=max(x['replayMax'] for x in results),
        quadratureConvergenceCertified=False,fullCabinetReady=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=results,scaleSha256=sha,frequenciesHz=FREQ),indent=2,allow_nan=False))
    print('G3_MODAL_REPLAY_GATE '+json.dumps(summary),flush=True)
if __name__=='__main__':main()
