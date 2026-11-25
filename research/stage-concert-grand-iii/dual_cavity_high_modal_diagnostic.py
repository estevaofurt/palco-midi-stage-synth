"""385-mode common free-space reference on screened upper mesh.
Modal comparisons use one fixed set of matrices; old 252-mode archive is
a separate directional spatial control, not a combined convergence proof.
"""
import argparse,hashlib,json,time
from pathlib import Path
import numpy as np
from scipy.linalg import block_diag
from spatial_layout import build as layout_build
from board_contour import build as contour_build,properties
from cabinet_geometry import geometry
from hybrid_cavity import build as upper_build,response as upper_response
from lower_prism import build as lower_build,response as lower_response
from recess_envelope import build as envelope
from acoustic_port_bridge import compatible
from port_coordinates import transform
from nested_acoustic_ports import project,reduced_panels,embedding
from lid_exterior import load,pressure
from dual_cavity_reference import couple
from dual_cavity_spatial_diagnostic import FREQ,CONFIGS,compare_spatial,save_matrices
from acoustic_trace_resolution import panel_capture,describe
from acoustic_matrix_archive import validate_manifest,read_npz,replay_full,modal_replay
from split_radiation import relative
ROOT=Path(__file__).parent
COUNT=55;NB=4;CONFIG=(40,160,24);LOWER_N=72
def read(n):return json.loads((ROOT/n).read_text())

def require_screen(doc,angle,sha):
    s=doc.get('summary',{})
    if doc.get('scaleSha256')!=sha or s.get('angleDeg')!=angle or s.get('gate') is not True or s.get('diagnosticOnly') is not True or s.get('screeningMinimumEnergy')!=.95:
        raise ValueError('invalid high-mode trace screening')
    upper=[r for r in doc.get('cases',[]) if (r.get('boundaryN'),r.get('wedgeLayers'))==CONFIG[1:]]
    lower=[r for r in doc.get('lower',[]) if r.get('planarN')==LOWER_N]
    if len(upper)!=1 or len(lower)!=1 or upper[0]['minimumCapture']['55']<.95 or lower[0]['degrees']['55']['minimumCapturedEnergy']<.95:
        raise ValueError('selected trace not screened')
    return upper[0]['minimumCapture']['55'],lower[0]['degrees']['55']['minimumCapturedEnergy']

