"""G3.12b: enriched-surface baffled radiation resistance and pressure.
Harmonic, one-sided ideal baffle only. No reactive load, enclosure,
causal fit, or physical calibration. Never reuse old four-field operators."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from acoustic_matrix_archive import read_npz
from hybrid_temporal_surface import surface_gram
from dry_structural_modal import read
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from spline_plate import assemble
from polygon_radiation import SurfaceModes
from radiation_resistance import hemisphere,pressure
from split_radiation import relative
from dual_cavity_spatial_diagnostic import save_matrices

def load_source(root,scale):
    raw=(root/'frozen_surface.json').read_bytes();f=json.loads(raw)
    d=json.loads((root/'hybrid_temporal_surface.json').read_text());s=d['summary']
    required=dict(gate=True,surfaceGate=True,rank=72,surfaceFields=72,surfaceNumericalRank=72,diagnosticOnly=True,
        physicalHypothesis=True,calibratedParameters=False,acousticCoordinatesChanged=True,oldAcousticOperatorsCompatible=False,
        acousticFitAccepted=False,timeDomainReady=False,radiationReady=False)
    if any(s.get(k)!=v for k,v in required.items()) or d['frozenSha256']!=hashlib.sha256(raw).hexdigest():raise ValueError('unapproved surface source')
    if hashlib.sha256(scale.read_bytes()).hexdigest()!=f['scaleSha256']:raise ValueError('scale mismatch')
    z=read_npz(root,f['archive'],dict(stiffness=(72,),damping=(72,72),ports=(72,4),physicalLift=(1386,72),
        gram=(72,72),fieldVectors=(72,72),fieldEigenvalues=(72,),fieldMap=(72,72)),f['trainingHz'])
    ev=z['fieldEigenvalues'];W=z['fieldVectors']
    if np.any(ev<=0) or relative(W.T@W,np.eye(72))>1e-8 or relative(np.sqrt(ev)[:,None]*W.T,z['fieldMap'])>1e-10:raise ValueError('inconsistent surface map')
    if relative(W.T@z['gram']@W,np.diag(ev))>1e-8:raise ValueError('inconsistent surface spectrum')
    return z,hashlib.sha256(raw).hexdigest()

def samples(plate,field,order):
    xy=[];w=[];S=[]
    for x,v,_ in plate['basis'].patches(order):
        xy.append(x);w.append(v);S.append(field(x))
    return np.concatenate(xy),np.concatenate(w),np.concatenate(S)

def resistance(xy,w,S,f,order,rho=1.204,c=343.):
    dirs,weights=hemisphere(order);A=np.ascontiguousarray(w[:,None]*S)
    omega=2*np.pi*f;k=omega/c
    B=np.zeros((S.shape[1],S.shape[1]),complex)
    # Bounded temporary size even for knot-aligned surface quadrature.
    for i in range(0,len(dirs),32):
        d=dirs[i:i+32,:2];z=np.zeros((len(d),S.shape[1]),complex)
        for j in range(0,len(xy),4096):
            x=xy[j:j+4096];z+=np.exp(1j*k*(d@x.T))@A[j:j+4096]
        B+=z.conj().T@(weights[i:i+32,None]*z)
    R=rho*omega**2/(4*np.pi**2*c)*B.real
    symmetry=float(np.linalg.norm(B.imag)/max(np.linalg.norm(B.real),1e-30))
    minimum=float(np.linalg.eigvalsh((R+R.T)/2).min()/max(np.linalg.norm(R),1e-30))
    return R,dict(imaginaryGramRelative=symmetry,reciprocity=relative(R,R.T),passivityMinRelative=minimum)

def harmonic(k,D,P,A,R,H,f):
    # Pure resistive reference at a single frequency; omits reactance.
    # This is not an accepted causal load or the full Rayleigh impedance.
    omega=2*np.pi*f;drag=D+A.T@R@A
    V=1j*omega*np.linalg.solve(np.diag(k-omega**2)+1j*omega*drag,P)
    Y=P.T@V;obs=H@A@V
    power=(Y+Y.conj().T)/2;wood=V.conj().T@D@V;air=V.conj().T@A.T@R@A@V
    err=relative(power,wood+air)
    return Y,obs,dict(powerRelative=err,reciprocity=relative(Y,Y.T),
        airFraction=float(np.trace(air).real/max(np.trace(power).real,1e-30)))

def main():
    p=argparse.ArgumentParser()
    for k in ('scale','source','out'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();z,sha=load_source(a.source,a.scale)
    sc=json.loads(a.scale.read_bytes());l=layout_build(sc,read('layout_hypothesis.json'));mat=read('board_interface_hypothesis.json')
    q=contour_build(l,read('board_contour_hypothesis.json'),mat);rib=read('ribbed_plate_hypothesis.json')['rib']
    poly=np.asarray(q['contourXY_m']);plate=assemble(poly,q['ribs'],mat['plate'],rib,30,14,False)
    ev=z['fieldEigenvalues'];W=z['fieldVectors'];A=z['fieldMap']
    field=SurfaceModes(plate,z['physicalLift'][:plate['rank']]@W/np.sqrt(ev)[None,:])
    x0,w0,S0=samples(plate,field,6);x1,w1,S1=samples(plate,field,8)
    gram=relative(S1.T@(w1[:,None]*S1),np.eye(72))
    area=abs(w1.sum()-plate['areaM2'])/plate['areaM2']
    if gram>1e-7 or area>1e-10:raise ValueError('surface reconstruction failed')
    center=poly.mean(0);mic=np.array([[center[0],center[1],.5],[center[0]+.25,center[1],1.5]])
    freq=[30.,150.,300.];rows=[];RR=[];HH=[];YY=[];OO=[]
    for f in freq:
        R0,r0=resistance(x0,w0,S0,f,12)
        R1,r1=resistance(x1,w1,S1,f,12)
        R2,r2=resistance(x1,w1,S1,f,16)
        H0=pressure(x0,w0,S0,mic,f,1.204,343.)
        H=pressure(x1,w1,S1,mic,f,1.204,343.)
        spatial=relative(R0,R1);angular=relative(R1,R2);obs=relative(H0,H)
        Y,O,rep=harmonic(z['stiffness'],z['damping'],z['ports'],A,R2,H,f)
        gate=bool(max(spatial,angular,obs)<=1e-6 and all(max(r['imaginaryGramRelative'],r['reciprocity'])<=1e-8 and r['passivityMinRelative']>=-1e-10 for r in (r0,r1,r2))
            and max(rep['powerRelative'],rep['reciprocity'])<=1e-8 and 0<=rep['airFraction']<=1+1e-10)
        row=dict(frequencyHz=f,spatialRelative=spatial,angularRelative=angular,pressureRelative=obs,
            resistanceAudit=r2,resistiveOnlyResponse=rep,gate=gate)
        rows.append(row);RR.append(R2);HH.append(H);YY.append(Y);OO.append(O)
        print('G3_ENRICHED_BAFFLE_CASE '+json.dumps(row),flush=True)
    a.out.mkdir(parents=True,exist_ok=True)
    entry=save_matrices(a.out,'enriched_baffle',frequencies=freq,resistance=np.stack(RR),pressure=np.stack(HH),mobility=np.stack(YY),observation=np.stack(OO))
    summary=dict(gate=all(v['gate'] for v in rows),diagnosticOnly=True,physicalHypothesis=True,calibratedParameters=False,
        fields=72,oneSidedIdealBaffle=True,resistanceOnly=True,reactanceIncluded=False,oldAcousticOperatorsCompatible=False,
        surfaceGramRelative=gram,areaRelative=area,maximumSpatialError=max(v['spatialRelative'] for v in rows),
        maximumAngularError=max(v['angularRelative'] for v in rows),maximumPressureError=max(v['pressureRelative'] for v in rows),
        acousticFitAccepted=False,timeDomainReady=False,radiationReady=False,polyphonyValidated=False)
    (a.out/'enriched_baffle.json').write_text(json.dumps(dict(summary=summary,cases=rows,archive=entry,
        sourceFrozenSha256=sha,frequenciesHz=freq,microphonesXYZ_m=mic.tolist(),surfaceOrders=[6,8],angularOrders=[12,16]),indent=2,allow_nan=False))
    print('G3_ENRICHED_BAFFLE_GATE '+json.dumps(summary),flush=True)
    if not summary['gate']:raise ValueError('enriched baffled resistance diagnostic failed')
if __name__=='__main__':main()
