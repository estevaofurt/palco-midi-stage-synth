"""G3.11n: synthetic damper and sustain control on reciprocal string model.
Damping changes only; no velocity reset, no gain envelope, no calibrated piano."""
import argparse,json
from pathlib import Path
import numpy as np
from scipy.linalg import cho_factor
from string_board_schur import StringBoard,fixture
from passive_midpoint import factor_psd
from split_radiation import relative

class PedalControl:
    def __init__(self,voices,rate,damper_mask=None,transition_ms=5.):
        if type(voices)!=int or voices<=0 or not np.isfinite([rate,transition_ms]).all() or min(rate,transition_ms)<=0:raise ValueError('invalid control')
        self.held=np.zeros(voices,dtype=bool)
        self.mask=np.ones(voices,dtype=bool) if damper_mask is None else np.asarray(damper_mask,dtype=bool).copy()
        if self.mask.shape!=(voices,):raise ValueError('invalid damper mask')
        self.pedal=0.;self.level=self.mask.astype(float)
        self.increment=min(1.,1000/(rate*transition_ms))
    def note(self,index,held):
        if type(index)!=int or not 0<=index<len(self.held) or type(held)!=bool:raise ValueError('invalid note event')
        self.held[index]=held
    def sustain(self,value):
        if not np.isfinite(value) or not 0<=value<=1:raise ValueError('invalid pedal position')
        self.pedal=float(value)
    def advance(self):
        target=np.where(self.mask & ~self.held,1-self.pedal,0.)
        self.level+=np.clip(target-self.level,-self.increment,self.increment)
        return self.level.copy()

class VariableDamper:
    def __init__(self,model,voice_of_partial,maximum_extra):
        self.model=model;self.intrinsic=model.ds.copy()
        self.mapping=np.asarray(voice_of_partial)
        self.extra=np.asarray(maximum_extra,dtype=float).copy()
        if self.mapping.shape!=model.ds.shape or self.mapping.dtype.kind not in 'iu' or np.any(self.mapping<0) or self.extra.shape!=model.ds.shape or not np.isfinite(self.extra).all() or np.any(self.extra<0):raise ValueError('invalid damper mapping')
        b=model.b;h=b.h
        self.H=b.R+2*b.M/h+h*b.K/2+np.einsum('jik,jlk->il',b.S,b.B)
        if model.solver=='dense':
            self.fixed=2*model.M0/h+model.D0+h*model.K0/2+model.Aug.T@self.H@model.Aug
    def apply(self,levels):
        levels=np.asarray(levels,dtype=float)
        if levels.ndim!=1 or len(levels)<=self.mapping.max() or not np.isfinite(levels).all() or np.any((levels<0)|(levels>1)):raise ValueError('invalid damper levels')
        a=self.model;b=a.b;h=a.h
        target=self.intrinsic+self.extra*levels[self.mapping]
        if np.array_equal(a.ds,target):return False
        a.ds[:]=target
        a.base=2*a.ms/h+a.ds+h*a.ks/2;a.hs=a.base+a.c
        if a.solver=='schur':
            eff=a.c*a.base/a.hs
            H=self.H+a.G.T@(eff[:,None]*a.G)
            a.U=b.A.T@factor_psd(H);a.V=a.U/b.diag[:,None]
            a.fac=cho_factor(np.eye(H.shape[0])+a.U.T@a.V)
        else:
            H=self.fixed.copy();i=np.arange(len(b.m),len(b.m)+len(a.ds))
            H[i,i]+=a.ds-self.intrinsic
            a.fac=cho_factor(H)
        return True
    def step(self,Fb,Fs,levels):
        self.apply(levels)
        old=self.model.v.copy()
        row=self.model.step(Fb,Fs)
        mid=(old+self.model.v)/2
        damper=self.model.h*float(np.sum((self.model.ds-self.intrinsic)*mid**2))
        # Damper loss is a subset of structural loss, not an additional loss.
        return row,damper

