"""G3.11t: offline sample-addressed MIDI subset, hammer and damper together.
Synthetic instrument; no MIDI device, audio observer, or real-time claims."""
import argparse,json
from pathlib import Path
import numpy as np
from hammer_lifecycle import HammerBank
from variable_damper import PedalControl,VariableDamper
from coupled_hammer_contact import midpoint

class EventEngine:
    def __init__(self,voices,partials,rate,solver='schur'):
        if not 1<=voices<=68:raise ValueError('invalid synthetic note count')
        self.bank=HammerBank(voices,partials,rate,solver);a=self.bank.a
        self.ctrl=PedalControl(voices,rate);self.damper=VariableDamper(a,np.repeat(np.arange(voices),partials),160*a.ms)
        self.rate=rate;self.voices=voices;self.sample=0;self.dirty=True;self.refreshes=0
        self.busy=0;self.messages=0;self.damperloss=0.
    def validate(self,event):
        if len(event)!=4 or any(type(v)!=int for v in event):raise ValueError('invalid event')
        t,status,key,value=event
        if t<0 or not 0<=value<=127:raise ValueError('invalid event data')
        if status in (0x80,0x90):
            if not 60<=key<60+self.voices:raise ValueError('note outside synthetic bank')
        elif status!=0xB0 or key!=64:raise ValueError('unsupported message')
    def event(self,status,key,value):
        self.messages+=1
        if status==0xB0:self.ctrl.sustain(value/127.);return
        j=key-60
        if status==0x80 or value==0:self.ctrl.note(j,False);return
        self.ctrl.note(j,True)
        if self.bank.active[j]:
            # Explicit diagnostic policy, not a complete repetition mechanism.
            self.busy+=1;return
        self.bank.launch(j,.3+2.7*(value-1)/126.)
    def refresh(self):
        b=self.bank;a=b.a
        response=np.column_stack([midpoint(a,b.Fb,b.P[:,j],True)[1] for j in range(self.voices)])
        C=b.P.T@response;norm=max(np.linalg.norm(C),1e-30)
        if np.linalg.norm(C-C.T)>1e-10*norm or np.linalg.eigvalsh((C+C.T)/2).min()<-1e-10*norm:raise ValueError('invalid dynamic compliance')
        b.G=a.h*((C+C.T)/2+np.diag(a.h/(2*b.m)))
        if np.linalg.eigvalsh(b.G).min()<=0:raise ValueError('nonpositive dynamic compliance')
        b.cached_key=None;b.cached=None;self.dirty=False;self.refreshes+=1
    def step(self):
        b=self.bank;a=b.a
        levels=self.ctrl.advance()
        if self.damper.apply(levels):self.dirty=True
        if b.active.any() and self.dirty:self.refresh()
        old=a.v.copy()
        F,row=b.step()
        vm=(old+a.v)/2
        self.damperloss+=a.h*float(np.sum((a.ds-self.damper.intrinsic)*vm**2))
        self.sample+=1
        return F,row
    def process(self,end,events):
        # Absolute sample indices, half-open block interval, input order
        # preserved when several messages have the same sample.
        events=list(events)
        if type(end)!=int or end<self.sample:raise ValueError('invalid end sample')
        previous=self.sample
        for v in events:
            self.validate(v)
            if not previous<=v[0]<end:raise ValueError('unsorted or out-of-block event')
            previous=v[0]
        cursor=0;rows=[]
        while self.sample<end:
            while cursor<len(events) and events[cursor][0]==self.sample:
                self.event(*events[cursor][1:]);cursor+=1
            rows.append(self.step())
        return rows
    def balance(self):
        b=self.bank
        return b.storage()+b.loss+b.feltloss+b.captureloss-b.injected

