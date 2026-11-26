"""G3.14d.3: analytic numerical decay of time integrators.
Scalar oscillators only; not measured piano sustain."""
import argparse,json,math,cmath
from pathlib import Path

def poles(lam,rate):
    if rate<=0:raise ValueError('rate')
    z=lam/rate
    main=(2+cmath.sqrt(1+2*z))/(3-2*z)
    parasitic=1/((3-2*z)*main)
    return main,parasitic

def metrics(f,rate,decay,method):
    if min(f,rate)<=0 or decay<0 or f>=rate/2:raise ValueError('domain')
    lam=complex(-decay,2*math.pi*f)
    if method=='bdf2':
        g,p=poles(lam,rate);secondary=abs(p)
    elif method=='midpoint':
        z=lam/(2*rate);g=(1+z)/(1-z);secondary=None
    else:raise ValueError('method')
    actual=-rate*math.log(abs(g));hz=rate*cmath.phase(g)/(2*math.pi)
    extra=actual-decay
    return dict(frequencyHz=f,rate=rate,method=method,physicalDecayPerS=decay,
        numericalDecayPerS=extra,amplitudeErrorDb30s=-20/math.log(10)*30*extra,
        frequencyErrorCents=1200*math.log2(hz/f),secondaryMagnitude=secondary,
        decayStable=abs(g)<=1+1e-12)

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    decay=math.log(1000)/30
    frequencies=(110.,130.8128,261.6256,329.6276,500.,1000.,2000.,4000.,8000.)
    rows=[metrics(f,rate,d,m) for f in frequencies for rate in (48000,96000,192000)
          for d in (0.,decay) for m in ('bdf2','midpoint')]
    if not all(r['decayStable'] for r in rows):raise ValueError('unstable pole')
    summary=dict(gate=True,diagnosticOnly=True,scalarOscillatorOnly=True,cases=len(rows),
        pianoSustainMeasured=False,selectedIntegrator=None,
        numericalDecayBudgetDb30s=1.,budgetDiagnosticOnly=True,
        bdf2ExceedsBudget=sum(r['method']=='bdf2' and abs(r['amplitudeErrorDb30s'])>1 for r in rows))
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'integrator_decay.json').write_text(json.dumps(dict(summary=summary,cases=rows),indent=2,allow_nan=False))
    for row in rows:
        if row['physicalDecayPerS']==0.:print('G3_INTEGRATOR_DECAY_CASE '+json.dumps(row,allow_nan=False),flush=True)
    print('G3_INTEGRATOR_DECAY_GATE '+json.dumps(summary,allow_nan=False),flush=True)
if __name__=='__main__':main()
