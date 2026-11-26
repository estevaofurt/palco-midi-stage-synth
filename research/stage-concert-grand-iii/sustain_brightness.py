"""G3.13l: combine reduced structural loss with intrinsic wire damping.
Screen both sustained fundamental and attack brightness, without changing
the output spectrum or treating pressure thresholds as audibility."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from scipy.io.wavfile import read
from wire_physical_midpoint import load
from structural_passive_fit import read_reference
from dry_pressure_render import RATE,pressure_source,common_gain,export_wav
from distributed_felt_loss import render_control,measures
from spectral_tail_audit import KEYS
from felt_law import params

SCALES=(1.,4.,8.,12.)
SPEEDS=(.3,3.)

def attack_bands(y,rate=RATE):
    """Windowed pressure RMS, no output processing; short-window bins
    describe broad brightness, not isolated partials."""
    out=[]
    for start,stop in ((0.,.05),(.05,.2)):
        x=np.asarray(y[round(start*rate):round(stop*rate)],float)
        if x.ndim!=2 or x.shape[1]!=2 or len(x)<8:raise ValueError('attack samples')
        w=np.hanning(len(x));p=abs(np.fft.rfft(x*w[:,None],axis=0))**2
        p[1:-1]*=2.;p/=len(x)*np.sum(w*w)
        f=np.fft.rfftfreq(len(x),1/rate);bands=[]
        for lo,hi in ((0.,500.),(500.,2000.),(2000.,8000.)):
            bands.append(np.sqrt(p[(f>=lo)&(f<hi)].sum(axis=0)))
        out.append(dict(startS=start,endS=stop,totalRmsPa=np.sqrt(p.sum(axis=0)).tolist(),
            bandRmsPa=np.stack(bands).tolist(),peakPa=np.max(abs(x),axis=0).tolist()))
    return out

def attack_compare(current,baseline):
    result=[];all_errors=[]
    for c,b in zip(current,baseline):
        full=np.asarray(b['totalRmsPa']);x=np.asarray(c['bandRmsPa']);r=np.asarray(b['bandRmsPa'])
        if np.any(full<=0):raise ValueError('empty attack reference')
        valid=r>=full[None,:]*1e-4
        delta=20*np.log10(np.maximum(x,1e-30)/np.maximum(r,1e-30))
        total=20*np.log10(np.maximum(c['totalRmsPa'],1e-30)/full)
        all_errors.extend(abs(delta[valid]).tolist())
        result.append(dict(startS=c['startS'],endS=c['endS'],totalDb=total.tolist(),
            bandDb=[[float(delta[i,j]) if valid[i,j] else None for j in range(2)] for i in range(3)],
            gate=bool(np.max(abs(total))<=1. and np.all(abs(delta[valid])<=3.))))
    return dict(windows=result,maximumSignificantBandChangeDb=max(all_errors,default=0.),gate=all(v['gate'] for v in result))

def fixed_thresholds(spectrum,reference):
    result=[]
    for c,r in zip(spectrum['channels'],reference['channels']):
        base=r['peakFundamentalRmsPa'];baseAll=r['peakSpectralRmsPa']
        if min(base,baseAll)<=0:raise ValueError('zero reference')
        def last(k,peak,db):
            hits=[v['timeS']+1 for v in c['windows'] if v[k]>=peak*10**(db/20)]
            return dict(lastWindowEndS=max(hits,default=0),rightCensored=bool(hits and max(hits)==len(c['windows'])))
        result.append(dict(channel=c['channel'],
            fundamental={str(db):last('fundamentalRmsPa',base,db) for db in (-20,-40,-60,-80)},
            total={str(db):last('spectralRmsPa',baseAll,db) for db in (-20,-40,-60,-80)}))
    return result

def nominal_source(root,key,sha,ph,rh):
    raw=(root/'distributed_felt_loss.json').read_bytes();d=json.loads(raw);s=d['summary']
    expected=dict(gate=True,group=f'{key}-release_pedal',cases=6,sourceFrozenSha256=sha,
        pressureManifestSha256=ph,referenceManifestSha256=rh,noOutputEQ=True,acousticFeedbackIncluded=False)
    if any(s.get(k)!=v for k,v in expected.items()):raise ValueError('nominal source identity')
    row=next(v for v in d['results'] if v['hammerSpeedMps']==3. and v['wireStiffnessLossScale']==1.
        and v['structureFactor']==1. and v['spreadCents']==0. and v['widthM']==0.)
    item=row['pressure'];path=root/item['file']
    if hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('nominal pressure hash')
    rate,y=read(path)
    if rate!=RATE or y.shape!=(1921440,2) or y.dtype!=np.float32:raise ValueError('nominal pressure format')
    return row['spectrum'],y,hashlib.sha256(raw).hexdigest()

def screen(row,baseline):
    cmp=row['comparison'];ref=baseline['comparison']
    sustain=all(v['fundamentalCommonT60S']>=max(0.,b['fundamentalCommonT60S']-max(1.,.10*b['fundamentalCommonT60S']))
        and .95<=v['fundamentalPeakRelative']<=1.05 for v,b in zip(cmp,ref))
    ratios=[v['lateUpperEnergyPa2S']/max(b['lateUpperEnergyPa2S'],1e-30) for v,b in zip(cmp,ref)]
    upper=all(x<=.75 for x in ratios) and all(v['upperDominanceWindowsCommon']<=b['upperDominanceWindowsCommon'] for v,b in zip(cmp,ref))
    return dict(fundamentalPreserved=bool(sustain),attackBrightnessPreserved=row['attackComparison']['gate'],
        upperEnergyRatio=ratios,upperReductionGate=bool(upper),
        candidateGate=bool(sustain and upper and row['attackComparison']['gate']))

def main():
    p=argparse.ArgumentParser()
    for k in ('scale','source','reference','pressure','nominal','out'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--key',type=int,choices=KEYS,required=True);a=p.parse_args()
    archive,wires,sha=load(a.source,a.scale);ref,rh=read_reference(a.reference,sha)
    z,coord,ph=pressure_source(a.pressure,sha,ref,archive,wires)
    nominal,nominalWav,nh=nominal_source(a.nominal,a.key,sha,ph,rh)
    root=Path(__file__).parent;spec=json.loads((root/'physical_sources.json').read_text());felt=json.loads((root/'felt_hypothesis.json').read_text())
    rows={x['key']:x for x in json.loads(a.scale.read_text())['rows']}
    pars=[params(k,rows[k]['count'],spec,felt) for k in KEYS];groups=[w.port for w in wires]
    masses=[h['massKg'] for h,_ in pars];felts=[pars[g][1] for g in groups]
    spread=1. if a.key==60 else 0.
    a.out.mkdir(parents=True,exist_ok=True);renders=[];baselines={}
    for speed in SPEEDS:
        for scale in SCALES:
            y,row=render_control(z,wires,rows,groups,masses,felts,a.key,'release_pedal',spread,.25,speed,0.,scale)
            row['attackBands']=attack_bands(y)
            if scale==1.:baselines[speed]=row
            b=baselines[speed]
            row['comparison']=measures(row,b)
            row['attackComparison']=attack_compare(row['attackBands'],b['attackBands'])
            row['nominalStrongReferenceThresholds']=fixed_thresholds(row['spectrum'],nominal)
            row['screening']=screen(row,b)
            renders.append((y,row))
            print('G3_SUSTAIN_BRIGHTNESS_CASE '+json.dumps({k:v for k,v in row.items() if k!='spectrum'},allow_nan=False),flush=True)
    # Explicitly include original strong reference in shared gain; no
    # per-file normalization, no post-filter. Do not compare gain across keys.
    gain=common_gain([nominalWav]+[y for y,_ in renders]);listen=a.out/'listen';physical=a.out/'physical'
    listen.mkdir(exist_ok=True);physical.mkdir(exist_ok=True)
    original=export_wav(listen/f'k{a.key}_nominal_strong_40s.wav',nominalWav,gain)
    for y,row in renders:
        name=f'k{a.key}_{"weak" if row["hammerSpeedMps"]==.3 else "strong"}_D25_loss{int(row["wireStiffnessLossScale"])}'
        row['files']=dict(audition40=export_wav(listen/(name+'_40s.wav'),y,gain),
            audition5=export_wav(listen/(name+'_5s.wav'),y[:5*RATE],gain),
            pressure=export_wav(physical/(name+'_pressure.wav'),y,gain,True))
    results=[row for _,row in renders]
    candidates=[]
    for scale in SCALES[1:]:
        matches=[v for v in results if v['wireStiffnessLossScale']==scale]
        candidates.append(dict(scale=scale,passedBothAttacks=all(v['screening']['candidateGate'] for v in matches),
            worstUpperRatio=max(max(v['screening']['upperEnergyRatio']) for v in matches),
            worstAttackBandChangeDb=max(v['attackComparison']['maximumSignificantBandChangeDb'] for v in matches)))
    summary=dict(gate=True,key=a.key,cases=len(results),diagnosticOnly=True,calibratedParameters=False,
        noOutputEQ=True,acousticFeedbackIncluded=False,above500HzDiagnosticOnly=True,commonGain=gain,
        selectedParameters=None,candidates=candidates,maximumEnergyBalance=max(max(v['startupBalance'],v['tailBalance']) for v in results),
        sourceFrozenSha256=sha,pressureManifestSha256=ph,referenceManifestSha256=rh,nominalManifestSha256=nh)
    (listen/'sustain_brightness.json').write_text(json.dumps(dict(summary=summary,original=original,results=results),indent=2,allow_nan=False))
    print('G3_SUSTAIN_BRIGHTNESS_GATE '+json.dumps(summary,allow_nan=False),flush=True)
if __name__=='__main__':main()
