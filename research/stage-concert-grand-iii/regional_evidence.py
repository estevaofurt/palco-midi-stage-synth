"""G3.13w: regional evidence consolidation; no new acoustic parameters.
Only join complete manifests with identical provenance and actual tuning vectors."""
import argparse,csv,hashlib,json,math
from pathlib import Path

KEYS=(45,48,60,64)
SPEEDS=(.3,3.)
IDENTITY=('sourceFrozenSha256','pressureManifestSha256','referenceManifestSha256')
BRIDGE_PROFILES=('approved','other_half','central_two')

def definitions(key):
    s=1. if key==60 else 0.
    return dict(approved=(0.,0.,s,0.),other_half=(.5,.5,s,.5),other_one=(1.,1.,s,1.),
                other_two=(2.,2.,s,2.),central_one_half=(1.,1.,1.5,1.),central_two=(1.,1.,2.,1.))

def load(path,key,bridge=False):
    raw=path.read_bytes();d=json.loads(raw);s=d['summary']
    names=BRIDGE_PROFILES if bridge else tuple(definitions(key))
    expected=dict(gate=True,key=key,cases=len(names)*2,diagnosticOnly=True,selectedParameters=None,
                  nominalStructure=True,noOutputEQ=True,acousticFeedbackIncluded=False)
    if any(s.get(k)!=v for k,v in expected.items()):raise ValueError('manifest contract '+str(path))
    if any(not isinstance(s.get(k),str) or len(s[k])!=64 for k in IDENTITY):raise ValueError('provenance')
    limit='maximumPartitionError' if bridge else 'maximumBalance'
    if not 0<=s[limit]<=1e-8:raise ValueError('balance')
    rows={}
    for row in d['results']:
        token=(row['variant'],row['speed'])
        if token in rows or token[0] not in names or token[1] not in SPEEDS:raise ValueError('case identity')
        profile=row['profile'] if bridge else row['config']['unisonProfile']
        if tuple(profile)!=definitions(key)[token[0]]:raise ValueError('profile mismatch')
        rows[token]=row
    if set(rows)!={(n,v) for n in names for v in SPEEDS}:raise ValueError('missing cases')
    if bridge:
        if any(not 0<=rows['approved',v]['approvedAttackRelative']<=1e-6 for v in SPEEDS):raise ValueError('bridge replay')
    else:
        replays=s['approvedAttackReplays']
        if len(replays)!=2 or {v['speed'] for v in replays}!=set(SPEEDS):raise ValueError('replay coverage')
        if any(not 0<=v['relative']<=1e-6 or tuple(v['profile'])!=definitions(key)['approved'] for v in replays):raise ValueError('attack replay')
    return s,rows,hashlib.sha256(raw).hexdigest()

def crossing(windows,peak,db=-60):
    if not math.isfinite(peak) or peak<=0:raise ValueError('peak')
    if len(windows)!=40 or [w['timeS'] for w in windows]!=list(range(40)):raise ValueError('window coverage')
    hits=[]
    for w in windows:
        v=w['fundamentalRmsPa']
        if not math.isfinite(v) or v<0:raise ValueError('pressure')
        if v>=peak*10**(db/20):hits.append(w['timeS']+1)
    last=max(hits,default=0)
    return dict(seconds=last,censored=last==40)

def compare(candidate,baseline):
    # A last-window hit is a lower bound, not an observed end time.
    if baseline['censored']:return dict(deltaLowerBoundS=None,extensionProven=False,deltaExactS=None)
    delta=candidate['seconds']-baseline['seconds']
    return dict(deltaLowerBoundS=delta,extensionProven=delta>=2,
                deltaExactS=None if candidate['censored'] else delta)

def energy_summary(row,key):
    ids=row['components'];s=row['snapshots'][-1];e=s['energyFraction'];l=s['lossFraction'];w=s['netBridgeWorkFraction']
    if s['timeS']!=40 or ids[0]!='board' or len(set(ids))!=len(ids) or any(len(a)!=len(ids) for a in (e,l,w)):
        raise ValueError('energy snapshot')
    if not all(math.isfinite(x) for a in (e,l,w) for x in a) or abs(sum(e)+sum(l)-1)>1e-8 or abs(sum(w))>1e-8:raise ValueError('energy balance')
    group=[i for i,n in enumerate(ids) if n.startswith(f'k{key}-')]
    if not group:raise ValueError('missing excited group')
    return dict(boardRemainingFraction=e[0],boardLossFraction=l[0],boardNetWorkFraction=w[0],
        excitedGroupRemainingFraction=sum(e[i] for i in group),
        otherWireRemainingFraction=sum(e[i] for i in range(1,len(ids)) if i not in group))

