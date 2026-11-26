"""Combined upper-volume refinement, fixed 385-mode basis and exterior.
Geometry audit first; do not certify absolute convergence from two meshes."""
import argparse,hashlib,json,time
from pathlib import Path
import numpy as np
from scipy.linalg import block_diag
from high_modal_allocation import require_archive,read
from graded_reference_audit import require_graded
from acoustic_matrix_archive import read_npz,replay_full
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from recess_envelope import build as envelope
from graded_volume_mesh import build as geometry_build,audit
from hybrid_cavity import build,response
from port_coordinates import transform
from acoustic_port_bridge import compatible
from nested_acoustic_ports import project
from acoustic_trace_resolution import panel_capture,describe
from dual_cavity_reference import couple
from dual_cavity_spatial_diagnostic import FREQ,compare_spatial,save_matrices
from split_radiation import relative

def select_screen(doc,angle,sha):
    s=doc['summary']
    if doc['scaleSha256']!=sha or s['angleDeg']!=angle or not s['gate'] or not s['diagnosticOnly'] or not s['surfaceOnly'] or s['radiationReady']:
        raise ValueError('invalid surface evidence')
    rows=[r for r in doc['cases'] if (r['boundaryN'],r['wedgeLayers'],r['edgeGrading'],r['layerGrading'],r['width'])==(200,32,.5,.5,.06)]
    if len(rows)!=1 or not rows[0]['screenGate'] or rows[0]['minimumCapture']<.95:raise ValueError('fine trace not approved')
    return rows[0]

def main():
    p=argparse.ArgumentParser()
    for key in ('scale','archive','consolidated','graded','trace','out'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--angle',type=float,choices=[30.,55.],required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sha=hashlib.sha256(raw).hexdigest();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    doc=json.loads((a.archive/'dual_cavity_high_modal.json').read_text());require_archive(doc,a.angle,sha)
    gd=json.loads((a.graded/'graded_cavity_replay.json').read_text());require_graded(gd,a.angle,sha)
    ex=json.loads((a.consolidated/'consolidated_exterior.json').read_text());s=ex['summary']
    assert ex['scaleSha256']==sha and ex['frequenciesHz']==FREQ and s['gate'] and s['angleDeg']==a.angle and s['approvedBlocks']==28 and not s['radiationReady']
    screen=select_screen(json.loads(a.trace.read_text()),a.angle,sha)
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.asarray(q['contourXY_m']);g=geometry(poly,l,read('cabinet_geometry_hypothesis.json'));height=g['rimTopZ_m'];mic=np.asarray(g['microphonesXYZ_m']);nf=len(FREQ)
    def field(xy):
        x,y=(2*(xy-poly.min(0))/np.ptp(poly,axis=0)-1).T
        return np.stack([np.ones(len(x)),x,y,x*y],axis=1)
    _,ports,_,geo=envelope(poly,height,g['rimBottomZ_m'],a.angle,55,field,55);assert geo['gate'] and len(ports)==7
    areas=np.array([v.basis.area for v in ports]);counts=[55]*7
    sh=read_npz(a.archive,doc['shared'],dict(areas=(7,),Zl=(nf,59,59),Pl=(nf,2,59),Ze=(nf,385,385),Pe=(nf,2,385)),FREQ)
    gr=read_npz(a.graded,gd['archive'],dict(Zu=(nf,334,334),Pu=(nf,len(mic),334),Y=(nf,4,4),flow=(nf,385,4)),FREQ)
    ext=read_npz(a.consolidated,ex['archive'],dict(Ze=(nf,385,385),Y=(nf,4,4),flow=(nf,385,4)),FREQ)
    assert relative(areas,sh['areas'])<=1e-10 and np.array_equal(ext['Ze'].real,sh['Ze'].real)
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'graded_combined_refinement.json'
    n,b,k=50,200,32
    m=geometry_build(poly,n,b,k,height,a.angle,.5,.5);geom=audit(m,poly,b,k,height,a.angle,.5,.5);del m
    assert geom['gate'] and geom['apertureFaces']==screen['traceFaces']
    path.write_text(json.dumps(dict(geometry=geom,complete=False,scaleSha256=sha),indent=2,allow_nan=False))
    print('G3_COMBINED_GEOMETRY '+json.dumps(geom),flush=True)
    u=build(poly,n,1,height,a.angle,field,55,wedge_layers=k,boundary_n=b,edge_grading=.5,layer_grading=.5)
    assert u['report']['nodes']==geom['nodes'] and u['report']['tetrahedra']==geom['tetrahedra'] and u['report']['faces']==geom['apertureFaces']
    assert all(compatible(x,y) for x,y in zip(u['panels'],ports[:6]))
    E,br=transform(u['panels'],ports[:6],order=18);assert max(br.values())<=1e-8;Eu=block_diag(np.eye(4),E)
    trace=[]
    for i,(faces,panel) in enumerate(zip(u['full']['apertureFaces'],u['panels'])):
        G,nodes=panel_capture(u['full']['xyz'],faces,u['Cfull'][:,55*i:55*(i+1)],panel);d=describe(G)
        assert d['minimumCapturedEnergy']>=.95 and abs(d['minimumCapturedEnergy']-screen['panels'][i]['polynomial']['minimumCapturedEnergy'])<=1e-8
        trace.append(dict(panel=i,nodes=nodes,**d))
    old=[];new=[];rows=[];ZZ=[];PP=[]
    for i,f in enumerate(FREQ):
        start=time.perf_counter();x=tuple(v[i] for v in (gr['Zu'],gr['Pu'],sh['Zl'],sh['Pl'],ext['Ze'],sh['Pe']))
        y,_=replay_full(*x,gr['Y'][i],gr['flow'][i],4);old.append(y)
        Z,P,r=response(u,f,mic,solver='schur-real');assert r['gate'];Z,P=project(Z,P,Eu)
        *v,c=couple(Z,P,*x[2:],4,reference_kind='common-free-space-monopole');assert c['gate']
        new.append(tuple(v));ZZ.append(Z);PP.append(P);rows.append(dict(frequencyHz=f,upper=r,coupled=c,seconds=time.perf_counter()-start))
        path.write_text(json.dumps(dict(geometry=geom,trace=trace,cases=rows,complete=False,scaleSha256=sha),indent=2,allow_nan=False))
        print('G3_COMBINED_CASE '+json.dumps(rows[-1]),flush=True)
    comp=compare_spatial(FREQ,old,new,counts,areas)
    archive=save_matrices(a.out,'combined_upper',frequencies=FREQ,Zu=np.stack(ZZ),Pu=np.stack(PP),Y=np.stack([v[0] for v in new]),flow=np.stack([v[-1] for v in new]))
    summary=dict(gate=True,angleDeg=a.angle,diagnosticOnly=True,upperConfig=[n,b,k],baselineConfig=[40,160,24],modes=385,
        combinedUpperRefinementGate=comp['gate'],comparison=comp['maximum'],minimumCapture=min(v['minimumCapturedEnergy'] for v in trace),
        lowerFixed=True,exteriorFixed=True,modalConvergenceCertified=False,fullCabinetReady=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,geometry=geom,trace=trace,cases=rows,comparison=comp,archive=archive,scaleSha256=sha,frequenciesHz=FREQ),indent=2,allow_nan=False))
    print('G3_COMBINED_GATE '+json.dumps(summary),flush=True)
if __name__=='__main__':main()
