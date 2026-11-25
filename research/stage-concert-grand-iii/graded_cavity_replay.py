"""Isolate the effect of graded upper volume at fixed 385-mode coordinates
and the consolidated sampled exterior. No enriched functions are used yet.
"""
import argparse,hashlib,json,time
from pathlib import Path
import numpy as np
from scipy.linalg import block_diag
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from hybrid_cavity import build as upper_build,response as upper_response
from recess_envelope import build as envelope
from acoustic_port_bridge import compatible
from port_coordinates import transform
from nested_acoustic_ports import project
from acoustic_trace_resolution import panel_capture,describe
from high_modal_allocation import require_archive
from acoustic_matrix_archive import read_npz,replay_full
from dual_cavity_reference import couple
from dual_cavity_spatial_diagnostic import FREQ,compare_spatial,save_matrices
from split_radiation import relative
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())

def require_sources(geo,trace,ext,angle,sha):
    for d,keys in ((geo,dict(geometryOnly=True,volumeMeshGeometryValidated=True)),(trace,dict(surfaceOnly=True)),(ext,dict(approvedBlocks=28,sampledBlockQuadratureApproved=True,resistanceUnchanged=True))):
        s=d.get('summary',{})
        if d.get('scaleSha256')!=sha or any(s.get(k)!=v for k,v in dict(gate=True,angleDeg=angle,diagnosticOnly=True,radiationReady=False,**keys).items()):
            raise ValueError('invalid graded replay prerequisite')
    rows=[r for r in geo['cases'] if (r['interiorN'],r['boundaryN'],r['wedgeLayers'],r['edgeGrading'],r['layerGrading'])==(40,160,24,.5,.5)]
    cases=[r for r in trace['cases'] if (r['boundaryN'],r['wedgeLayers'],r['edgeGrading'],r['layerGrading'],r['width'])==(160,24,.5,.5,.06)]
    if len(rows)!=1 or len(cases)!=1 or not rows[0]['gate'] or not cases[0]['screenGate']:raise ValueError('selected mesh not validated')
    return rows[0],cases[0]

def main():
    p=argparse.ArgumentParser()
    for key in ('scale','archive','consolidated','geometry','trace','out'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--angle',type=float,choices=[30.,55.],required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sha=hashlib.sha256(raw).hexdigest();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    doc=json.loads((a.archive/'dual_cavity_high_modal.json').read_text());require_archive(doc,a.angle,sha)
    ex=json.loads((a.consolidated/'consolidated_exterior.json').read_text())
    geom,screen=require_sources(json.loads(a.geometry.read_text()),json.loads(a.trace.read_text()),ex,a.angle,sha)
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.asarray(q['contourXY_m']);g=geometry(poly,l,read('cabinet_geometry_hypothesis.json'));mic=np.asarray(g['microphonesXYZ_m']);nf=len(FREQ)
    def field(xy):
        x,y=(2*(xy-poly.min(0))/np.ptp(poly,axis=0)-1).T
        return np.stack([np.ones(len(x)),x,y,x*y],axis=1)
    _,ports,_,geo=envelope(poly,g['rimTopZ_m'],g['rimBottomZ_m'],a.angle,55,field,55);assert geo['gate'] and len(ports)==7
    areas=np.array([v.basis.area for v in ports]);counts=[55]*7
    sh=read_npz(a.archive,doc['shared'],dict(areas=(7,),Zl=(nf,59,59),Pl=(nf,2,59),Ze=(nf,385,385),Pe=(nf,2,385)),FREQ)
    up=read_npz(a.archive,doc['upper'],dict(Zu=(nf,334,334),Pu=(nf,len(mic),334),Y=(nf,4,4),flow=(nf,385,4)),FREQ)
    prior=read_npz(a.consolidated,ex['archive'],dict(Ze=(nf,385,385),Y=(nf,4,4),flow=(nf,385,4)),FREQ)
    assert relative(areas,sh['areas'])<=1e-10 and np.array_equal(prior['Ze'].real,sh['Ze'].real)
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'graded_cavity_replay.json'
    u=upper_build(poly,40,1,g['rimTopZ_m'],a.angle,field,55,wedge_layers=24,boundary_n=160,edge_grading=.5,layer_grading=.5)
    assert u['report']['gate'] and u['report']['nodes']==geom['nodes'] and u['report']['tetrahedra']==geom['tetrahedra'] and u['report']['faces']==geom['apertureFaces']
    assert len(u['panels'])==6 and all(compatible(x,y) for x,y in zip(u['panels'],ports[:6]))
    E,br=transform(u['panels'],ports[:6],order=18);assert max(br.values())<=1e-8;Eu=block_diag(np.eye(4),E)
    traces=[]
    for i,(faces,panel) in enumerate(zip(u['full']['apertureFaces'],u['panels'])):
        G,n=panel_capture(u['full']['xyz'],faces,u['Cfull'][:,55*i:55*(i+1)],panel);d=describe(G)
        assert d['minimumCapturedEnergy']>=.95 and abs(d['minimumCapturedEnergy']-screen['panels'][i]['polynomial']['minimumCapturedEnergy'])<=1e-8
        traces.append(dict(panel=i,nodes=n,**d))
    old=[];new=[];reports=[];Zs=[];Ps=[]
    for i,f in enumerate(FREQ):
        start=time.perf_counter();x=tuple(v[i] for v in (up['Zu'],up['Pu'],sh['Zl'],sh['Pl'],prior['Ze'],sh['Pe']))
        y,_=replay_full(*x,prior['Y'][i],prior['flow'][i],4);old.append(y)
        Z,P,ur=upper_response(u,f,mic,solver='schur-real');assert ur['gate'];Zu,Pu=project(Z,P,Eu)
        v=(Zu,Pu,*x[2:]);*out,cr=couple(*v,4,reference_kind='common-free-space-monopole');assert cr['gate']
        new.append(tuple(out));Zs.append(Zu);Ps.append(Pu)
        row=dict(frequencyHz=f,seconds=time.perf_counter()-start,upper=ur,coupled=cr,
            upperMatrixRelative=relative(x[0],Zu),upperObserverRelative=relative(x[1],Pu))
        reports.append(row);print('G3_GRADED_CAVITY_CASE '+json.dumps(row),flush=True)
        path.write_text(json.dumps(dict(reports=reports,trace=traces,complete=False,scaleSha256=sha),indent=2,allow_nan=False))
    comp=compare_spatial(FREQ,old,new,counts,areas)
    archive=save_matrices(a.out,'graded_upper',frequencies=FREQ,Zu=np.stack(Zs),Pu=np.stack(Ps),Y=np.stack([v[0] for v in new]),flow=np.stack([v[-1] for v in new]))
    summary=dict(gate=True,angleDeg=a.angle,diagnosticOnly=True,upperConfig=[40,160,24],edgeGrading=.5,layerGrading=.5,
        modes=385,minimumPolynomialCapture=min(x['minimumCapturedEnergy'] for x in traces),reusedLowerAndExterior=True,
        algebraicStabilityGate=True,gradedVsUniformGate=comp['gate'],comparison=comp['maximum'],
        modalConvergenceCertified=False,fullCabinetReady=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,reports=reports,trace=traces,comparison=comp,archive=archive,frequenciesHz=FREQ,scaleSha256=sha),indent=2,allow_nan=False))
    print('G3_GRADED_CAVITY_GATE '+json.dumps(summary),flush=True)
if __name__=='__main__':main()