def probe(voices,partials,rate,seconds=.12):
    a=fixture(voices,partials,rate,'schur',32);b=fixture(voices,partials,rate,'dense',32)
    mapping=np.repeat(np.arange(voices),partials)
    # Synthetic positive damping, deliberately not tuned to piano decay.
    extra=160*a.ms
    ctrl=PedalControl(voices,rate,transition_ms=5.)
    x=VariableDamper(a,mapping,extra);y=VariableDamper(b,mapping,extra)
    events={0:[('on',0)],round(.01*rate):[('pedal',1.)],round(.02*rate):[('off',0)],
        round(.04*rate):[('pedal',.5)],round(.06*rate):[('pedal',0.)],round(.075*rate):[('on',0)],round(.09*rate):[('off',0)]}
    W=L=absolute=peak=err=state=ledger=jump=damper=0.;minimum=0.;rows=[]
    Fb=np.zeros(32);direction=np.cos(np.arange(voices*partials));direction/=np.linalg.norm(direction)
    for i in range(round(seconds*rate)):
        for kind,value in events.get(i,[]):
            if kind=='pedal':ctrl.sustain(value)
            else:ctrl.note(value,kind=='on')
        levels=ctrl.advance()
        if i in events:rows.append(dict(sample=i,events=events[i],firstDamperLevel=float(levels[0])))
        before=a.energy();x.apply(levels);y.apply(levels)
        jump=max(jump,abs(a.energy()-before))
        t=(i+.5)/rate
        force=direction*np.sin(2*np.pi*130*t)*np.sin(np.pi*t/.015)**2 if t<.015 else np.zeros_like(direction)
        w,dl=x.step(Fb,force,levels);v,dr=y.step(Fb,force,levels)
        W+=w[0];L+=w[1:].sum();absolute+=abs(w[0]);damper+=dl
        minimum=min(minimum,float(w[1:].min()),dl,w[1]-dl)
        E=a.energy();peak=max(peak,E);err=max(err,abs(W-L-E))
        ledger=max(ledger,relative(np.r_[w,dl],np.r_[v,dr]))
        state=max(state,*(relative(getattr(a,k),getattr(b,k)) for k in ('q','v')),
            *(relative(getattr(a.b,k),getattr(b.b,k)) for k in ('q','v','x','a')))
        if not np.isfinite([W,L,E,state,ledger,damper]).all():raise ValueError('nonfinite response')
    scale=max(absolute,peak,1e-30);budget=err/scale
    return dict(voices=voices,partials=partials,sampleRate=rate,energyRelative=budget,stateRelative=state,
        ledgerRelative=ledger,coefficientChangeEnergyRelative=jump/scale,minimumLoss=minimum,damperLoss=damper,events=rows,
        gate=bool(budget<=1e-9 and max(state,ledger)<=1e-8 and jump/scale<=1e-12 and minimum>=-1e-14 and damper>0))

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    rows=[probe(v,j,r) for v in (32,64) for j in (1,4) for r in (44100,48000,96000)]
    gate=all(v['gate'] for v in rows)
    summary=dict(gate=gate,diagnosticOnly=True,syntheticParameters=True,physicalFitAccepted=False,
        maximumEnergyError=max(v['energyRelative'] for v in rows),maximumStateError=max(v['stateRelative'] for v in rows),
        maximumLedgerError=max(v['ledgerRelative'] for v in rows),maximumCoefficientChangeEnergyError=max(v['coefficientChangeEnergyRelative'] for v in rows),
        halfPedalControlTested=True,damperCalibrationAccepted=False,timeDomainReady=False,polyphonyValidated=False,radiationReady=False)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'variable_damper.json').write_text(json.dumps(dict(summary=summary,cases=rows),indent=2,allow_nan=False))
    print('G3_VARIABLE_DAMPER_GATE '+json.dumps(summary),flush=True)
    if not gate:raise ValueError('variable damper diagnostic failed')
if __name__=='__main__':main()
