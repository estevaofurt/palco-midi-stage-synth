"""G3.14d.23: joint weak/strong evidence; no parameter selection.
Read finished manifests only, with the same common pressure reference.
A last-window hit is right censored, not an audible duration."""
import argparse,json,math,hashlib,csv
from pathlib import Path

SPEEDS=(.3,3.)
FACTORS=(.75,.5,.25)
DBS=('-20','-40','-60','-80')
def require(x,message):
    if not x:raise ValueError(message)
def digest(path):
    raw=path.read_bytes()
    return json.loads(raw),hashlib.sha256(raw).hexdigest()
def identity(s,expected):
    require(all(s.get(k)==v for k,v in expected.items()),'manifest scope '+str(expected))
def finite(v):
    return isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v)
def endpoint(x):
    n=x['lastWindowEndS'];c=x['rightCensored']
    require(finite(n) and int(n)==n and 0<=n<=40 and isinstance(c,bool) and c==(n==40),'threshold endpoint')
    return int(n),c
def delta(wet,dry):
    w,wc=endpoint(wet);d,dc=endpoint(dry)
    return dict(wetSeconds=w,drySeconds=d,wetCensored=wc,dryCensored=dc,
        exactDifferenceS=None if wc or dc else w-d,
        lowerBoundS=None if dc else w-d,upperBoundS=None if wc else w-d)

def long_cases(doc,speed):
    s=doc['summary']
    identity(s,dict(gate=True,diagnosticOnly=True,sameBasis=True,seconds=40,rate=48000,speed=speed,cases=2,
        commonThresholdReference='first 5s strong dry',attackPreviouslyRejected=True,noOutputEQ=True,
        physicalFeedbackAccepted=False,audibleSustainMeasured=False))
    result={}
    for row in doc['cases']:
        wet=row['wet']
        require(isinstance(wet,bool) and wet not in result and row['speed']==speed and row['seconds']==40,'long case identity')
        require(0<=row['firstFiveSecondsReplayRelative']<=1e-6 and max(row['attackBalance'],row['tailBalance'])<=1e-8,'long case balance')
        channels={}
        for c in row['common']:
            j=c['channel'];require(j in (1,2) and j not in channels,'channel identity')
            channels[j]={k:c['fundamental'][k] for k in DBS}
            for v in channels[j].values():endpoint(v)
        require(set(channels)=={1,2},'channel coverage')
        result[wet]=channels
    require(set(result)=={True,False},'long case coverage')
    return [dict(speed=speed,channel=j,thresholdDb=int(db),**delta(result[True][j][db],result[False][j][db]))
        for j in (1,2) for db in DBS]

def candidate(row):
    f=row['bridgeFactor'];require(f in FACTORS,'bridge factor')
    require(row['wet'] is True and row['seconds']==5,'audition scope')
    ratios=row['fundamentalRatioToDry']
    require(len(ratios)==5 and all(len(r)==2 and all(finite(v) and v>=0 for v in r) for r in ratios),'ratio coverage')
    a=row['vsDryNominal']['attackScreeningGate'];late=min(ratios[-1])>=1.
    require(isinstance(a,bool) and row['attackScreeningGate'] is a and row['lateWindowAtLeastDry'] is late,'audition gate mismatch')
    require(max(row['attackBalance'],row['tailBalance'])<=1e-8,'audition balance')
    return dict(speed=row['speed'],bridgeFactor=f,attackGate=a,lateRatios=ratios[-1],lateGate=late,
        eligibleForLongTest=a and late)

def joint(auditions):
    require(set(auditions)==set(SPEEDS),'missing speed')
    allrows={}
    for speed,doc in auditions.items():
        s=doc['summary'];identity(s,dict(gate=True,diagnosticOnly=True,cases=3,speed=speed,seconds=5,rate=48000,
            bridgeFactors=list(FACTORS),otherDampingNominal=True,noOutputEQ=True,selectedParameters=None,
            physicalFeedbackAccepted=False,audibleSustainMeasured=False))
        rows={}
        for row in doc['cases']:
            c=candidate(row);f=c['bridgeFactor'];require(c['speed']==speed and f not in rows,'duplicate or mismatched case');rows[f]=c
        require(set(rows)==set(FACTORS),'missing factors')
        require(set(s['eligibleForLongTest'])=={f for f,c in rows.items() if c['eligibleForLongTest']},'summary gate mismatch')
        allrows[speed]=rows
    result=[]
    for f in FACTORS:
        cases=[allrows[v][f] for v in SPEEDS]
        result.append(dict(bridgeFactor=f,cases=cases,eligibleForLongTest=all(v['eligibleForLongTest'] for v in cases)))
    return result

def main():
    p=argparse.ArgumentParser()
    for name in ('long','audition','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();longs={};auditions={};hashes={};identityHash=None;gain=None
    for speed,tag in zip(SPEEDS,('0.3','3.0')):
        ld,h=digest(a.long/f'G3-physical-long-{tag}'/'long'/'physical_long_decay.json')
        ad,k=digest(a.audition/f'G3-bridge-audition-{tag}'/'bridge_audition.json')
        ls=ld['summary'];ss=ad['summary'];source=ls['sourceFrozenSha256']
        require(isinstance(source,str) and len(source)==64 and source==ss['sourceFrozenSha256'],'source mismatch')
        require(finite(ls['commonGain']) and ls['commonGain']>0 and ls['commonGain']==ss['commonGain'],'gain mismatch')
        if identityHash is None:identityHash=source;gain=ls['commonGain']
        require(identityHash==source and gain==ls['commonGain'],'cross-speed provenance')
        longs[speed]=ld;auditions[speed]=ad;hashes['long-'+tag]=h;hashes['audition-'+tag]=k
    comparisons=[row for v in SPEEDS for row in long_cases(longs[v],v)]
    candidates=joint(auditions)
    summary=dict(gate=True,diagnosticOnly=True,comparisons=len(comparisons),candidateCount=len(candidates),
        eligibleForLongTest=[r['bridgeFactor'] for r in candidates if r['eligibleForLongTest']],
        sourceFrozenSha256=identityHash,commonGain=gain,manifestSha256=hashes,
        selectedParameters=None,physicalFeedbackAccepted=False,audibleSustainMeasured=False,
        shortWindowScreeningOnly=True)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'joint_acoustic_evidence.json').write_text(json.dumps(dict(summary=summary,decay=comparisons,candidates=candidates),indent=2,allow_nan=False))
    with (a.out/'decay_comparison.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(comparisons[0]));w.writeheader();w.writerows(comparisons)
    for r in comparisons:
        if r['thresholdDb']==-60:print('G3_JOINT_DECAY '+json.dumps(r,allow_nan=False),flush=True)
    for r in candidates:print('G3_JOINT_BRIDGE '+json.dumps(r,allow_nan=False),flush=True)
    print('G3_JOINT_GATE '+json.dumps(summary,allow_nan=False),flush=True)
if __name__=='__main__':main()
