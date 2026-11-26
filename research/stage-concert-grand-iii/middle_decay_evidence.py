"""G3.14d.24: intermediate decay evidence from completed 40s manifests.
No new simulation or tuning. Windowed pressure power is not sound energy
or perceived loudness; never infer audible duration."""
import argparse,json,math,csv
from pathlib import Path
from joint_acoustic_evidence import digest,long_cases,require,endpoint,finite,SPEEDS,DBS

INTERVALS=((0,1),(1,3),(3,5),(5,10),(10,15),(15,20),(20,30),(30,40))
def windows(row,channel):
    c=next(v for v in row['spectrum']['channels'] if v['channel']==channel)
    w=c['windows']
    require(len(w)==40 and [v['timeS'] for v in w]==list(range(40)),'window coverage')
    a=[v['fundamentalRmsPa'] for v in w]
    require(all(finite(v) and v>=0 for v in a) and max(a)>0,'pressure values')
    require(abs(max(a)-c['peakFundamentalRmsPa'])<=1e-10*max(a),'peak mismatch')
    return a

def compare(dry,wet,peak):
    require(len(dry)==len(wet)==40 and finite(peak) and peak>0,'series shape')
    require(all(finite(v) and v>=0 for v in dry+wet),'pressure domain')
    rows=[]
    for lo,hi in INTERVALS:
        d=sum(x*x for x in dry[lo:hi]);w=sum(x*x for x in wet[lo:hi])
        rows.append(dict(startS=lo,endS=hi,dryPa2S=d,wetPa2S=w,wetToDryPowerRatio=w/d if d>0 else None,
            rmsDifferenceDb=10*math.log10(w/d) if min(w,d)>0 else None))
    occupancy=[]
    for db in DBS:
        limit=peak*10**(int(db)/20)
        def measure(a):
            hits=[i for i,x in enumerate(a) if x>=limit]
            gaps=sum(1 for i in range(hits[0],hits[-1]+1) if a[i]<limit) if hits else 0
            return dict(windowsAbove=len(hits),lastWindowEndS=max(hits,default=-1)+1,
                rightCensored=39 in hits,internalBelowWindows=gaps)
        occupancy.append(dict(thresholdDb=int(db),dry=measure(dry),wet=measure(wet)))
    return dict(intervals=rows,occupancy=occupancy)

def main():
    p=argparse.ArgumentParser();p.add_argument('--long',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    docs={};hashes={};source=None;gain=None
    for speed,tag in zip(SPEEDS,('0.3','3.0')):
        d,h=digest(a.long/f'G3-physical-long-{tag}'/'long'/'physical_long_decay.json')
        long_cases(d,speed);s=d['summary']
        if source is None:source=s['sourceFrozenSha256'];gain=s['commonGain']
        require(source==s['sourceFrozenSha256'] and gain==s['commonGain'] and gain>0,'provenance')
        docs[speed]={v['wet']:v for v in d['cases']};hashes[tag]=h
    result=[]
    for speed in SPEEDS:
        for ch in (1,2):
            dry=windows(docs[speed][False],ch);wet=windows(docs[speed][True],ch)
            peak=max(windows(docs[3.][False],ch)[:5]);row=compare(dry,wet,peak)
            for measure in row['occupancy']:
                for flag,label in ((False,'dry'),(True,'wet')):
                    original=next(v for v in docs[speed][flag]['common'] if v['channel']==ch)['fundamental'][str(measure['thresholdDb'])]
                    require(endpoint(measure[label])==endpoint(original),'threshold replay')
            row.update(speed=speed,channel=ch,referencePeakPa=peak)
            result.append(row)
            print('G3_MIDDLE_DECAY_CASE '+json.dumps(row,allow_nan=False),flush=True)
    summary=dict(gate=True,diagnosticOnly=True,cases=len(result),sourceFrozenSha256=source,manifestSha256=hashes,
        commonGain=gain,thresholdReplay=True,windowedPressurePowerNotAcousticEnergy=True,
        audibleSustainMeasured=False,selectedParameters=None,physicalFeedbackAccepted=False)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'middle_decay.json').write_text(json.dumps(dict(summary=summary,cases=result),indent=2,allow_nan=False))
    with (a.out/'middle_decay.csv').open('w',newline='',encoding='utf-8') as f:
        fields=['speed','channel',*result[0]['intervals'][0].keys()]
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for row in result:
            for i in row['intervals']:w.writerow(dict(speed=row['speed'],channel=row['channel'],**i))
    print('G3_MIDDLE_DECAY_GATE '+json.dumps(summary,allow_nan=False),flush=True)
if __name__=='__main__':main()
