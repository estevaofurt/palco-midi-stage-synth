"""G3.14d.16: independent comparison of acoustic audition to nominal attack.
Only reads integrity-checked pressure WAVs; no sound generation or tuning."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from scipy.io.wavfile import read
from attack_flutter import envelope_metrics
from sustain_brightness import attack_bands,attack_compare
from split_radiation import relative

RATE=48000
def checked(root,item,seconds):
    name=item['file']
    if Path(name).name!=name:raise ValueError('invalid WAV name')
    path=root/name
    if hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('WAV hash')
    rate,y=read(path)
    if rate!=RATE or y.dtype!=np.float32 or y.shape!=(round(seconds*RATE),2) or not np.isfinite(y).all() or not np.any(y):raise ValueError('pressure format')
    return y.astype(float)

def bands(y):
    # Compare absolute RMS per 1s window, in Pa. Fundamental is a
    # narrow FFT band (not a calibrated loudness or audible threshold).
    rows=[]
    for i in range(len(y)//RATE):
        x=y[i*RATE:(i+1)*RATE];w=np.hanning(len(x))
        p=abs(np.fft.rfft(x*w[:,None],axis=0))**2
        p[1:-1]*=2.;p/=len(x)*np.sum(w*w)
        f=np.fft.rfftfreq(len(x),1/RATE)
        rows.append(dict(startS=i,fundamentalRmsPa=np.sqrt(p[(f>=250)&(f<=273)].sum(axis=0)).tolist(),
            lowRmsPa=np.sqrt(p[(f>=30)&(f<=500)].sum(axis=0)).tolist(),
            totalRmsPa=np.sqrt(p.sum(axis=0)).tolist()))
    return rows

def compare(y,ref):
    a=envelope_metrics(y[:2*RATE],RATE,60);b=envelope_metrics(ref[:2*RATE],RATE,60)
    ripple=[]
    for x,z in zip(a['fundamental'],b['fundamental']):
        v=x['rippleRmsDb'];r=z['rippleRmsDb']
        ripple.append(dict(currentDb=v,referenceDb=r,gate=bool(v is not None and r is not None and v<=max(1.10*r,r+.15))))
    attack=attack_compare(attack_bands(y),attack_bands(ref))
    return dict(waveformRelative2s=relative(y[:2*RATE],ref[:2*RATE]),attack=attack,ripple=ripple,
        attackScreeningGate=bool(attack['gate'] and all(x['gate'] for x in ripple)))

def main():
    p=argparse.ArgumentParser()
    for k in ('cq','approved','out'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    cq=json.loads((a.cq/'physical_cq.json').read_text())['summary'];folder=a.cq/'audition'
    if cq.get('screeningGate') is not True:
        report=dict(gate=True,blockedBy='physical CQ screening',audioCompared=False)
        (a.out/'attack_comparison.json').write_text(json.dumps(report));print('G3_PHYSICAL_ATTACK_COMPARE '+json.dumps(report),flush=True);return
    doc=json.loads((folder/'physical_audition.json').read_text());s=doc['summary']
    old=json.loads((a.approved/'attack_flutter.json').read_text());os=old['summary']
    if any(s.get(k)!=v for k,v in dict(gate=True,cases=4,rate=RATE,rank=64,seconds=5,noOutputEQ=True,localBasis=True).items()):raise ValueError('audition scope')
    if any(os.get(k)!=v for k,v in dict(gate=True,key=60,acousticFeedbackIncluded=False,noOutputEQ=True,sourceFrozenSha256=cq['sourceFrozenSha256']).items()):raise ValueError('approved source scope')
    if s['sourceFrozenSha256']!=cq['sourceFrozenSha256'] or s['projectionFrozenSha256']!=cq['localProjectionFrozenSha256']:raise ValueError('audition provenance')
    result=[]
    for speed in (.3,3.):
        oldrow=next(v for v in old['results'] if v['variant']=='nominal_structure' and v['speed']==speed)
        reference=checked(a.approved,oldrow['native'],2)
        dryrow=next(v for v in doc['cases'] if v['speed']==speed and not v['wet'])
        wetrow=next(v for v in doc['cases'] if v['speed']==speed and v['wet'])
        dry=checked(folder,dryrow['native'],5);wet=checked(folder,wetrow['native'],5)
        d=compare(dry,reference);w=compare(wet,reference);local=compare(wet,dry)
        row=dict(speed=speed,dryVsApproved=d,wetVsApproved=w,wetVsDry=local,dryWindows=bands(dry),wetWindows=bands(wet),
            dryAcousticWorkJ=dryrow['acousticWorkJ'],wetAcousticWorkJ=wetrow['acousticWorkJ'],
            dryReferenceReplayGate=bool(d['waveformRelative2s']<=1e-6))
        result.append(row)
        print('G3_PHYSICAL_ATTACK_CASE '+json.dumps(row,allow_nan=False),flush=True)
    report=dict(gate=True,diagnosticOnly=True,audioCompared=True,cases=2,
        dryReferenceReplayGate=all(x['dryReferenceReplayGate'] for x in result),
        wetAttackScreeningGate=all(x['wetVsApproved']['attackScreeningGate'] and x['wetVsDry']['attackScreeningGate'] for x in result),
        sourceFrozenSha256=s['sourceFrozenSha256'],projectionFrozenSha256=s['projectionFrozenSha256'],
        listenerApproved=False,audibleSustainMeasured=False,physicalFeedbackAccepted=False,
        above500HzDiagnosticOnly=True,noOutputEQ=True)
    (a.out/'attack_comparison.json').write_text(json.dumps(dict(summary=report,cases=result),indent=2,allow_nan=False))
    print('G3_PHYSICAL_ATTACK_COMPARE '+json.dumps(report,allow_nan=False),flush=True)
if __name__=='__main__':main()