def summarize(key,rows,bridge=None):
    out=[]
    for name,profile in definitions(key).items():
        cases=[]
        for speed in SPEEDS:
            row=rows[name,speed];base=rows['approved',speed];strong=rows['approved',3.]
            channels=[]
            cs=row['spectrum']['channels'];bs=base['spectrum']['channels'];ss=strong['spectrum']['channels']
            fixed=row['nominalStrongReferenceThresholds']
            if any([x['channel'] for x in a]!=[1,2] for a in (cs,bs,ss,fixed)):raise ValueError('channels')
            for c,b,s,f in zip(cs,bs,ss,fixed):
                match=crossing(c['windows'],b['peakFundamentalRmsPa'])
                control=crossing(b['windows'],b['peakFundamentalRmsPa'])
                common=crossing(c['windows'],s['peakFundamentalRmsPa'])
                old=f['fundamental']['-60']
                if not 0<=old['lastWindowEndS']<=40 or old['rightCensored']!=(old['lastWindowEndS']==40):raise ValueError('historic threshold')
                channels.append(dict(channel=c['channel'],matched=match,matchedBaseline=control,
                    **compare(match,control),approvedStrong=common,
                    historicalStrong=dict(seconds=old['lastWindowEndS'],censored=old['rightCensored'])))
            gate=row['screening']['candidateGate'] is True
            energy=None
            if bridge is not None and (name,speed) in bridge:
                energy=energy_summary(bridge[name,speed],key)
            cases.append(dict(speed=speed,gate=gate,channels=channels,energy=energy))
        valid=all(c['gate'] for c in cases)
        extension=all(ch['extensionProven'] for c in cases for ch in c['channels'])
        out.append(dict(key=key,variant=name,profile=list(profile),preservedBothAttacks=valid,
            extensionBothAttacks=extension,eligibleForAudition=name!='approved' and valid and extension,cases=cases))
    return out

def main():
    p=argparse.ArgumentParser();p.add_argument('--unison',type=Path,required=True);p.add_argument('--bridge',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    regions=[];manifests={};identity=None
    for key in KEYS:
        s,rows,h=load(a.unison/f'G3-nominal-unison-{key}'/'nominal_unison.json',key)
        manifests[f'unison-{key}']=h;current=tuple(s[k] for k in IDENTITY)
        if identity is None:identity=current
        if current!=identity:raise ValueError('unison identity mismatch')
        bridge=None
        if key in (48,60):
            b,bridge,h=load(a.bridge/f'G3-bridge-energy-{key}'/'bridge_energy.json',key,True)
            if tuple(b[k] for k in IDENTITY)!=identity:raise ValueError('bridge identity mismatch')
            replays={v['speed']:v['manifestSha256'] for v in s['approvedAttackReplays']}
            if any(v['approvedManifestSha256']!=replays[v['speed']] for v in bridge.values()):raise ValueError('attack provenance mismatch')
            manifests[f'bridge-{key}']=h
        regions.extend(summarize(key,rows,bridge))
    summary=dict(gate=True,diagnosticOnly=True,selectedParameters=None,audibleSustainMeasured=False,
        globalTuningValidated=False,unisonCases=48,bridgeCases=12,
        eligibleForAudition=[dict(key=r['key'],variant=r['variant'],profile=r['profile']) for r in regions if r['eligibleForAudition']],
        provenance=dict(zip(IDENTITY,identity)),manifestSha256=manifests)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'regional_evidence.json').write_text(json.dumps(dict(summary=summary,regions=regions),indent=2,allow_nan=False))
    with (a.out/'regional_evidence.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.writer(f);writer.writerow(['key','variant','profile','speed','channel','gate','eligibleForAudition','matchedSeconds','matchedCensored','baselineSeconds','baselineCensored','deltaLowerBoundS','approvedStrongSeconds','approvedStrongCensored','historicalStrongSeconds','historicalStrongCensored'])
        for r in regions:
            for c in r['cases']:
                for ch in c['channels']:
                    writer.writerow([r['key'],r['variant'],r['profile'],c['speed'],ch['channel'],c['gate'],r['eligibleForAudition'],ch['matched']['seconds'],ch['matched']['censored'],ch['matchedBaseline']['seconds'],ch['matchedBaseline']['censored'],ch['deltaLowerBoundS'],ch['approvedStrong']['seconds'],ch['approvedStrong']['censored'],ch['historicalStrong']['seconds'],ch['historicalStrong']['censored']])
    print('G3_REGIONAL_EVIDENCE_GATE '+json.dumps(summary,allow_nan=False),flush=True)
if __name__=='__main__':main()
