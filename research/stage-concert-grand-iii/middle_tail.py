"""G3.13m: compare medium-band residuals in already rendered physical WAVs.
Diagnostic only. No signal processing applied to audition files."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from scipy.io.wavfile import read
from scipy.signal import find_peaks

TARGETS=(220.,327.,669.,783.,791.,1719.,1838.,1957.,2315.,2897.)
def analyze(y,rate,key,reference=None):
    y=np.asarray(y,dtype=float)
    if y.ndim!=2 or y.shape[1]!=2 or len(y)<10*rate or not np.isfinite(y).all():raise ValueError('pressure WAV')
    f0=440*2**((key-69)/12);f=np.fft.rfftfreq(rate,1/rate);w=np.hanning(rate)
    fundamental=abs(f-f0)<=max(5.,.008*f0)
    middle=(f>=250)&(f<1500)&~fundamental
    upper=f>=1500
    bands=dict(fundamental=fundamental,middle=middle,upper=upper)
    out=[]
    for ch in range(2):
        windows=[]
        for t in range(len(y)//rate):
            x=y[t*rate:(t+1)*rate,ch];p=abs(np.fft.rfft(x*w))**2
            p[1:-1]*=2;p/=rate*np.sum(w*w)
            total=float(p.sum())
            e={k:float(p[m].sum()) for k,m in bands.items()}
            pk,_=find_peaks(p)
            pk=pk[(f[pk]>=250)&(f[pk]<1500)&~fundamental[pk]]
            pk=pk[np.argsort(p[pk])[::-1]][:5]
            peaks=[dict(hz=float(f[i]),fraction=float(p[abs(f-f[i])<=4].sum()/max(total,1e-300)),
                rmsPa=float(np.sqrt(p[abs(f-f[i])<=4].sum()))) for i in pk]
            windows.append(dict(timeS=t,totalRmsPa=float(np.sqrt(total)),
                bandRmsPa={k:float(np.sqrt(v)) for k,v in e.items()},
                bandFraction={k:v/max(total,1e-300) for k,v in e.items()},
                targets={str(int(hz)):dict(rmsPa=float(np.sqrt(p[abs(f-hz)<=4].sum())),
                    fraction=float(p[abs(f-hz)<=4].sum()/max(total,1e-300))) for hz in TARGETS},
                middlePeaks=peaks))
        peak=max(v['totalRmsPa'] for v in windows)
        fund=max(v['bandRmsPa']['fundamental'] for v in windows)
        if min(peak,fund)<=0:raise ValueError('no reference signal')
        common=peak if reference is None else reference[ch]['peakRmsPa']
        fundref=fund if reference is None else reference[ch]['fundamentalPeakRmsPa']
        for v in windows:
            v['totalDbCommon']=float(20*np.log10(max(v['totalRmsPa']/common,1e-30)))
            v['middleDbCommon']=float(20*np.log10(max(v['bandRmsPa']['middle']/common,1e-30)))
            v['fundamentalDbCommon']=float(20*np.log10(max(v['bandRmsPa']['fundamental']/fundref,1e-30)))
        late=[v for v in windows if v['timeS']>=1]
        flagged=[v for v in late if v['middleDbCommon']>=-80 and v['bandFraction']['middle']>=.3]
        # 30% is a diagnostic warning, not a psychoacoustic audibility gate.
        out.append(dict(channel=ch+1,peakRmsPa=peak,fundamentalPeakRmsPa=fund,
            middleEnergyAfter1s=float(sum(v['bandRmsPa']['middle']**2 for v in late)),
            middleEnergyAfter5s=float(sum(v['bandRmsPa']['middle']**2 for v in late if v['timeS']>=5)),
            middleWarningWindows=len(flagged),middleWarningFirstS=flagged[0]['timeS'] if flagged else None,
            targetEnergyAfter1s={str(int(hz)):float(sum(v['targets'][str(int(hz))]['rmsPa']**2 for v in late)) for hz in TARGETS},
            windows=windows))
    return out

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--key',type=int,choices=[45,48,60,64],required=True);a=p.parse_args()
    raw=(a.source/'distributed_felt_loss.json').read_bytes();d=json.loads(raw);s=d['summary']
    if any(s.get(k)!=v for k,v in dict(gate=True,cases=6,group=f'{a.key}-release_pedal',noOutputEQ=True,acousticFeedbackIncluded=False).items()):raise ValueError('source gate')
    result=[];refs={}
    for row in sorted(d['results'],key=lambda v:(v['hammerSpeedMps'],v['wireStiffnessLossScale'])):
        speed=row['hammerSpeedMps'];scale=row['wireStiffnessLossScale'];item=row['pressure'];path=a.source/item['file']
        if hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('pressure hash')
        rate,y=read(path)
        if rate!=48000 or y.dtype!=np.float32 or y.shape!=(1921440,2):raise ValueError('pressure format')
        out=analyze(y,rate,a.key,refs.get(speed))
        if scale==1.:refs[speed]=out
        ref=refs[speed]
        for c,b in zip(out,ref):
            c['middleEnergyRatioAfter1s']=c['middleEnergyAfter1s']/max(b['middleEnergyAfter1s'],1e-30)
            c['middleEnergyRatioAfter5s']=c['middleEnergyAfter5s']/max(b['middleEnergyAfter5s'],1e-30)
            c['targetEnergyRatioAfter1s']={k:v/max(b['targetEnergyAfter1s'][k],1e-30) for k,v in c['targetEnergyAfter1s'].items()}
        record=dict(key=a.key,speed=speed,lossScale=scale,channels=out)
        result.append(record)
        compact=[{**{k:v for k,v in c.items() if k!='windows'},
            'selectedWindows':[v for v in c['windows'] if v['timeS'] in (1,3,5,7,10,15,20)]} for c in out]
        print('G3_MIDDLE_TAIL_CASE '+json.dumps(dict(key=a.key,speed=speed,lossScale=scale,channels=compact),allow_nan=False),flush=True)
    summary=dict(gate=True,key=a.key,cases=len(result),diagnosticOnly=True,sourceManifestSha256=hashlib.sha256(raw).hexdigest(),
        mediumBandHz=[250,1500],warningFraction=.3,warningRelativeDb=-80,acousticFeedbackIncluded=False,
        above500HzDiagnosticOnly=True,calibratedParameters=False)
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'middle_tail.json').write_text(json.dumps(dict(summary=summary,results=result),indent=2,allow_nan=False))
    print('G3_MIDDLE_TAIL_GATE '+json.dumps(summary),flush=True)
if __name__=='__main__':main()
