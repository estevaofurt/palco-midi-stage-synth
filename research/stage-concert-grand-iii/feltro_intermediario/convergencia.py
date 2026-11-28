"""Compare physical intermediate-felt 64/128-partial runs, without changing the model.
Inputs: two directories containing 107-24,107-76,108-24,108-76 with
resultados.json and sinais.npz from the existing pressao_c8.py driver.
Reported contact metrics describe sampled positive force, not capture time.
"""
import argparse
import json
from pathlib import Path
import numpy as np

CASES=('107-24','107-76','108-24','108-76')
CUTS=((60,100),(60,90),(70,100))

def contact(force,rate,relative_threshold=0.):
    force=np.asarray(force,dtype=float)
    assert force.ndim==2 and force.shape[0]>0 and force.shape[1]>0
    assert np.isfinite(force).all() and np.all(force>=0)
    total=force.sum(axis=1)
    assert total.max()>0
    def measure(x):
        peak=float(x.max())
        active=np.flatnonzero(x>relative_threshold*peak)
        if not len(active):return None
        lo,hi=int(active[0]),int(active[-1])
        return dict(first_force_step=lo,last_force_step=hi,
                    active_steps=int(len(active)),span_steps=hi-lo+1,
                    onset_ms=1000*lo/rate,
                    span_ms=1000*(hi-lo+1)/rate,
                    active_ms=1000*len(active)/rate,
                    zero_steps_inside_span=hi-lo+1-len(active),
                    peak_N=peak)
    return dict(relative_threshold=relative_threshold,total=measure(total),
                per_wire=[measure(force[:,i]) for i in range(force.shape[1])])

def load(root,case,partials):
    folder=root/case
    m=json.loads((folder/'resultados.json').read_text())
    key,vel=map(int,case.split('-'))
    assert (m['key'],m['midi'],m['partials'],m['rate_hz'],m['steps'])==(key,vel,partials,384000,38400)
    assert 0<m['capture_step']<=m['steps']
    assert 0<=m['energy_residual']<1e-8 and 0<=m['continuity']<1e-10
    assert m['impact_speed_mps']>0
    with np.load(folder/'sinais.npz',allow_pickle=False) as data:
        f=data['force'];p=data['pressure']
    assert f.ndim==2 and len(f)==m['capture_step'] and p.shape==(m['steps'],2)
    assert np.isfinite(p).all() and np.all(np.linalg.norm(p,axis=0)>0)
    c=contact(f,m['rate_hz'])
    assert np.isclose(f.sum()/m['rate_hz'],m['impulse_Ns'],rtol=1e-12,atol=0)
    assert np.isclose(c['total']['peak_N'],m['peak_N'],rtol=1e-12,atol=0)
    return m,f,p,c

def compare(a,b,case):
    m,f,p,c=load(a,case,64); n,g,q,d=load(b,case,128)
    for k in ('key','midi','rate_hz','steps','impact_speed_mps','voicing'):
        assert m[k]==n[k],k
    assert f.shape[1]==g.shape[1]
    rate=m['rate_hz'];fp=np.zeros((m['steps'],f.shape[1]));gp=fp.copy()
    fp[:len(f)]=f;gp[:len(g)]=g
    denom=np.linalg.norm(gp)
    assert denom>0
    pres=np.linalg.norm(p-q,axis=0)/np.linalg.norm(q,axis=0)
    nfft=round(.040*rate);hz=np.fft.rfftfreq(nfft,1/rate);mask=(hz>=300)&(hz<650)
    windows={}
    for start,stop in CUTS:
        i,j=(round(t*rate/1000) for t in (start,stop))
        for taper,w in (('hann',np.hanning(j-i)),('rectangular',np.ones(j-i))):
            power=lambda x:(abs(np.fft.rfft(x[i:j]*w[:,None],n=nfft,axis=0)[mask])**2).sum(axis=0)
            x,y=power(p),power(q)
            assert np.all(x>0) and np.all(y>0)
            windows[f'{start}-{stop}_{taper}']=(10*np.log10(x/y)).tolist()
    return dict(case=case,rate_hz=rate,launch_to_capture_ms=[1000*m['capture_step']/rate,1000*n['capture_step']/rate],
                contact_64=c,contact_128=d,
                sensitivity_64=contact(f,rate,1e-6),sensitivity_128=contact(g,rate,1e-6),
                force_relative_l2=float(np.linalg.norm(fp-gp)/denom),
                impulse_relative=abs(m['impulse_Ns']/n['impulse_Ns']-1),
                peak_relative=abs(m['peak_N']/n['peak_N']-1),
                causal_pressure_relative=pres.tolist(),
                pressure_screen_1_percent=bool(np.max(pres)<=.01),
                band_64_over_128_dB=windows,
                energy_residual=[m['energy_residual'],n['energy_residual']],
                continuity=[m['continuity'],n['continuity']])

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run64',type=Path);parser.add_argument('run128',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    result={k:compare(args.run64,args.run128,k) for k in CASES}
    report=dict(status='diagnostic_only',cases=result,
                all_pressure_screens_pass=all(v['pressure_screen_1_percent'] for v in result.values()),
                physical_validation=False,
                scope='1% historical pressure screen only; no experimental force-time calibration or final G3.02 gate. Force span and active duration are discrete sample intervals; threshold sensitivity reported separately.')
    with args.output.open('x',encoding='utf-8') as f:json.dump(report,f,indent=2,allow_nan=False)
    print(json.dumps(report,indent=2,allow_nan=False))
if __name__=='__main__':
    main()
