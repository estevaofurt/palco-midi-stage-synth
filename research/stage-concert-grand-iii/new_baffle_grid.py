"""G3.13b: new co-coordinate 80-mode baffle grid, frozen fit replay.
No retuning on this grid. New development and reserved check sets are
exported separately; higher frequencies remain diagnostic."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from structural_passive_fit import read_reference,contexts,structural_impedance,matrix_errors,TRAIN
from wire_physical_midpoint import load
from structural_region_decay import rebuild
from wire_baffle_reference import FREQ
from polygon_radiation import SurfaceModes
from enriched_baffle import samples,resistance
from surface_reactive_fft import cell_integrals,reactive
from radiation_resistance import pressure
from modal_string_radiation import response
from baffle_passive_fit import evaluate,audit
from acoustic_matrix_archive import read_npz
from split_radiation import relative
from dual_cavity_spatial_diagnostic import save_matrices

DEVELOPMENT=[42.,72.,108.,176.,208.,238.,255.,279.]
RESERVED=[58.,92.,132.,194.,258.,264.,292.]
EXTENSION=[330.,380.,440.,500.]
REPLAY=150.

def check_grid():
    groups=[DEVELOPMENT,RESERVED,EXTENSION,FREQ]
    if any(len(set(g))!=len(g) for g in groups) or any(set(g)&set(h) for i,g in enumerate(groups) for h in groups[i+1:]):
        raise ValueError('overlapping frequency grids')

def read_fit(root,sha,rh):
    raw=(root/'frozen_structural_passive.json').read_bytes();f=json.loads(raw)
    d=json.loads((root/'structural_passive_fit.json').read_text());s=d['summary']
    if d['frozenSha256']!=hashlib.sha256(raw).hexdigest() or f['sourceFrozenSha256']!=sha or f['referenceManifestSha256']!=rh or f['trainingHz']!=TRAIN:
        raise ValueError('fit provenance')
    if any(s.get(k)!=v for k,v in dict(gate=True,screeningFitGate=False,passivityGate=True,optimizationGate=True,fitRank=64,physicalAcousticFitAccepted=False).items()):
        raise ValueError('unexpected fit status')
    cfg=f['selected']['config'];n=1+len(cfg['relax'])+len(cfg['osc'])
    z=read_npz(root,f['archive'],dict(coefficients=(n,80,80),projection=(80,64)),TRAIN)
    if not audit(z['coefficients'],cfg)['gate']:raise ValueError('fit passivity')
    return z['coefficients'],cfg,hashlib.sha256(raw).hexdigest()

def coordinate_audit(local,archived):
    errors={k:relative(local[k],archived[k]) for k in ('stiffness','damping','ports','wirePorts','physicalLift','regionalDamping')}
    if max(errors.values())>1e-10:raise ValueError('coordinate mismatch: do not mix independent lifts')
    return errors

def kernel(f,grids,quad,mic):
    x0,w0,S0,x,w,S=quad
    R0,a=resistance(x0,w0,S0,f,12);R1,b=resistance(x,w,S,f,12);R,c=resistance(x,w,S,f,16)
    X0=reactive(*grids[120],f,8);X=reactive(*grids[240],f,8);X12=reactive(*grids[240],f,12)
    H0=pressure(x0,w0,S0,mic,f,1.204,343.);H=pressure(x,w,S,mic,f,1.204,343.)
    row=dict(frequencyHz=f,resistanceSpatial=relative(R0,R1),resistanceAngular=relative(R1,R),
        reactiveGrid=relative(X0,X),reactiveKernel=relative(X,X12),pressure=relative(H0,H),
        reciprocity=max(relative(X,X.T),relative(R,R.T)),
        passivityMin=min(t['passivityMinRelative'] for t in (a,b,c)))
    row['gate']=bool(max(row[k] for k in ('resistanceSpatial','resistanceAngular','reactiveKernel','pressure'))<=1e-6
        and row['reactiveGrid']<=.005 and row['reciprocity']<=1e-10 and row['passivityMin']>=-1e-10)
    return R+1j*(X+X.T)/2,H,row

def score_one(z,Z,H,f,C,cfg,ctx):
    B=z['fieldMap'];target=B.T@Z@B;observer=H@B
    fitted=evaluate([2j*np.pi*f],C,cfg)[0]
    e=matrix_errors(fitted[None],target[None])[0];cases=[];YY=[];OO=[]
    for i,(md,wires) in enumerate(ctx):
        Y,O,exact=response(md,z['wirePorts'],wires,target,observer,f)
        Yf,Of,fit=response(md,z['wirePorts'],wires,fitted,observer,f)
        if not exact['gate'] or not fit['gate']:raise ValueError('harmonic algebra')
        cases.append(dict(config=i,mobility=relative(Yf,Y),pressure=relative(Of,O),c4Pressure=relative(Of[:,2],O[:,2]),
            exactPower=exact['powerRelative'],fitPower=fit['powerRelative']))
        YY.append(Y);OO.append(O)
    row=dict(**e,cases=cases,maximumResponse=max(max(v[k] for k in ('mobility','pressure','c4Pressure')) for v in cases))
    row['maximum']=max(row['maximumResponse'],*(row[k] for k in ('impedance','resistance','reactance')))
    return row,np.stack(YY),np.stack(OO)

def main():
    p=argparse.ArgumentParser()
    for key in ('scale','source','surface','reference','fit','out'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();check_grid();archive,wires,sha=load(a.source,a.scale)
    z,rh=read_reference(a.reference,sha);C,cfg,fh=read_fit(a.fit,sha,rh)
    local={}
    def sink(plate,poly,lift):local.update(plate=plate,poly=poly,lift=lift)
    k,D,P,A,wires,G,lift,replay=rebuild(a.scale,a.surface,archive,wires,surface_sink=sink)
    ca=coordinate_audit(dict(stiffness=k,damping=D,ports=P,wirePorts=A,physicalLift=lift,regionalDamping=G),z)
    plate,poly=local['plate'],local['poly']
    field=SurfaceModes(plate,local['lift']@z['fieldVectors']/np.sqrt(z['fieldEigenvalues'])[None,:])
    quad=(*samples(plate,field,6),*samples(plate,field,8))
    x,w,S=quad[3:];gram=relative(S.T@(w[:,None]*S),np.eye(80))
    if gram>1e-7:raise ValueError('surface Gram')
    grids={}
    for n in (120,240):
        B,dx,dy,area=cell_integrals(poly,field,n)
        if abs(area-plate['areaM2'])/plate['areaM2']>1e-9:raise ValueError('grid area')
        grids[n]=(B,dx,dy)
    center=poly.mean(0);mic=np.array([[*center,.5],[center[0]+.25,center[1],1.5]])
    Z,H,rep=kernel(REPLAY,grids,quad,mic);j=FREQ.index(REPLAY)
    replayError=max(relative(Z,z['impedance'][j]),relative(H,z['pressure'][j]))
    if not rep['gate'] or replayError>1e-8:raise ValueError('archived acoustic replay')
    rows={v['key']:v for v in json.loads(a.scale.read_text())['rows']};ctx=contexts(z,wires,rows)
    a.out.mkdir(parents=True,exist_ok=True)
    summaries={}
    for role,freq in [('development',DEVELOPMENT),('reserved',RESERVED),('extension',EXTENSION)]:
        results=[];Zs=[];Hs=[];Ys=[];Os=[]
        for f in freq:
            Z,H,ker=kernel(f,grids,quad,mic)
            sc,Y,O=score_one(z,Z,H,f,C,cfg,ctx)
            row=dict(frequencyHz=f,kernel=ker,frozenFit=sc)
            results.append(row);Zs.append(Z);Hs.append(H);Ys.append(Y);Os.append(O)
            print('G3_NEW_BAFFLE_CASE '+json.dumps(dict(role=role,**row),allow_nan=False),flush=True)
        gate=all(v['kernel']['gate'] for v in results)
        desc=save_matrices(a.out,'new_baffle_'+role,frequencies=freq,impedance=np.stack(Zs),pressure=np.stack(Hs),
            mobility=np.stack(Ys,axis=1),observation=np.stack(Os,axis=1))
        s=dict(gate=gate,role=role,points=len(freq),maximumFrozenFitError=max(v['frozenFit']['maximum'] for v in results),
            frozenFitGate=bool(gate and max(v['frozenFit']['maximum'] for v in results)<=.05),
            maximumReactiveGrid=max(v['kernel']['reactiveGrid'] for v in results))
        summaries[role]=s
        (a.out/('new_baffle_'+role+'.json')).write_text(json.dumps(dict(summary=s,cases=results,frequenciesHz=freq,
            archive=desc,sourceFrozenSha256=sha,referenceManifestSha256=rh,fitFrozenSha256=fh),indent=2,allow_nan=False))
    summary=dict(gate=bool(summaries['development']['gate'] and summaries['reserved']['gate']),
        extensionGate=summaries['extension']['gate'],groups=summaries,coordinateReplay=ca,acousticReplay=replayError,
        normalizedGramRelative=gram,diagnosticOnly=True,calibratedParameters=False,fitRetuned=False,
        physicalAcousticFitAccepted=False,continuousFrequencyValidated=False,timeDomainReady=False,radiationReady=False)
    (a.out/'new_baffle_grid.json').write_text(json.dumps(dict(summary=summary,sourceFrozenSha256=sha,
        referenceManifestSha256=rh,fitFrozenSha256=fh),indent=2,allow_nan=False))
    print('G3_NEW_BAFFLE_GATE '+json.dumps(summary,allow_nan=False),flush=True)
    if not summary['gate']:raise ValueError('new primary reference convergence failed')
if __name__=='__main__':main()
