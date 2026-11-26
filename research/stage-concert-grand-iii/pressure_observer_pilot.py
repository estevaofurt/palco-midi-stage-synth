"""G3.11v: archive pressure observations on nine audited frequencies.
Stable real-pole-pair observer fit is an independent sparse pilot, not
a calibrated microphone or accepted load. No feedback from observer."""
import argparse,hashlib,json,itertools
from pathlib import Path
import numpy as np
from scipy.linalg import block_diag
from acoustic_matrix_archive import read_npz,replay_full,modal_replay
from high_modal_allocation import require_archive,read
from fixed_355_validation import require_fine
from new_frequency_validation import require_basis,NEW,FREQ
from frozen_basis_replay import require_120,require_new
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from dual_cavity_spatial_diagnostic import compare_spatial,save_matrices
from split_radiation import relative

def extract(a):
    raw=a.scale.read_bytes();sha=hashlib.sha256(raw).hexdigest();sc=json.loads(raw)
    assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    d120=json.loads((a.basis120/'common_snapshot_transfer.json').read_text());require_120(d120,a.angle,sha)
    raw168=(a.basis168/'fixed_snapshot_transfer.json').read_bytes()
    d168=json.loads(raw168);require_basis(d168,a.angle,sha)
    maps={}
    for n,d,root,nu in ((120,d120,a.basis120,96),(168,d168,a.basis168,144)):
        b=read_npz(root,d['archive'],dict(Tu=(330,nu),Tl=(55,24),areas=(7,)),FREQ)
        T=block_diag(b['Tu'],b['Tl'])
        if np.iscomplexobj(T) or relative(T.T@T,np.eye(n))>1e-8 or np.any(b['areas']<=0):raise ValueError('invalid basis')
        maps[n]=b
    areas=maps[120]['areas']
    if relative(areas,maps[168]['areas'])>1e-10:raise ValueError('area mismatch')
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    nm=len(geometry(np.asarray(q['contourXY_m']),l,read('cabinet_geometry_hypothesis.json'))['microphonesXYZ_m'])
    if a.new:
        d=json.loads((a.new/'new_frequency_validation.json').read_text())
        require_new(d,a.angle,sha,hashlib.sha256(raw168).hexdigest())
        freq=list(NEW);nf=len(freq)
        z=read_npz(a.new,d['archive'],dict(Zu=(nf,334,334),Pu=(nf,nm,334),Zl=(nf,59,59),Pl=(nf,2,59),Ze=(nf,385,385),Pe=(nf,2,385),Y=(nf,4,4),flow=(nf,385,4)),freq)
    else:
        if not all((a.archive,a.consolidated,a.fine)):raise ValueError('missing fine reference')
        d=json.loads((a.archive/'dual_cavity_high_modal.json').read_text());require_archive(d,a.angle,sha)
        fd=json.loads((a.fine/'graded_combined_refinement.json').read_text());require_fine(fd,a.angle,sha)
        ed=json.loads((a.consolidated/'consolidated_exterior.json').read_text());s=ed['summary']
        if ed['scaleSha256']!=sha or ed['frequenciesHz']!=FREQ or any(s.get(k)!=v for k,v in dict(gate=True,angleDeg=a.angle,approvedBlocks=28,sampledBlockQuadratureApproved=True,radiationReady=False).items()):
            raise ValueError('invalid exterior')
        freq=FREQ;nf=len(freq)
        sh=read_npz(a.archive,d['shared'],dict(areas=(7,),Zl=(nf,59,59),Pl=(nf,2,59),Ze=(nf,385,385),Pe=(nf,2,385)),freq)
        ex=read_npz(a.consolidated,ed['archive'],dict(Ze=(nf,385,385),Y=(nf,4,4),flow=(nf,385,4)),freq)
        if relative(sh['areas'],areas)>1e-10 or not np.array_equal(sh['Ze'].real,ex['Ze'].real):raise ValueError('reference mismatch')
        z=read_npz(a.fine,fd['archive'],dict(Zu=(nf,334,334),Pu=(nf,nm,334),Y=(nf,4,4),flow=(nf,385,4)),freq)
        z.update(Zl=sh['Zl'],Pl=sh['Pl'],Ze=ex['Ze'],Pe=sh['Pe'])

    full=[];red=[];replay=[]
    for i,f in enumerate(freq):
        x=tuple(z[k][i] for k in ('Zu','Pu','Zl','Pl','Ze','Pe'))
        y,rep=replay_full(*x,z['Y'][i],z['flow'][i],4);full.append(y);replay.append(rep)
        b=maps[120];v,_=modal_replay(x,b['Tu'],b['Tl'],4,[55]*7,areas,y);red.append(v)
    comp=compare_spatial(freq,red,full,[55]*7,areas)
    if not comp['gate']:raise ValueError('120 mode observation comparison failed')
    a.out.mkdir(parents=True,exist_ok=True)
    data={}
    for prefix,rows in (('full',full),('reduced',red)):
        for j,key in enumerate(('upper','lower','exterior'),1):data[prefix+'_'+key]=np.stack([x[j] for x in rows])
    archive=save_matrices(a.out,'pressure_observation',frequencies=freq,**data)
    source_root=a.new if a.new else a.fine
    source_name='new_frequency_validation.json' if a.new else 'graded_combined_refinement.json'
    summary=dict(gate=True,angleDeg=a.angle,diagnosticOnly=True,referenceModes=385,reducedModes=120,
        independentFrequencies=bool(a.new),maximum=comp['maximum'],timeDomainReady=False,radiationReady=False)
    (a.out/'pressure_observation.json').write_text(json.dumps(dict(summary=summary,frequenciesHz=freq,scaleSha256=sha,
        sourceManifestSha256=hashlib.sha256((source_root/source_name).read_bytes()).hexdigest(),
        basisManifestSha256=hashlib.sha256((a.basis120/'common_snapshot_transfer.json').read_bytes()).hexdigest(),
        upperMicrophones=nm,archive=archive,replay=replay),indent=2,allow_nan=False))
    print('G3_PRESSURE_OBSERVATION_GATE '+json.dumps(summary),flush=True)

