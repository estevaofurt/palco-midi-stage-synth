"""G3.11d: independently evaluate new frequencies, frozen 168-mode basis.
No frequency interpolation or fitting; reproduce full common-monopole
operators at each new point and audit quadrature before coupling."""
import argparse,hashlib,json,time
from pathlib import Path
import numpy as np
from scipy.linalg import block_diag
from high_modal_allocation import read
from spatial_layout import build as layout_build
from board_contour import build as contour_build,properties
from cabinet_geometry import geometry
from recess_envelope import build as envelope
from hybrid_cavity import build as upper_build,response as upper_response
from lower_prism import build as lower_build,response as lower_response
from acoustic_port_bridge import compatible
from port_coordinates import transform
from nested_acoustic_ports import project
from high_modal_remaining_reactive import classify
from enriched_reactive_diagnostic import audit_block
from exterior_angular_panels import angular_panels
from lid_exterior import pressure
from dual_cavity_reference import couple
from dual_cavity_spatial_diagnostic import FREQ,compare_spatial,save_matrices
from acoustic_matrix_archive import read_npz,modal_replay
from fixed_355_validation import require_fine,valid_metrics
from split_radiation import relative

NEW=(55.,175.,275.)

def require_basis(d,angle,sha):
    s=d.get('summary',{})
    expected=dict(gate=True,angleDeg=angle,diagnosticOnly=True,rank=24,modes=168,referenceModes=385,
        trainingMesh=[40,160,24],validationMesh=[50,200,32],fixedBasis=True,trainedOnFine=False,
        independentUpperMeshValidated=True,continuousFrequencyValidated=False,timeDomainReady=False,modalConvergenceCertified=False,radiationReady=False)
    if d.get('scaleSha256')!=sha or d.get('frequenciesHz')!=FREQ or any(s.get(k)!=v for k,v in expected.items()) or set(s.get('maximum',{}))!={'coarseModal','fineModal','fullSpatial','reducedSpatial','combined'} or not all(valid_metrics(v) for v in s['maximum'].values()):
        raise ValueError('invalid frozen basis')
    if set(NEW)&set(FREQ):raise ValueError('validation frequency leaked into training')

