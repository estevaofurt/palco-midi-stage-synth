"""Fixed 252-mode common-exterior reference, varying upper FEM mesh only.
Upper matrices are transformed to identical physical port coordinates.
This is a directional spatial convergence experiment, not finite-rim BEM.
"""
import argparse,json,hashlib,time
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
from nested_acoustic_ports import project
from lid_exterior import load,pressure
from dual_cavity_reference import couple
from dual_cavity_extended_diagnostic import prerequisite
from dual_cavity_reference_diagnostic import compare,maximum
from acoustic_trace_resolution import panel_capture,describe
from flow_modal_audit import audit_flow
ROOT=Path(__file__).parent
FREQ=[30.,80.,150.,200.,250.,300.]
CONFIGS=[(40,40,1),(40,100,16),(40,120,24),(60,100,16)]
def read(n):return json.loads((ROOT/n).read_text())
def compare_spatial(freq,a,b,counts,areas):
    if len(a)!=len(b) or len(a)!=len(freq) or len(freq)==0:raise ValueError('incomplete comparison')
    rows=compare(freq,a,b);T=np.eye(sum(counts))
    for row,x,y in zip(rows,a,b):
        rr=audit_flow(x[-1],y[-1],T,counts,areas)
        row.update(physicalVelocityRelative=rr['physicalVelocityRelative'],flowPanels=rr['panels'])
    out=maximum(rows);out['physicalVelocityRelative']=max(x['physicalVelocityRelative'] for x in rows)
    return dict(maximum=out,frequencies=rows,gate=all(v<=.05 for v in out.values()))
