"""Reduced pre-contact action with explicit energy and timestamp convention.
MIDI requests target impact speed; it does not measure physical key motion.
"""
import math,json,argparse
from pathlib import Path
from physical_inventory import hammer
ROOT=Path(__file__).parent
def launch(key,midi,s,c):
    if type(key) is not int or not 21<=key<=108 or type(midi) is not int or not 0<=midi<=127:raise ValueError('MIDI domain')
    if midi==0:return None
    L=c['travelM'];gap=c['letOffM'];R=c['actionRatio'];g=c['gravityMps2'];a=c['impactSpeedMinMps'];b=c['impactSpeedMaxMps'];p=c['velocityExponent']
    if not (0<gap<L and R>0 and g>=0 and 0<a<b and p>0):raise ValueError('action domain')
    m=hammer(key,s['hammer'])['massKg']
    v=a+(b-a)*((midi-1)/126)**p
    u=math.sqrt(v*v+2*g*gap);D=L-gap
    # Driven stage: smooth monotone velocity v(t)=u*(3t^2-2t^3), t normalized.
    td=2*D/u;tf=2*gap/(u+v)
    work=.5*m*u*u+m*g*D;gravityFlight=m*g*gap;impact=.5*m*v*v
    err=abs(work-m*g*L-impact)
    assert err<=1e-12 and abs(u-g*tf-v)<=1e-12 and abs(u*tf-.5*g*tf*tf-gap)<=1e-12
    return dict(key=key,midiVelocity=midi,hammerMassKg=m,impactSpeedMps=v,letOffSpeedMps=u,drivenDurationS=td,freeFlightS=tf,
        fullTravelS=td+tf,drivenTravelM=D,letOffM=gap,keyTravelToEscapeM=D/R,peakKeySpeedMps=u/R,
        actionWorkJ=work,gravityFlightJ=gravityFlight,gravityTotalJ=m*g*L,impactEnergyJ=impact,balanceJ=err,
        drivenForcePeakN=m*(1.5*u/td+g),timestampConvention='first_contact',scheduledPreRoll=False)
def state_at(q,t,c):
    # Analytic fixture from rest to first contact. No drive after release.
    if not 0<=t<=q['fullTravelS']+1e-12:raise ValueError('time')
    td=q['drivenDurationS'];u=q['letOffSpeedMps'];m=q['hammerMassKg'];g=c['gravityMps2']
    if t<td:
        z=t/td;x=u*td*(z**3-.5*z**4);v=u*(3*z*z-2*z**3);F=m*(u/td*(6*z-6*z*z)+g);stage='driven'
    else:
        dt=min(t-td,q['freeFlightS']);x=q['drivenTravelM']+u*dt-.5*g*dt*dt;v=u-g*dt;F=0.;stage='free'
    return dict(travelM=x,speedMps=v,driveForceN=F,stage=stage)
def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    s=json.loads((ROOT/'physical_sources.json').read_text());c=json.loads((ROOT/'action_hypothesis.json').read_text());rows=[]
    for k in range(21,109):
        rs=[launch(k,v,s,c) for v in range(1,128)]
        assert all(x['impactEnergyJ']<y['impactEnergyJ'] for x,y in zip(rs,rs[1:]))
        for q in rs:
            end=state_at(q,q['fullTravelS'],c);release=state_at(q,q['drivenDurationS'],c)
            assert abs(end['travelM']-c['travelM'])<1e-12 and abs(end['speedMps']-q['impactSpeedMps'])<1e-12 and release['driveForceN']==0.
        rows.extend(rs)
    summary=dict(keys=88,launches=len(rows),maxBalanceJ=max(q['balanceJ'] for q in rows),gate=True,calibrated=False,actionReady=False)
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'action.json').write_text(json.dumps(dict(summary=summary,rows=rows,config=c),indent=2,allow_nan=False))
    print('G3_ACTION_GATE '+json.dumps(summary),flush=True)
    for q in rows:
        if q['key']==60 and q['midiVelocity'] in (24,76,127):print('G3_ACTION_ANCHOR '+json.dumps(q),flush=True)
if __name__=='__main__':main()