def schedule(voices,rate):
    t=lambda x:round(x*rate)
    events=[]
    for j in range(voices):
        events.append((0,0x90,60+j,32+int(95*j/max(1,voices-1))))
    events.extend([(t(.0005),0x90,60,100),(t(.002),0xB0,64,127)])
    for j in range(voices):events.append((t(.004),0x90 if j%2 else 0x80,60+j,0))
    events.append((t(.014),0xB0,64,64))
    for j in range(voices):events.append((t(.018),0x90,60+j,100))
    for j in range(voices):events.append((t(.023),0x80,60+j,0))
    events.append((t(.032),0xB0,64,0))
    return sorted(events,key=lambda v:v[0])

def arrays(e):
    b=e.bank;a=b.a
    return (a.q,a.v,a.b.q,a.b.v,a.b.x,a.b.a,b.v,b.z)

def proof(voices,partials,rate):
    a=EventEngine(voices,partials,rate);b=EventEngine(voices,partials,rate,'dense')
    ev=schedule(voices,rate);index=0
    errors=np.zeros(8);scales=np.zeros(8);err=force=peak=contact=work=0.;max_active=0
    for i in range(round(.065*rate)):
        es=[]
        while index<len(ev) and ev[index][0]==i:es.append(ev[index]);index+=1
        F,r=a.process(i+1,es)[0];G,s=b.process(i+1,es)[0]
        peak=max(peak,float(np.max(F)));force=max(force,float(np.max(np.abs(F-G))))
        err=max(err,abs(a.balance()),abs(b.balance()))
        for j,(x,y) in enumerate(zip(arrays(a),arrays(b))):
            errors[j]=max(errors[j],np.linalg.norm(x-y));scales[j]=max(scales[j],np.linalg.norm(y))
        contact=max(contact,r['contactError'],s['contactError']);work=max(work,r['workError'],s['workError'])
        max_active=max(max_active,int(a.bank.active.sum()))
        if not np.array_equal(a.bank.active,b.bank.active):raise ValueError('capture timing mismatch')
    state=float(np.max(errors/np.maximum(scales,1e-30)))
    energy=err/max(a.bank.injected,1e-30);force/=max(peak,1e-30)
    launches=int(a.bank.launches.sum());captures=int(a.bank.captures.sum())
    gate=bool(launches==captures==2*voices and a.busy==b.busy==1 and a.messages==b.messages==len(ev)
        and not a.ctrl.held.any() and a.ctrl.pedal==0 and np.all(a.ctrl.level==1)
        and a.refreshes>1 and a.damperloss>0 and a.damperloss<=a.bank.loss+1e-14
        and np.isfinite([state,energy,force]).all() and energy<=1e-8 and max(state,force)<=1e-8 and contact<=1e-12 and work<=1e-10)
    return dict(voices=voices,partials=partials,sampleRate=rate,messages=a.messages,launches=launches,captures=captures,busyRejected=a.busy,
        maximumActiveHammers=max_active,complianceRefreshes=a.refreshes,damperLossJ=a.damperloss,
        energyRelative=energy,peakNormalizedStateRelative=state,forceRelative=force,contactResidualM=contact,workResidualJ=work,gate=gate)

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    rows=[proof(n,j,r) for n in (2,4,8) for j in (4,8) for r in (48000,96000)]
    gate=all(x['gate'] for x in rows)
    summary=dict(gate=gate,diagnosticOnly=True,syntheticParameters=True,sampleAddressedEvents=True,halfPedal=True,
        maximumEnergyError=max(x['energyRelative'] for x in rows),maximumStateError=max(x['peakNormalizedStateRelative'] for x in rows),
        maximumForceError=max(x['forceRelative'] for x in rows),totalMessages=sum(x['messages'] for x in rows),
        totalLaunches=sum(x['launches'] for x in rows),totalCaptures=sum(x['captures'] for x in rows),
        physicalFitAccepted=False,timeDomainReady=False,polyphonyValidated=False,radiationReady=False)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'event_coupling.json').write_text(json.dumps(dict(summary=summary,cases=rows),indent=2,allow_nan=False))
    print('G3_EVENT_COUPLING_GATE '+json.dumps(summary),flush=True)
    for x in rows:print('G3_EVENT_COUPLING_CASE '+json.dumps(x),flush=True)
    if not gate:raise ValueError('event coupling failed')
if __name__=='__main__':main()
