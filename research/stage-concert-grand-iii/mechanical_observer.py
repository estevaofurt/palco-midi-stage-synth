"""G3.11u: offline synthetic mechanical observer, not microphone pressure.
Raw velocity observations with a fixed projection, common gain and
anti-alias conversion. No physical acoustic calibration or production audio."""
import argparse,json
from pathlib import Path
import numpy as np
from scipy.signal import resample_poly
from scipy.io import wavfile
from event_coupling import EventEngine

# Two fixed linear observation rows on the four generalized board fields.
# Arbitrary diagnostic directions, not stereo microphone positions.
OBS=np.array([[.8,.4,-.2,.1],[.8,-.4,.2,.1]],dtype=float)

class ObservedEngine(EventEngine):
    def step(self):
        a=self.bank.a.b
        before=a.v.copy()
        F,row=super().step()
        velocity=OBS@(a.A@((before+a.v)*.5))
        return F,row,velocity

def render(voices,partials,rate,events,seconds,block,solver='schur'):
    a=ObservedEngine(voices,partials,rate,solver)
    N=round(rate*seconds);events=list(events)
    if type(block)!=int or block<=0 or any(not 0<=v[0]<N for v in events):raise ValueError('invalid render range')
    data=np.empty((N,2));error=0.;cursor=0
    for start in range(0,N,block):
        end=min(N,start+block);stop=cursor
        while stop<len(events) and events[stop][0]<end:stop+=1
        rows=a.process(end,events[cursor:stop]);cursor=stop
        data[start:end]=[v[2] for v in rows]
        error=max(error,abs(a.balance()))
    if cursor!=len(events) or not np.isfinite(data).all():raise ValueError('invalid observation')
    return data,dict(voices=voices,partials=partials,sourceRate=rate,samples=N,
        energyRelative=error/max(a.bank.injected,1e-30),injectedJ=a.bank.injected,
        launches=int(a.bank.launches.sum()),captures=int(a.bank.captures.sum()),
        peak=float(np.max(np.abs(data))),rms=float(np.sqrt(np.mean(data**2))))

def convert(data,rate):
    if rate not in (48000,96000,192000) or data.ndim!=2 or data.shape[1]!=2 or not np.isfinite(data).all():raise ValueError('invalid conversion')
    factor=rate//48000
    return np.ascontiguousarray(data if factor==1 else resample_poly(data,1,factor,axis=0,window=('kaiser',8.6),padtype='constant'))

def alias_probe():
    t=np.arange(96000)/96000
    a=convert(np.column_stack((np.sin(2*np.pi*1000*t),np.sin(2*np.pi*35000*t))),96000)[1000:-1000]
    rms=np.sqrt(np.mean(a*a,axis=0))
    pass_error=abs(float(rms[0])*np.sqrt(2)-1)
    stop=float(rms[1])*np.sqrt(2)
    return dict(passbandAmplitudeError=pass_error,stopbandAmplitude=stop,gate=bool(pass_error<=.002 and stop<=.001))

def note_events(voices,rate,velocity,pedal):
    t=lambda x:round(x*rate)
    ev=[(0,0xB0,64,127 if pedal else 0)]
    for i in range(voices):ev.append((t(i*.001),0x90,60+i,velocity))
    for i in range(voices):ev.append((t(.045+i*.001),0x80,60+i,0))
    if pedal:ev.append((t(.14),0xB0,64,0))
    return sorted(ev,key=lambda x:x[0])

def proof():
    rate=48000;ev=note_events(2,rate,90,True)
    a,x=render(2,4,rate,ev,.18,64)
    b,y=render(2,4,rate,ev,.18,127)
    d,z=render(2,4,rate,ev,.18,64,'dense')
    error=float(np.linalg.norm(a-d)/max(np.linalg.norm(d),1e-30))
    partition=bool(np.array_equal(a,b));silent,_=render(2,4,rate,[],.01,32)
    # Ensure observing is side-effect free by comparing energy/injection
    # across block partition and independent dense response.
    energy=max(x['energyRelative'],y['energyRelative'],z['energyRelative'])
    gate=bool(partition and np.count_nonzero(silent)==0 and error<=1e-8 and energy<=1e-8 and x['peak']>0 and x['launches']==x['captures']==2)
    return dict(gate=gate,partitionBitwise=partition,silentExact=bool(np.count_nonzero(silent)==0),
        denseObservationRelative=error,maximumEnergyError=energy)

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    check=proof();alias=alias_probe();a.out.mkdir(parents=True,exist_ok=True)
    rows=[];audio=[]
    for v in (32,80,127):
        for sustain in (False,True):
            ev=note_events(2,96000,v,sustain)
            raw,row=render(2,4,96000,ev,.22,64)
            y=convert(raw,96000);name=f'proxy_v{v}_pedal{int(sustain)}'
            row.update(name=name,velocity=v,sustain=sustain,outputRate=48000,outputSamples=len(y))
            np.save(a.out/(name+'.npy'),raw,allow_pickle=False)
            rows.append(row);audio.append(y)
    # One common scalar across all six observations, no per-note leveling.
    maximum=max(float(np.max(np.abs(y))) for y in audio)
    gain=.8/max(maximum,1e-30)
    for row,y in zip(rows,audio):
        pcm=np.rint(y*gain*32767).astype(np.int16)
        wavfile.write(a.out/(row['name']+'.wav'),48000,pcm)
        row['pcmPeak']=int(np.max(np.abs(pcm.astype(np.int32))))
    gate=bool(check['gate'] and alias['gate'] and all(v['energyRelative']<=1e-8 and v['launches']==v['captures']==2 and v['peak']>0 for v in rows))
    summary=dict(gate=gate,diagnosticOnly=True,syntheticParameters=True,mechanicalVelocityProxy=True,microphonePressure=False,
        commonGain=gain,physicalFitAccepted=False,timeDomainReady=False,radiationReady=False,polyphonyValidated=False,
        outputRate=48000,wavFiles=len(rows),maximumEnergyError=max(v['energyRelative'] for v in rows))
    (a.out/'mechanical_observer.json').write_text(json.dumps(dict(summary=summary,proof=check,alias=alias,rows=rows),indent=2,allow_nan=False))
    print('G3_OBSERVER_GATE '+json.dumps(summary),flush=True)
    print('G3_OBSERVER_PROOF '+json.dumps(dict(proof=check,alias=alias)),flush=True)
    for row in rows:print('G3_OBSERVER_CASE '+json.dumps(row),flush=True)
    if not gate:raise ValueError('observer diagnostic failed')
if __name__=='__main__':main()