def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--screen',type=Path,required=True)
    p.add_argument('--archive',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--angle',type=float,choices=[30.,55.],required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sha=hashlib.sha256(raw).hexdigest();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    screened= require_screen(json.loads(a.screen.read_text()),a.angle,sha)
    doc=json.loads((a.archive/'dual_cavity_spatial.json').read_text());rows=validate_manifest(doc,a.angle,sha,FREQ,CONFIGS);assert doc['summary']['gate']
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.asarray(q['contourXY_m']);g=geometry(poly,l,read('cabinet_geometry_hypothesis.json'))
    h=-g['rimBottomZ_m'];_,center,_=properties(poly);mic=np.asarray(g['microphonesXYZ_m']);nm=len(mic);nf=len(FREQ)
    lp=np.array([np.r_[center,-h*.25],np.r_[center,-h*.75]])
    far=np.array([[poly[:,0].max()+2.,poly[:,1].mean(),1.5],[poly[:,0].mean(),poly[:,1].max()+2.,-.8]])
    def field(xy):
        x,y=(2*(xy-poly.min(0))/np.ptp(poly,axis=0)-1).T
        return np.stack([np.ones(len(x)),x,y,x*y],axis=1)
    _,ext,_,geo=envelope(poly,g['rimTopZ_m'],g['rimBottomZ_m'],a.angle,COUNT,field,COUNT)
    _,oldext,_,_=envelope(poly,g['rimTopZ_m'],g['rimBottomZ_m'],a.angle,36,field,36)
    assert geo['gate'] and len(ext)==7
    counts=[COUNT]*7;areas=[x.basis.area for x in ext]
    shared=read_npz(a.archive,doc['shared'],dict(areas=(7,),Zl=(nf,40,40),Pl=(nf,2,40),Ze=(nf,252,252),Pe=(nf,2,252)),FREQ)
    old=read_npz(a.archive,rows[2]['archive'],dict(Zu=(nf,220,220),Pu=(nf,nm,220),Y=(nf,4,4),flow=(nf,252,4)),FREQ)
    assert relative(areas,shared['areas'])<=1e-10
    Tu36,_=embedding(ext[:-1],oldext[:-1],order=18);Tl36,_=embedding(ext[-1:],oldext[-1:],order=18)
    T36=block_diag(Tu36,Tl36);maps={(36,36):(Tu36,Tl36)}
    for n,m in ((45,45),(55,55),(55,45),(45,55),(55,36),(36,55)):
        lo=reduced_panels(ext,[n]*6+[m]);Tu,_=embedding(ext[:-1],lo[:-1],order=18);Tl,_=embedding(ext[-1:],lo[-1:],order=18);maps[n,m]=(Tu,Tl)
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'dual_cavity_high_modal.json'
    start=time.perf_counter();l=lower_build(poly,LOWER_N,h,field,COUNT);assert compatible(l['mouth'],ext[-1])
    E,br=transform([l['mouth']],ext[-1:],order=18);assert max(br.values())<=1e-8
    El=block_diag(np.eye(NB),E);lower=[];lr=[]
    xyz=np.c_[l['xy'],np.full(len(l['xy']),-h)]
    G,nodes=panel_capture(xyz,l['tri'],l['B'][:,NB:],l['mouth']);lowerCapture=describe(G)['minimumCapturedEnergy']
    assert lowerCapture>=.95 and abs(lowerCapture-screened[1])<=1e-8
    for f in FREQ:
        Z,P,r=lower_response(l,2j*np.pi*f,lp);assert r['gate'];lower.append(project(Z,P,El));lr.append(r)
    del l
    print('G3_HIGH_MODAL_LOWER '+json.dumps(dict(seconds=time.perf_counter()-start,capture=lowerCapture)),flush=True)
    start=time.perf_counter();exterior=[];er=[]
    for f,(Z,r) in zip(FREQ,load(ext,FREQ,30,52,40,pair_block=64,self_block=8)):
        assert r['gate'];exterior.append((Z,pressure(ext,np.eye(len(Z)),far,f,30)));er.append(r)
    sharedEntry=save_matrices(a.out,'shared_high',frequencies=FREQ,areas=areas,Zl=np.stack([v[0] for v in lower]),Pl=np.stack([v[1] for v in lower]),Ze=np.stack([v[0] for v in exterior]),Pe=np.stack([v[1] for v in exterior]))
    print('G3_HIGH_MODAL_EXTERIOR '+json.dumps(dict(seconds=time.perf_counter()-start,maximumReactiveAsymmetry=max(r['reactiveAsymmetry'] for r in er))),flush=True)
    n,b,k=CONFIG;u=upper_build(poly,n,1,g['rimTopZ_m'],a.angle,field,COUNT,wedge_layers=k,boundary_n=b)
    assert len(u['panels'])==6 and all(compatible(x,y) for x,y in zip(u['panels'],ext[:-1]))
    E,br=transform(u['panels'],ext[:-1],order=18);assert max(br.values())<=1e-8;Eu=block_diag(np.eye(NB),E)
    trace=[]
    for i,(faces,panel) in enumerate(zip(u['full']['apertureFaces'],u['panels'])):
        G,nodes=panel_capture(u['full']['xyz'],faces,u['Cfull'][:,COUNT*i:COUNT*(i+1)],panel)
        trace.append(dict(panel=i,nodes=nodes,**describe(G)))
    upperCapture=min(x['minimumCapturedEnergy'] for x in trace)
    assert upperCapture>=.95 and abs(upperCapture-screened[0])<=1e-8
    full=[];mats=[];reports=[];oldfull=[]
    for i,f in enumerate(FREQ):
        Z,P,ur=upper_response(u,f,mic,solver='schur-real');assert ur['gate'];Zu,Pu=project(Z,P,Eu)
        Zl,Pl=lower[i];Ze,Pe=exterior[i];x=(Zu,Pu,Zl,Pl,Ze,Pe)
        *y,cr=couple(*x,NB,reference_kind='common-free-space-monopole');assert cr['gate']
        mats.append(x);full.append(tuple(y));reports.append(dict(frequencyHz=f,upper=ur,lower=lr[i],exterior=er[i],coupled=cr))
        o,_=replay_full(old['Zu'][i],old['Pu'][i],shared['Zl'][i],shared['Pl'][i],shared['Ze'][i],shared['Pe'][i],old['Y'][i],old['flow'][i],NB)
        oldfull.append((*o[:-1],T36@o[-1]))
        path.write_text(json.dumps(dict(complete=False,reports=reports,shared=sharedEntry,scaleSha256=sha),indent=2,allow_nan=False))
        print('G3_HIGH_MODAL_FREQUENCY '+json.dumps(dict(frequencyHz=f,gate=cr['gate'],upperResidual=ur['residual'])),flush=True)
    upperEntry=save_matrices(a.out,'upper_high',frequencies=FREQ,Zu=np.stack([v[0] for v in mats]),Pu=np.stack([v[1] for v in mats]),Y=np.stack([v[0] for v in full]),flow=np.stack([v[-1] for v in full]))
    outputs={};cases=[]
    for (n,m),(Tu,Tl) in maps.items():
        vals=[];rr=[]
        for f,x,y in zip(FREQ,mats,full):
            v,r=modal_replay(x,Tu,Tl,NB,counts,areas,y);vals.append(v);rr.append(dict(frequencyHz=f,**r))
        outputs[n,m]=vals;cases.append(dict(upperModesPerPanel=n,lowerModes=m,reports=rr,against385=compare_spatial(FREQ,vals,full,counts,areas)))
    comparisons=dict(modal36to45=compare_spatial(FREQ,outputs[36,36],outputs[45,45],counts,areas),
        modal45to55=compare_spatial(FREQ,outputs[45,45],full,counts,areas),
        upperOnly=compare_spatial(FREQ,outputs[45,55],full,counts,areas),
        lowerOnly=compare_spatial(FREQ,outputs[55,45],full,counts,areas),
        spatial36=compare_spatial(FREQ,oldfull,outputs[36,36],counts,areas))
    summary=dict(gate=True,angleDeg=a.angle,diagnosticOnly=True,maximumModes=385,upperConfig=list(CONFIG),lowerN=LOWER_N,
        upperCapture=upperCapture,lowerCapture=lowerCapture,modalGate=comparisons['modal45to55']['gate'],
        spatial36Gate=comparisons['spatial36']['gate'],quadratureConvergenceCertified=False,combinedFineMeshNotTested=True,
        commonFreeSpaceMonopolesOnly=True,fullCabinetReady=False,radiationReady=False,
        comparisons={k:v['maximum'] for k,v in comparisons.items()})
    path.write_text(json.dumps(dict(summary=summary,reports=reports,cases=cases,comparisons=comparisons,trace=trace,
        shared=sharedEntry,upper=upperEntry,scaleSha256=sha,frequenciesHz=FREQ),indent=2,allow_nan=False))
    print('G3_HIGH_MODAL_GATE '+json.dumps(summary),flush=True)
if __name__=='__main__':main()
