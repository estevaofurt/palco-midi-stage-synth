"""Use canonical enriched trace on the validated graded wedge.
Reproduce its polynomial trace and compare restricted acoustic responses
on exactly the same discretization, independently of exterior loading.
"""
import argparse,hashlib,json,time
from pathlib import Path
import numpy as np
from scipy.linalg import block_diag
from enriched_smooth_diagnostic import require_sources,read
from enriched_aperture_reference import enrich,restrict
from graded_cavity_replay import require_sources as require_geometry
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from recess_envelope import build as envelope
from hybrid_cavity import build,response
from port_coordinates import transform
from acoustic_port_bridge import compatible
from nested_acoustic_ports import project
from wedge_surface_trace import trace_matrix
from acoustic_trace_resolution import describe,panel_capture
from dual_cavity_spatial_diagnostic import FREQ,save_matrices
from split_radiation import relative

def enriched_trace(u,old,panels,screen):
    E,br=transform(u['panels'],old[:6],order=18);assert max(br.values())<=1e-8
    base=u['Cfull']@E;cols=[];rows=[];xyz=u['full']['xyz']
    for i,(faces,panel) in enumerate(zip(u['full']['apertureFaces'],panels[:6])):
        assert compatible(u['panels'][i],old[i])
        nodes,iv=np.unique(faces,return_inverse=True);f=iv.reshape(faces.shape);x=xyz[nodes]
        C=trace_matrix(panel,x,f,order=10);D=trace_matrix(panel,x,f,order=14)
        quad=relative(C,D);prefix=relative(D[:,:55],base[nodes,55*i:55*(i+1)])
        assert quad<=1e-8 and prefix<=1e-8
        G,_=panel_capture(x,f,D,panel);capture=describe(G)
        assert capture['minimumCapturedEnergy']>=.95 and abs(capture['minimumCapturedEnergy']-screen['panels'][i]['full']['minimumCapturedEnergy'])<=1e-8
        T=np.zeros((len(xyz),panel.basis.count));T[nodes]=D;cols.append(T)
        rows.append(dict(panel=i,quadratureRelative=quad,prefixRelative=prefix,**capture))
    return np.column_stack(cols),rows,block_diag(np.eye(4),E)

def main():
    p=argparse.ArgumentParser()
    for key in ('scale','consolidated','geometry','trace','out'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--angle',type=float,choices=[30.,55.],required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sha=hashlib.sha256(raw).hexdigest();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    ex=json.loads(a.consolidated.read_text());tr=json.loads(a.trace.read_text());screen=require_sources(ex,tr,a.angle,sha)
    geom,_=require_geometry(json.loads(a.geometry.read_text()),tr,ex,a.angle,sha)
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.asarray(q['contourXY_m']);g=geometry(poly,l,read('cabinet_geometry_hypothesis.json'));mic=np.asarray(g['microphonesXYZ_m'])
    def field(xy):
        x,y=(2*(xy-poly.min(0))/np.ptp(poly,axis=0)-1).T
        return np.stack([np.ones(len(x)),x,y,x*y],axis=1)
    _,old,_,geo=envelope(poly,g['rimTopZ_m'],g['rimBottomZ_m'],a.angle,55,field,55);assert geo['gate']
    panels,counts,idx,basis=enrich(old)
    u=build(poly,40,1,g['rimTopZ_m'],a.angle,field,55,wedge_layers=24,boundary_n=160,edge_grading=.5,layer_grading=.5)
    assert u['report']['nodes']==geom['nodes'] and u['report']['tetrahedra']==geom['tetrahedra']
    C,traces,E=enriched_trace(u,old,panels,screen);rim=len(u['full']['xyz'])-u['C'].shape[0]
    assert C.shape[1]==374 and np.linalg.norm(C[:rim])<=1e-12
    m=dict(u,C=C[rim:],Cfull=C,panels=panels[:6])
    ui=np.r_[np.arange(4),4+idx[:330]]
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'enriched_upper.json';rows=[];ZZ=[];PP=[]
    for f in FREQ:
        start=time.perf_counter();Z,P,r=response(m,f,mic,solver='schur-real');assert r['gate']
        # The restricted trace and equations match the polynomial solve;
        # verify independently at the band endpoints.
        check=None
        if f in (FREQ[0],FREQ[-1]):
            z,p,rr=response(u,f,mic,solver='schur-real');assert rr['gate'];z,p=project(z,p,E)
            check=dict(impedance=relative(restrict(Z,ui),z),pressure=relative(P[:,ui],p))
            assert max(check.values())<=1e-8
        rows.append(dict(frequencyHz=f,upper=r,polynomialRestriction=check,seconds=time.perf_counter()-start));ZZ.append(Z);PP.append(P)
        path.write_text(json.dumps(dict(cases=rows,trace=traces,complete=False,scaleSha256=sha),indent=2,allow_nan=False))
        print('G3_ENRICH_UPPER_CASE '+json.dumps(rows[-1]),flush=True)
    archive=save_matrices(a.out,'enriched_upper',frequencies=FREQ,Zu=np.stack(ZZ),Pu=np.stack(PP))
    summary=dict(gate=True,angleDeg=a.angle,diagnosticOnly=True,modes=374,width=.06,counts=counts[:6],
        minimumCapture=min(v['minimumCapturedEnergy'] for v in traces),algebraicStabilityGate=True,
        modalConvergenceCertified=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,trace=traces,polynomialIndices=ui.tolist(),archive=archive,scaleSha256=sha,frequenciesHz=FREQ),indent=2,allow_nan=False))
    print('G3_ENRICH_UPPER_GATE '+json.dumps(summary),flush=True)
if __name__=='__main__':main()