def main():
    p=argparse.ArgumentParser()
    for key in ('scale','basis','fine','out'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--angle',type=float,choices=[30.,55.],required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sha=hashlib.sha256(raw).hexdigest();sc=json.loads(raw)
    assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    fd=json.loads((a.fine/'graded_combined_refinement.json').read_text());require_fine(fd,a.angle,sha)
    bd=json.loads((a.basis/'fixed_snapshot_transfer.json').read_text());require_basis(bd,a.angle,sha)
    b=read_npz(a.basis,bd['archive'],dict(Tu=(330,144),Tl=(55,24),areas=(7,)),FREQ)
    T=block_diag(b['Tu'],b['Tl'])
    if np.iscomplexobj(T) or relative(T.T@T,np.eye(168))>1e-8:raise ValueError('invalid orthogonal basis')
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.asarray(q['contourXY_m']);g=geometry(poly,l,read('cabinet_geometry_hypothesis.json'))
    h=-g['rimBottomZ_m'];_,center,_=properties(poly);mic=np.asarray(g['microphonesXYZ_m'])
    lp=np.array([np.r_[center,-h*.25],np.r_[center,-h*.75]])
    far=np.array([[poly[:,0].max()+2.,poly[:,1].mean(),1.5],[poly[:,0].mean(),poly[:,1].max()+2.,-.8]])
    def field(xy):
        x,y=(2*(xy-poly.min(0))/np.ptp(poly,axis=0)-1).T
        return np.stack([np.ones(len(x)),x,y,x*y],axis=1)
    _,ports,_,geo=envelope(poly,g['rimTopZ_m'],g['rimBottomZ_m'],a.angle,55,field,55)
    areas=np.array([v.basis.area for v in ports]);counts=[55]*7
    assert geo['gate'] and relative(areas,b['areas'])<=1e-10
    inv=classify(ports);assert len(inv)==28
    freq=list(NEW);omega=2*np.pi*np.array(freq);k=omega/343.;factor=1.204*omega/(4*np.pi)
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'new_frequency_validation.json'
    X=np.zeros((len(freq),385,385));react=[]
    for i,j,kind in inv:
        start=time.perf_counter()
        v,rep=audit_block(ports[i],ports[j],k,kind)
        row=dict(panel=i,otherPanel=j,kind=kind,**rep,seconds=time.perf_counter()-start)
        react.append(row)
        I=slice(55*i,55*(i+1));J=slice(55*j,55*(j+1));X[:,I,J]=v
        if i!=j:X[:,J,I]=v.transpose(0,2,1)
        print('G3_NEW_FREQ_REACTIVE '+json.dumps(row,allow_nan=False),flush=True)
        path.write_text(json.dumps(dict(complete=False,reactive=react,scaleSha256=sha),indent=2,allow_nan=False))
    if not all(r['gate'] for r in react):raise ValueError('new frequency reactive quadrature failed')
    parts={}
    for order in (30,42):
        parts[order]=[]
        for panel in ports:
            _,x,w,A=panel.samples(order);parts[order].append((x,w[:,None]*A))
    exterior=[];smooth=[]
    for i,f in enumerate(freq):
        G0,_=angular_panels(parts[30],k[i],32);G1,_=angular_panels(parts[42],k[i],32);G2,_=angular_panels(parts[42],k[i],40)
        P0=pressure(ports,np.eye(385),far,f,30);P1=pressure(ports,np.eye(385),far,f,42)
        R=factor[i]*k[i]*G2
        rep=dict(surface=relative(G0,G1),angular=relative(G1,G2),observer=relative(P0,P1),
            passivity=float(np.linalg.eigvalsh(R).min()/max(np.linalg.norm(R),1e-30)))
        rep['gate']=max(rep['surface'],rep['angular'],rep['observer'])<=1e-8 and rep['passivity']>=-1e-10
        smooth.append(dict(frequencyHz=f,**rep));exterior.append((R+1j*factor[i]*X[i],P1))
    if not all(r['gate'] for r in smooth):raise ValueError('new frequency smooth quadrature failed')
    low=lower_build(poly,72,h,field,55);assert compatible(low['mouth'],ports[-1])
    E,br=transform([low['mouth']],ports[-1:],order=18);assert max(br.values())<=1e-8
    El=block_diag(np.eye(4),E);lower=[];lr=[]
    for f in freq:
        Z,P,r=lower_response(low,2j*np.pi*f,lp);assert r['gate'];lower.append(project(Z,P,El));lr.append(r)
    del low
    upper=upper_build(poly,50,1,g['rimTopZ_m'],a.angle,field,55,wedge_layers=32,boundary_n=200,edge_grading=.5,layer_grading=.5)
    assert all(compatible(x,y) for x,y in zip(upper['panels'],ports[:6]))
    E,br=transform(upper['panels'],ports[:6],order=18);assert max(br.values())<=1e-8
    Eu=block_diag(np.eye(4),E);full=[];reduced=[];reports=[];ops=[]
    for i,f in enumerate(freq):
        Z,P,ur=upper_response(upper,f,mic,solver='schur-real');assert ur['gate']
        x=(*project(Z,P,Eu),*lower[i],*exterior[i]);*y,cr=couple(*x,4,reference_kind='common-free-space-monopole');assert cr['gate']
        z,rr=modal_replay(x,b['Tu'],b['Tl'],4,counts,areas,y)
        full.append(tuple(y));reduced.append(z);ops.append(x);reports.append(dict(frequencyHz=f,upper=ur,lower=lr[i],coupled=cr,reduced=rr))
        print('G3_NEW_FREQ_CASE '+json.dumps(dict(frequencyHz=f,gate=cr['gate']),allow_nan=False),flush=True)
    comp=compare_spatial(freq,reduced,full,counts,areas)
    archive=save_matrices(a.out,'new_frequency_operators',frequencies=freq,**{k:np.stack([x[i] for x in ops]) for i,k in enumerate(('Zu','Pu','Zl','Pl','Ze','Pe'))},
        Y=np.stack([v[0] for v in full]),flow=np.stack([v[-1] for v in full]))
    summary=dict(gate=comp['gate'],angleDeg=a.angle,diagnosticOnly=True,referenceModes=385,reducedModes=168,frozenBasis=True,
        heldOutFrequencies=freq,trainingFrequencies=FREQ,approvedReactiveBlocks=len(react),continuousFrequencyValidated=False,
        modalConvergenceCertified=False,timeDomainReady=False,radiationReady=False,maximum=comp['maximum'])
    path.write_text(json.dumps(dict(summary=summary,reactive=react,smooth=smooth,reports=reports,comparison=comp,archive=archive,
        basisManifestSha256=hashlib.sha256((a.basis/'fixed_snapshot_transfer.json').read_bytes()).hexdigest(),scaleSha256=sha,frequenciesHz=freq),indent=2,allow_nan=False))
    print('G3_NEW_FREQ_GATE '+json.dumps(summary),flush=True)
    if not comp['gate']:raise ValueError('frozen basis failed independent frequency test')
if __name__=='__main__':main()