def dictionary(freq,k,g):
    # Stable, strictly proper real transfer functions, pairs of numerator
    # terms sharing a damped oscillator denominator. No passivity claim
    # for a non-power-conjugate output map.
    s=2j*np.pi*np.asarray(freq,float)[:,None];w=2*np.pi*np.linspace(35,310,k)[None,:]
    den=s*s+2*(2*np.pi*g)*s+w*w
    return np.concatenate([w*w/den,w*s/den],axis=1)

def fit(freq,Y,cfg):
    k,g,r=cfg;D=dictionary(freq,k,g)
    Y=np.asarray(Y,complex)
    w=1/np.maximum(np.linalg.norm(Y.reshape(len(Y),-1),axis=1),1e-30)
    D=D*w[:,None];norm=np.linalg.norm(D,axis=0);D/=norm
    A=np.concatenate([D.real,D.imag]);B=Y.reshape(len(Y),-1)*w[:,None];B=np.concatenate([B.real,B.imag])
    X=np.linalg.solve(A.T@A+r*np.eye(2*k),A.T@B)/norm[:,None]
    return X.reshape((2*k,)+Y.shape[1:])

def predict(freq,C,cfg):
    return np.einsum('fk,kij->fij',dictionary(freq,*cfg[:2]),C)

def errors(freq,Y,C,cfg):
    return [dict(frequencyHz=float(f),relative=relative(x,y)) for f,x,y in zip(freq,predict(freq,C,cfg),Y)]

def select(freq,groups):
    rows=[]
    for cfg in itertools.product((2,3,4),(5.,15.,35.),(1e-4,1e-2)):
        fold=[]
        for i,f in enumerate(freq):
            ix=np.arange(len(freq))!=i
            er={key:errors([f],Y[i:i+1],fit(np.asarray(freq)[ix],Y[ix],cfg),cfg)[0]['relative'] for key,Y in groups.items()}
            fold.append(dict(frequencyHz=float(f),errors=er))
        values=[v for row in fold for v in row['errors'].values()]
        rows.append(dict(config=list(cfg),maximumInner=max(values),meanInner=float(np.mean(values)),folds=fold))
    return min(rows,key=lambda x:(x['maximumInner'],x['meanInner'],x['config'])),rows

