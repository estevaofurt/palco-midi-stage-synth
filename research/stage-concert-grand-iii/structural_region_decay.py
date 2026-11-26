"""G3.12v: locate structural dissipation by physical subassembly.
Rebuild the 80-dimensional basis locally, verify observable replay against
the frozen model, then project each PSD damping block in that SAME basis."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from scipy.linalg import cholesky,solve_triangular
from enriched_baffle import load_source
from dry_structural_modal import read
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from bridge_strings import centerline
from spline_plate import assemble
from structural_assembly import assemble as structure
from string_structure import setup
from dry_snapshot_reduction import normalized
from dry_hybrid_reduction import response_columns
from wire_port_enrichment import rebuild_base,enrich_basis,model,development_grids,comparison
from wire_physical_midpoint import CoupledWire,load
from physical_long_decay import startup
from physical_loss_sensitivity import prepare,simulate,crossings,NAMES
from felt_law import params
from split_radiation import relative
from dual_cavity_spatial_diagnostic import save_matrices

REGIONS=('plateAndRibs','rim','bridges','wiresAndDampers')

def project_regions(D,V,sizes):
    if sum(sizes)!=len(D) or min(sizes)<=0 or V.shape[0]!=len(D):raise ValueError('region dimensions')
    result=[];start=0;mask=np.zeros_like(D)
    for n in sizes:
        sl=slice(start,start+n);local=D[sl,sl];U=V[sl]
        x=U.T@local@U;result.append((x+x.T)/2);mask[sl,sl]=local;start+=n
    if relative(mask,D)>1e-12:raise ValueError('nonlocal damping blocks')
    G=np.stack(result);target=V.T@D@V
    error=relative(G.sum(axis=0),target)
    mins=[float(np.linalg.eigvalsh(x).min()/max(np.linalg.norm(x),1e-30)) for x in G]
    if error>1e-10 or min(mins)<-1e-10:raise ValueError('projected loss partition')
    return G,dict(reconstructionRelative=error,minimumEigenvalueRelative=mins)

def rebuild(scale,surface,archive,wires,surface_sink=None):
    old,sha=load_source(surface,scale);raw=scale.read_bytes();sc=json.loads(raw)
    rows={v['key']:v for v in sc['rows']}
    l=layout_build(sc,read('layout_hypothesis.json'));mat=read('board_interface_hypothesis.json')
    c=contour_build(l,read('board_contour_hypothesis.json'),mat);rib=read('ribbed_plate_hypothesis.json')['rib']
    poly=np.asarray(c['contourXY_m']);centers={s:centerline(l['bridgeAttachmentNodes'][s]) for s in ('bass','treble')}
    plate=assemble(poly,c['ribs'],mat['plate'],rib,30,14,False)
    q=structure(plate,centers,read('bridge_hypothesis.json'),mat,read('rim_structure_hypothesis.json'),2,8,14,True)
    M=q['M'];K=q['K']+q['Jrim']+q['Jbridge'];D=q['D']
    grid=np.asarray(json.loads((surface/'frozen_surface.json').read_text())['trainingHz'])
    base,audit=rebuild_base(M,K,D,q['P'][:,[0,2,4,5]],old,grid)
    if not audit['gate']:raise ValueError('base replay')
    P,ww,labels=setup(q,centers,rows,[45,48,60,64],2,128)
    if [w.id for w in ww]!=[w.id for w in wires]:raise ValueError('wire order changed')
    rear=sorted(set(w.rear for w in ww));F=np.zeros((len(M),len(rear)));F[rear,np.arange(len(rear))]=1.
    train,inner,outer=development_grids()
    s=1/np.sqrt(np.diag(M));L=cholesky((K+(2*np.pi*100)**2*M)*(s[:,None]*s[None,:]),lower=True)
    T,_=np.linalg.qr(L.T@(base/s[:,None]),mode='reduced')
    m,k,d,f=normalized(M,K,D,F);S=response_columns(m,k,d,f,train)
    V=enrich_basis(T,S,8);physical=s[:,None]*solve_triangular(L.T,V,lower=False)
    md,A,mass=model(M,K,D,P,physical)
    if len(md['M'])!=80:raise ValueError('unexpected rank')
    k=np.diag(md['K']);d=md['D'];P=md['P'];B=np.stack([A[w.rear] for w in ww])
    # Compare transfer functions, NEVER identify columns from separate assemblies.
    freq=np.sort(np.r_[train,inner,outer]);replays=[]
    for n in (16,32,128):
        x=CoupledWire(k,d,P,B,ww,48000,n)
        y=CoupledWire(archive['stiffness'],archive['damping'],archive['ports'],archive['wirePorts'],wires,48000,n)
        replays.append(dict(partials=n,**comparison(x.transfer(freq),y.transfer(freq))))
    if max(v['maximum'] for v in replays)>1e-5:raise ValueError('local wire transfer replay')
    G,partition=project_regions(D,A,[q['plateDofs'],q['rimDofs'],sum(q['bridgeDofs'])])
    if relative(G.sum(axis=0),d)>1e-10:raise ValueError('structural damping replay')
    if surface_sink is not None:surface_sink(plate,poly,A[:q['plateDofs']])
    return k,d,P,B,ww,G,A,dict(base=audit,massRelative=mass,transferReplay=replays,partition=partition,
        plateDofs=q['plateDofs'],rimDofs=q['rimDofs'],bridgeDofs=q['bridgeDofs'],surfaceSourceSha256=sha)

def factors():
    base=[(1.,1.,1.)]
    for j in range(3):
        x=[1.]*3;x[j]=.25;base.append(tuple(x))
    return base+[(.25,.25,.25),(.1,.1,.1),(.5,.5,.5)]

def full_partition(m,G):
    size=len(m.M);n=m.a.n
    A=np.zeros((4,size,size));A[:3,:n,:n]=G
    A[3]=m.D-A[:3].sum(axis=0);A[3]=(A[3]+A[3].T)/2
    if relative(A.sum(axis=0),m.D)>1e-10 or min(np.linalg.eigvalsh(x).min()/max(np.linalg.norm(x),1e-30) for x in A)<-1e-8:
        raise ValueError('full loss partition')
    return A

def rename(result):
    def names(v):return dict(zip(REGIONS,[v[k] for k in NAMES]))
    result['lossFractions']=names(result['lossFractions'])
    for row in result['snapshots']:row['lossFractions']=names(row['lossFractions'])
    return result

def main():
    p=argparse.ArgumentParser()
    for key in ('scale','source','surface','sensitivity','out'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();archive,wires,sha=load(a.source,a.scale)
    raw=(a.sensitivity/'physical_loss_sensitivity.json').read_bytes();d=json.loads(raw);s=d['summary']
    if d['sourceFrozenSha256']!=sha or any(s.get(k)!=v for k,v in dict(gate=True,cases=36,acousticLoadIncluded=False,calibratedParameters=False).items()):raise ValueError('unapproved sensitivity')
    k,D,P,A,wires,G,lift,audit=rebuild(a.scale,a.surface,archive,wires)
    print('G3_STRUCTURAL_REGION_REPLAY '+json.dumps(audit,allow_nan=False),flush=True)
    rows={v['key']:v for v in json.loads(a.scale.read_text())['rows']}
    pars=[params(k,rows[k]['count'],read('physical_sources.json'),read('felt_hypothesis.json')) for k in (45,48,60,64)]
    groups=[w.port for w in wires];masses=[x['massKg'] for x,_ in pars];felts=[pars[g][1] for g in groups];rows['_platePort']=P[:,6]
    cases=[];rate=48000
    for n in (16,32):
        states=[startup(k,D,A,wires,rows,groups,masses,felts,rate,n,1.,v) for v in (.3,3.)]
        m,q,v,O,_=states[0];J=full_partition(m,G);ref=None
        for cfg in factors():
            prepared=prepare(m.M,m.K,J*np.asarray([*cfg,1.])[:,None,None],O,1/rate,2400)
            pending=[]
            for speed,(other,q,v,o,init) in zip((.3,3.),states):
                if not np.array_equal(other.D,m.D) or not np.array_equal(o,O):raise ValueError('inconsistent attack')
                result,rms=simulate(prepared,q,v);pending.append((speed,rename(result),rms))
            if ref is None:ref=pending[-1][2].max(axis=0)
            for speed,result,rms in pending:
                row=dict(partials=n,rate=rate,pedal=1.,hammerSpeedMps=speed,factors=dict(zip(REGIONS[:3],cfg)),
                    **result,referencePeakRmsMps=ref.tolist(),commonReferenceThresholds={name:crossings(rms[:,i],ref[i]) for i,name in enumerate(('wire','plate'))})
                if cfg==(1.,1.,1.):
                    prior=next(v for v in d['cases'] if v['partials']==n and v['pedal']==1. and v['hammerSpeedMps']==speed and all(x==1. for x in v['factors'].values()))
                    err=abs(result['initialEnergyJ']/prior['initialEnergyJ']-1.)
                    expected=prior['lossFractions']['structure'];actual=sum(result['lossFractions'][x] for x in REGIONS[:3])
                    err=max(err,abs(expected-actual))
                    if err>1e-5:raise ValueError('nominal decay replay')
                    row['nominalReplayRelative']=err
                cases.append(row)
                print('G3_STRUCTURAL_REGION_CASE '+json.dumps({k:v for k,v in row.items() if k!='snapshots'},allow_nan=False),flush=True)
    summary=dict(gate=all(v['gate'] for v in cases),cases=len(cases),diagnosticOnly=True,physicalHypothesis=True,
        structureRank=80,wires=10,localBasisRebuilt=True,selectedParameters=None,calibratedParameters=False,
        maximumTransferReplay=max(v['maximum'] for v in audit['transferReplay']),maximumBalanceError=max(v['balanceRelative'] for v in cases),
        maximumNominalReplay=max(v['nominalReplayRelative'] for v in cases if 'nominalReplayRelative' in v),
        acousticLoadIncluded=False,audibleSustainMeasured=False,timeDomainReady=False,radiationReady=False,polyphonyValidated=False)
    a.out.mkdir(parents=True,exist_ok=True)
    desc=save_matrices(a.out,'regional_structure',frequencies=development_grids()[0],stiffness=k,damping=D,ports=P,
        physicalLift=lift,wirePorts=A,regionalDamping=G)
    (a.out/'structural_region_decay.json').write_text(json.dumps(dict(summary=summary,audit=audit,cases=cases,archive=desc,
        sourceFrozenSha256=sha,sensitivityManifestSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_STRUCTURAL_REGION_GATE '+json.dumps(summary),flush=True)
    if not summary['gate']:raise ValueError('regional decay proof failed')
if __name__=='__main__':main()
