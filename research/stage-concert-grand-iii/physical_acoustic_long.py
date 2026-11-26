"""G3.14d.17: diagnostic 40s C4 decay, frozen physical CQ.
Rejected attack remains rejected. No retuning, new damping, or EQ."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from wire_physical_midpoint import load
from structural_region_decay import rebuild
from acoustic_matrix_archive import read_npz
from retarded_local_reference import geometry
from physical_acoustic_audition import render
from physical_attack_comparison import checked
from causal_pressure_observer import build_kernel,stream_proof,harmonic_proof
from fixed_acoustic_projection import TRAIN,CHECK,NOVEL
from spectral_tail_audit import analyze
from sustain_brightness import fixed_thresholds
from attack_flutter import write_checked
from split_radiation import relative

RATE=48000
FREQ=list(TRAIN)+list(CHECK)+list(NOVEL)

def validate_coordinates(local,stored):
    # No mapping between independently constructed bases is assumed.
    errors={key:relative(value,stored[key]) for key,value in local.items()}
    if max(errors.values())>1e-7:raise ValueError('frozen CQ coordinate replay '+str(errors))
    return errors

def thresholds(y,reference):
    s=analyze(y,RATE,60)
    return dict(own=[dict(channel=c['channel'],fundamental=c['fundamentalThresholds'],total=c['totalThresholds']) for c in s['channels']],
        common=fixed_thresholds(s,reference),spectrum=s)

def main():
    p=argparse.ArgumentParser()
    for name in ('scale','source','surface','cq','out'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--speed',type=float,choices=(.3,3.),required=True)
    a=p.parse_args();archive,wires,sha=load(a.source,a.scale)
    raw=(a.cq/'physical_cq.json').read_bytes();s=json.loads(raw)['summary']
    expected=dict(gate=True,screeningGate=True,rate=RATE,rank=64,weightsGenerated=True,sourceFrozenSha256=sha,independentCoordinatesMixed=False)
    if any(s.get(k)!=v for k,v in expected.items()):raise ValueError('CQ prerequisite')
    z=read_npz(a.cq,s['archive'],dict(weights=(1024,64,64),projection=(80,64),stiffness=(80,),
        damping=(80,80),ports=(80,7),wirePorts=(10,80),physicalLift=(1386,80)),FREQ)
    fraw=(a.cq/'local_cq_projection.json').read_bytes();f=json.loads(fraw)
    if hashlib.sha256(fraw).hexdigest()!=s['localProjectionFrozenSha256'] or f['sourceFrozenSha256']!=sha:raise ValueError('projection identity')
    local={}
    def sink(plate,poly,lift):local.update(plate=plate,poly=poly,lift=lift)
    k,D,P,A,wires,G,lift,replay=rebuild(a.scale,a.surface,archive,wires,surface_sink=sink)
    if [w.id for w in wires]!=f['wireIds']:raise ValueError('wire identity')
    checks=validate_coordinates(dict(stiffness=k,damping=D,ports=P,wirePorts=A,physicalLift=lift),z)
    B,_,quad,_,mic,_=geometry(local['plate'],local['poly'],local['lift']);xy,w,S=quad[3:];S=S@B
    K,support,_=build_kernel(xy,w,S,mic,RATE,3);proof=stream_proof(K,RATE,support)
    harm=harmonic_proof(K,RATE,xy,w,S,mic,FREQ)
    band=max(max(v['accelerationRelative'],v['velocityRelative']) for v in harm)
    if not proof['gate'] or band>.005:raise ValueError('pressure observer')
    folder=a.cq/'audition';aud=json.loads((folder/'physical_audition.json').read_text());sm=aud['summary']
    if any(sm.get(key)!=v for key,v in dict(gate=True,cases=4,seconds=5,rate=RATE,rank=64,noOutputEQ=True,
        sourceFrozenSha256=sha,projectionFrozenSha256=s['localProjectionFrozenSha256']).items()):raise ValueError('audition prerequisite')
    rows={v['key']:v for v in json.loads(a.scale.read_text())['rows']}
    gain=sm['commonGain'];a.out.mkdir(parents=True,exist_ok=True)
    # The prior 5s strong dry reference provides the same absolute peak
    # for weak and strong, as in the earlier nominal sustain comparison.
    strong=next(v for v in aud['cases'] if v['speed']==3. and not v['wet'])
    ref=checked(folder,strong['native'],5)
    # analyze() needs ten seconds; zero-padding does not alter its 1s
    # windows or the maximum across the existing first five.
    strongRef=analyze(np.pad(ref,((0,5*RATE),(0,0))),RATE,60)
    results=[]
    for wet in (False,True):
        old=next(v for v in aud['cases'] if v['speed']==a.speed and v['wet']==wet)
        original=checked(folder,old['native'],5)
        y,row=render(k,D,A,wires,rows,z['projection'],z['weights'],K,RATE,a.speed,wet,seconds=40.)
        err=relative(y[:5*RATE],original)
        if err>1e-6:raise ValueError('5s audition replay '+str(err))
        metrics=thresholds(y,strongRef);row.update(metrics);row['firstFiveSecondsReplayRelative']=err
        label='C4_'+('weak' if a.speed==.3 else 'strong')+'_'+('wet' if wet else 'dry')
        row['listen']=write_checked(a.out/(label+'_40s.wav'),y,RATE,False,gain)
        row['native']=write_checked(a.out/(label+'_pressure_40s.wav'),y,RATE,True,gain)
        results.append(row)
        print('G3_PHYSICAL_LONG_CASE '+json.dumps({k:v for k,v in row.items() if k not in ('spectrum','pressureEnvelope','hammerContacts','attackBands')},allow_nan=False),flush=True)
    summary=dict(gate=True,diagnosticOnly=True,seconds=40,rate=RATE,speed=a.speed,cases=2,
        sourceFrozenSha256=sha,cqManifestSha256=hashlib.sha256(raw).hexdigest(),coordinateReplay=checks,
        pressureBandMaximum=band,commonGain=gain,commonThresholdReference='first 5s strong dry',
        attackPreviouslyRejected=True,noOutputEQ=True,physicalFeedbackAccepted=False,
        audibleSustainMeasured=False,above500HzDiagnosticOnly=True,wholeEngineRealtimeValidated=False)
    (a.out/'physical_long_decay.json').write_text(json.dumps(dict(summary=summary,cases=results),indent=2,allow_nan=False))
    print('G3_PHYSICAL_LONG_GATE '+json.dumps(summary,allow_nan=False),flush=True)
def same_basis_long(out,prior,k,D,A,wires,rows,U,W,geom,rate,refs,sourceHash,projectionHash,cqRoot,speed):
    # Never read prior mechanical matrices into the current reconstruction.
    # Compare only physical pressure outputs at the shared microphones.
    from dual_cavity_spatial_diagnostic import save_matrices
    if rate!=RATE:raise ValueError('rate')
    raw=(cqRoot/'physical_cq.json').read_bytes();s=json.loads(raw)['summary'];sha=sourceHash
    priorCQ=json.loads((prior/'physical_cq.json').read_text())['summary']
    if any(v.get('screeningGate') is not True or v.get('sourceFrozenSha256')!=sha for v in (s,priorCQ)):raise ValueError('CQ scope')
    if s['localProjectionFrozenSha256']!=projectionHash:raise ValueError('local projection identity')
    B,_,quad,_,mic,_=geom;xy,w,S=quad[3:];S=S@B
    K,support,_=build_kernel(xy,w,S,mic,RATE,3);proof=stream_proof(K,RATE,support)
    harm=harmonic_proof(K,RATE,xy,w,S,mic,FREQ)
    band=max(max(v['accelerationRelative'],v['velocityRelative']) for v in harm)
    if not proof['gate'] or band>.005:raise ValueError('pressure observer')
    out.mkdir(parents=True,exist_ok=True)
    pressureEntry=save_matrices(out,'same_basis_pressure',frequencies=FREQ,kernel=K,support=support,microphones=mic)
    print('G3_PHYSICAL_LONG_OBSERVER '+json.dumps(dict(archive=pressureEntry,projectionFrozenSha256=projectionHash,bandMaximum=band),allow_nan=False),flush=True)
    folder=prior/'audition';aud=json.loads((folder/'physical_audition.json').read_text());sm=aud['summary']
    if any(sm.get(key)!=v for key,v in dict(gate=True,cases=4,seconds=5,rate=RATE,rank=64,noOutputEQ=True,
        sourceFrozenSha256=sha,projectionFrozenSha256=priorCQ['localProjectionFrozenSha256']).items()):raise ValueError('audition prerequisite')
    gain=sm['commonGain'];out.mkdir(parents=True,exist_ok=True)
    # The prior 5s strong dry reference provides the same absolute peak
    # for weak and strong, as in the earlier nominal sustain comparison.
    strong=next(v for v in aud['cases'] if v['speed']==3. and not v['wet'])
    ref=checked(folder,strong['native'],5)
    # analyze() needs ten seconds; zero-padding does not alter its 1s
    # windows or the maximum across the existing first five.
    strongRef=analyze(np.pad(ref,((0,5*RATE),(0,0))),RATE,60)
    results=[]
    for wet in (False,True):
        old=next(v for v in aud['cases'] if v['speed']==speed and v['wet']==wet)
        original=checked(folder,old['native'],5)
        y,row=render(k,D,A,wires,rows,U,W,K,RATE,speed,wet,seconds=40.)
        err=relative(y[:5*RATE],original)
        if err>1e-6:raise ValueError('5s audition replay '+str(err))
        metrics=thresholds(y,strongRef);row.update(metrics);row['firstFiveSecondsReplayRelative']=err
        label='C4_'+('weak' if speed==.3 else 'strong')+'_'+('wet' if wet else 'dry')
        row['listen']=write_checked(out/(label+'_40s.wav'),y,RATE,False,gain)
        row['native']=write_checked(out/(label+'_pressure_40s.wav'),y,RATE,True,gain)
        results.append(row)
        print('G3_PHYSICAL_LONG_CASE '+json.dumps({k:v for k,v in row.items() if k not in ('spectrum','pressureEnvelope','hammerContacts','attackBands')},allow_nan=False),flush=True)
    summary=dict(gate=True,diagnosticOnly=True,seconds=40,rate=RATE,speed=speed,cases=2,
        sourceFrozenSha256=sha,cqManifestSha256=hashlib.sha256(raw).hexdigest(),sameBasis=True,pressureArchive=pressureEntry,
        pressureBandMaximum=band,commonGain=gain,commonThresholdReference='first 5s strong dry',
        attackPreviouslyRejected=True,noOutputEQ=True,physicalFeedbackAccepted=False,
        audibleSustainMeasured=False,above500HzDiagnosticOnly=True,wholeEngineRealtimeValidated=False)
    (out/'physical_long_decay.json').write_text(json.dumps(dict(summary=summary,cases=results),indent=2,allow_nan=False))
    print('G3_PHYSICAL_LONG_GATE '+json.dumps(summary,allow_nan=False),flush=True)
if __name__=='__main__':main()