def read_observation(root,independent):
    raw=(root/'pressure_observation.json').read_bytes();d=json.loads(raw);s=d['summary'];freq=list(NEW) if independent else FREQ
    if d['frequenciesHz']!=freq or any(s.get(k)!=v for k,v in dict(gate=True,diagnosticOnly=True,referenceModes=385,reducedModes=120,
        independentFrequencies=independent,timeDomainReady=False,radiationReady=False).items()):raise ValueError('invalid observation evidence')
    n=len(freq);nm=d['upperMicrophones']
    shapes={p+'_'+k:(n,m,4) for p in ('full','reduced') for k,m in (('upper',nm),('lower',2),('exterior',2))}
    return d,read_npz(root,d['archive'],shapes,freq),hashlib.sha256(raw).hexdigest()

def pilot(fine,new,out):
    a,A,ha=read_observation(fine,False);b,B,hb=read_observation(new,True)
    if any(a[k]!=b[k] for k in ('scaleSha256','basisManifestSha256','upperMicrophones')) or a['summary']['angleDeg']!=b['summary']['angleDeg']:raise ValueError('observer provenance mismatch')
    train=a['frequenciesHz'];valid=b['frequenciesHz']
    if set(train)&set(valid):raise ValueError('overlap')
    groups={k:A['full_'+k] for k in ('upper','lower','exterior')}
    selected,candidates=select(train,groups);cfg=tuple(selected['config'])
    C={k:fit(train,Y,cfg) for k,Y in groups.items()}
    out.mkdir(parents=True,exist_ok=True)
    archive=save_matrices(out,'observer_coefficients',frequencies=train,**C)
    frozen=dict(selected=selected,archive=archive,trainingHz=train,sourceManifestSha256=ha)
    raw=json.dumps(frozen,indent=2,allow_nan=False).encode();(out/'frozen_observer.json').write_bytes(raw)
    training={k:errors(train,Y,C[k],cfg) for k,Y in groups.items()}
    validation={k:errors(valid,B['full_'+k],C[k],cfg) for k in groups}
    tr=max(v['relative'] for rows in training.values() for v in rows);va=max(v['relative'] for rows in validation.values() for v in rows)
    summary=dict(gate=True,diagnosticOnly=True,sparsePilot=True,angleDeg=a['summary']['angleDeg'],trainingPoints=len(train),validationPoints=len(valid),
        selectionUsedValidation=False,stableStrictlyProper=True,selectedConfig=list(cfg),maximumTrainingError=tr,maximumInnerError=selected['maximumInner'],
        maximumValidationError=va,sampledFitGate=bool(max(tr,va,selected['maximumInner'])<=.05),physicalFitAccepted=False,
        continuousFrequencyValidated=False,timeDomainReady=False,radiationReady=False)
    (out/'observer_pilot.json').write_text(json.dumps(dict(summary=summary,training=training,validation=validation,candidates=candidates,
        frozenSha256=hashlib.sha256(raw).hexdigest(),validationManifestSha256=hb),indent=2,allow_nan=False))
    print('G3_OBSERVER_PILOT_GATE '+json.dumps(summary),flush=True)

def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='mode',required=True)
    e=sub.add_parser('extract')
    for k in ('scale','basis120','basis168','out'):e.add_argument('--'+k,type=Path,required=True)
    for k in ('new','archive','consolidated','fine'):e.add_argument('--'+k,type=Path)
    e.add_argument('--angle',type=float,choices=[30.,55.],required=True)
    f=sub.add_parser('pilot')
    for k in ('fine','new','out'):f.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args()
    if a.mode=='extract':extract(a)
    else:pilot(a.fine,a.new,a.out)
if __name__=='__main__':main()