def save_matrices(out,name,**matrices):
    path=out/(name+'.npz');np.savez_compressed(path,**matrices)
    return dict(file=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--previous',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--angle',type=float,required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sha=hashlib.sha256(raw).hexdigest();prerequisite(json.loads(a.previous.read_text()),a.angle,sha)
    sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.asarray(q['contourXY_m']);g=geometry(poly,l,read('cabinet_geometry_hypothesis.json'))
    h=-g['rimBottomZ_m'];_,center,_=properties(poly);mic=np.asarray(g['microphonesXYZ_m'])
    lp=np.array([np.r_[center,-h*.25],np.r_[center,-h*.75]])
    far=np.array([[poly[:,0].max()+2.,poly[:,1].mean(),1.5],[poly[:,0].mean(),poly[:,1].max()+2.,-.8]])
    def field(xy):
        x,y=(2*(xy-poly.min(0))/np.ptp(poly,axis=0)-1).T
        return np.stack([np.ones(len(x)),x,y,x*y],axis=1)
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'dual_cavity_spatial.json';rows=[];outputs=[]
    _,ext,_,geo=envelope(poly,g['rimTopZ_m'],g['rimBottomZ_m'],a.angle,36,field,36)
    assert len(ext)==7
    counts=[x.basis.count for x in ext];areas=[x.basis.area for x in ext]
    l=lower_build(poly,72,h,field,36);assert compatible(l['mouth'],ext[-1])
    E,br=transform([l['mouth']],ext[-1:]);assert max(br.values())<=1e-8
    El=block_diag(np.eye(4),E);lower=[];lowerReports=[]
    for f in FREQ:
        Z,P,r=lower_response(l,2j*np.pi*f,lp);assert r['gate']
        lower.append(project(Z,P,El));lowerReports.append(r)
    del l
    exterior=[];extReports=[]
    for f,(Z,r) in zip(FREQ,load(ext,FREQ,30,52,40)):
        assert r['gate'];exterior.append((Z,pressure(ext,np.eye(len(Z)),far,f,30)));extReports.append(r)
    shared=save_matrices(a.out,'shared_reference',frequencies=FREQ,areas=areas,
        Zl=np.stack([x[0] for x in lower]),Pl=np.stack([x[1] for x in lower]),
        Ze=np.stack([x[0] for x in exterior]),Pe=np.stack([x[1] for x in exterior]))
    for n,b,k in CONFIGS:
        start=time.perf_counter()
        u=upper_build(poly,n,1,g['rimTopZ_m'],a.angle,field,36,wedge_layers=k,boundary_n=b)
        assert len(u['panels'])==6 and all(compatible(x,y) for x,y in zip(u['panels'],ext[:-1]))
        E,br=transform(u['panels'],ext[:-1]);assert max(br.values())<=1e-8
        Eu=block_diag(np.eye(4),E);trace=[]
        for i,(f,panel) in enumerate(zip(u['full']['apertureFaces'],u['panels'])):
            G,nodes=panel_capture(u['full']['xyz'],f,u['Cfull'][:,36*i:36*(i+1)],panel)
            trace.append(dict(panel=i,nodes=nodes,**describe(G)))
        capture=min(x['minimumCapturedEnergy'] for x in trace)
        if k>1 and capture<.95:raise ValueError('refined trace failed spatial screening')
        upper=[];vals=[];reports=[]
        for f,(Zl,Pl),(Ze,Pe),lr,er in zip(FREQ,lower,exterior,lowerReports,extReports):
            Z,P,ur=upper_response(u,f,mic,solver='schur');assert ur['gate']
            Zu,Pu=project(Z,P,Eu);upper.append((Zu,Pu))
            Y,p1,p2,p3,F,cr=couple(Zu,Pu,Zl,Pl,Ze,Pe,4,reference_kind='common-free-space-monopole')
            assert cr['gate'];vals.append((Y,p1,p2,p3,F))
            reports.append(dict(frequencyHz=f,upper=ur,lower=lr,exterior=er,coupled=cr))
            print('G3_SPATIAL_FREQUENCY '+json.dumps(dict(n=n,boundaryN=b,wedgeLayers=k,frequencyHz=f,gate=cr['gate'])),flush=True)
        archive=save_matrices(a.out,f'upper_{n}_{b}_{k}',frequencies=FREQ,Zu=np.stack([x[0] for x in upper]),Pu=np.stack([x[1] for x in upper]),
            Y=np.stack([x[0] for x in vals]),flow=np.stack([x[-1] for x in vals]))
        row=dict(planarN=n,boundaryN=b,wedgeLayers=k,nodes=u['K'].shape[0],minimumCapture36=capture,trace=trace,
            seconds=time.perf_counter()-start,archive=archive,reports=reports,gate=all(x['coupled']['gate'] for x in reports))
        rows.append(row);outputs.append(vals)
        path.write_text(json.dumps(dict(cases=rows,shared=shared,complete=False,scaleSha256=sha),indent=2,allow_nan=False))
        print('G3_SPATIAL_CASE '+json.dumps({key:v for key,v in row.items() if key not in ('reports','trace')}),flush=True)
        del u
    comparisons=dict(oldToRefined=compare_spatial(FREQ,outputs[0],outputs[1],counts,areas),
        boundaryAndLayers=compare_spatial(FREQ,outputs[1],outputs[2],counts,areas),
        interior=compare_spatial(FREQ,outputs[1],outputs[3],counts,areas))
    gate=all(r['gate'] for r in rows) and comparisons['boundaryAndLayers']['gate'] and comparisons['interior']['gate']
    summary=dict(gate=gate,angleDeg=a.angle,maximumModes=252,exteriorFixed=True,lowerFixed=True,
        directionalSpatialOnly=True,combinedFineMeshNotTested=True,modalConvergenceCertified=False,quadratureConvergenceCertified=False,
        commonFreeSpaceMonopolesOnly=True,fullCabinetReady=False,radiationReady=False,
        comparisons={key:v['maximum'] for key,v in comparisons.items()})
    path.write_text(json.dumps(dict(summary=summary,cases=rows,shared=shared,comparisons=comparisons,
        scaleSha256=sha,frequenciesHz=FREQ),indent=2,allow_nan=False))
    print('G3_SPATIAL_GATE '+json.dumps(summary),flush=True);assert gate
if __name__=='__main__':main()
