"""G3.01d: scale candidate 02 and explicit local geometry/termination inventory.
Analytical design only; not acoustic validation, global layout or fabrication.
"""
import argparse,copy,hashlib,json,math
from pathlib import Path
from scipy.optimize import brentq
from scale_hypothesis import build,area
ROOT=Path(__file__).parent
def db(x):return 20*math.log10(x)
def candidate(cfg,wound):
    base=build(cfg);old=base['rows'];w={r['key']:r for r in wound['rows']}
    assert wound['summary']['gate'] and set(w)==set(range(21,50))
    assert all(abs(w[r['key']]['oldTensionN']-r['tensionPerStringN'])<1e-8 for r in old[:29])
    # One predeclared engineering margin below the 3dB review threshold.
    # Average group impedance proxy, NOT end-point impedance or sound level.
    target=w[49]['newAverageGroupZ']*10**(2.5/20)
    def group_z(dmm):
        d=dmm/1000;L=old[29]['lengthM'];f=old[29]['nominalHz'];mu=cfg['steel']['density']*area(d)
        EI=cfg['steel']['young']*math.pi*d**4/64
        T=4*L*L*f*f*mu-math.pi**2*EI/L**2
        return 3*math.sqrt(T*mu)
    a=copy.deepcopy(cfg);d50=brentq(lambda d:group_z(d)-target,1.006,1.125,xtol=1e-12)
    a['solidDiameterMm'][0][1]=d50
    new=build(a)['rows'];out=[];wires=[]
    for row0 in new:
        row=copy.deepcopy(row0);k=row['key'];L=row['lengthM'];count=row['count'];mu=row['linearDensityKgM']
        if k in w:
            v=w[k];T=v['retunedTensionN'];row.update(tensionPerStringN=T,coreStressPa=v['coreStressPa'],
                impedancePerStringNsM=math.sqrt(T*mu),groupImpedanceNsM=v['newAverageGroupZ'],
                analyticalHz=v['modalFrequenciesHz'][0],residualCents=1200*math.log2(v['modalFrequenciesHz'][0]/row['nominalHz']),
                modalFrequenciesHz=v['modalFrequenciesHz'],massModel='piecewise_centered_winding',
                bendingInharmonicityParameter=math.pi**2*row['bendingNm2']/(T*L*L),
                terminationLocalZNsM=v['bareImpedanceNsM'],windingLocalZNsM=v['wrappedImpedanceNsM'],
                windingIntervalM=v['windingIntervalM'])
            # B alone is not a modal dispersion descriptor for nonuniform mass.
            row.pop('inharmonicity')
        else:
            B=row.pop('inharmonicity');row.update(bendingInharmonicityParameter=B,massModel='uniform_steel',
                modalFrequenciesHz=[row['nominalHz']*n*math.sqrt((1+B*n*n)/(1+B)) for n in range(1,9)],
                terminationLocalZNsM=row['impedancePerStringNsM'],windingLocalZNsM=None,windingIntervalM=None)
        assert cfg['screen']['minTensionN']<=row['tensionPerStringN']<=cfg['screen']['maxTensionN']
        assert row['coreStressPa']<=cfg['screen']['maxCoreStressPa'] and abs(row['residualCents'])<1e-4
        row['provenance']='derived engineering hypothesis 02; not Yamaha measured'
        out.append(row)
        for i in range(count):
            uid=f'k{k}-s{i+1}'
            # Local arclength measured from the front speaking termination.
            # No guessed world coordinates, damper locations or duplex dimensions.
            ports=[dict(id=uid+':'+role,role=role,localS_m=s,worldXYZ_m=None,axes=None)
                   for role,s in [('front',0.),('hammer',row['hammerPositionM']),('damper',None),('bridge',L)]]
            wires.append(dict(id=uid,key=k,unisonIndex=i+1,bridgeId=row['bridge'],lengthM=L,
                windingIntervalM=row['windingIntervalM'],ports=ports,frontNonSpeakingLengthM=None,rearNonSpeakingLengthM=None,
                breakAnglesRad=None,terminationCompliance=None,globalFrame=None,damperPresent=None,geometryStatus='local_only'))
    edges=[]
    for x,y in zip(out,out[1:]):
        k=x['key'];oldavg=db(old[k-20]['groupImpedanceNsM']/old[k-21]['groupImpedanceNsM'])
        avg=db(y['groupImpedanceNsM']/x['groupImpedanceNsM'])
        local=db(y['count']*y['terminationLocalZNsM']/(x['count']*x['terminationLocalZNsM']))
        edges.append(dict(keys=[k,k+1],oldAverageDeltaDb=oldavg,newAverageDeltaDb=avg,
            endpointProxyDeltaDb=local,topologyTransition=k in (29,46,49),
            averageReview=abs(avg)>3,endpointReview=abs(local)>3))
    assert len(out)==88 and len(wires)==226
    assert len({p['id'] for wire in wires for p in wire['ports']})==904
    assert abs(edges[28]['newAverageDeltaDb']-2.5)<1e-8
    assert all(not e['averageReview'] for e in edges)
    assert all(a['coreDiameterM']>=b['coreDiameterM']-1e-15 for a,b in zip(out[29:],out[30:]))
    # Keep every published solid anchor from C4 upwards untouched.
    assert out[39:][0]['coreDiameterM']==old[39]['coreDiameterM']
    for x,y in zip(out[39:],old[39:]):assert x['lengthM']==y['lengthM'] and x['coreDiameterM']==y['coreDiameterM'] and x['tensionPerStringN']==y['tensionPerStringN']
    summary=dict(keys=88,strings=226,ports=904,diameter50BeforeMm=cfg['solidDiameterMm'][0][1],diameter50AfterMm=d50,
        oldTotalTensionN=base['summary']['totalTensionN'],totalTensionN=sum(x['count']*x['tensionPerStringN'] for x in out),
        averageReviewEdges=sum(e['averageReview'] for e in edges),endpointReviewEdges=sum(e['endpointReview'] for e in edges),
        geometryReady=False,scaleReady=False,gate=True)
    return dict(version='G3-scale-hypothesis-02',summary=summary,rows=out,edges=edges,wires=wires,
        limitations=['average and bare endpoint travelling-wave impedance proxies are not frequency-dependent bridge mobility','wound mass and tension derived from centered 90% hypothesis','no global layout, damper geometry, duplex lengths, contact widths, tuning stretch or voicing','screen passes only local analytical scope'])
def main():
    p=argparse.ArgumentParser();p.add_argument('--wound',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    raw=(ROOT/'scale_hypothesis.json').read_bytes();w=json.loads(a.wound.read_text())
    assert w['sourceSha256']==hashlib.sha256(raw).hexdigest()
    report=candidate(json.loads(raw),w);a.out.mkdir(parents=True,exist_ok=True)
    report['sourceSha256']=hashlib.sha256(raw).hexdigest();report['woundReportSha256']=hashlib.sha256(a.wound.read_bytes()).hexdigest()
    (a.out/'scale_geometry.json').write_text(json.dumps(report,indent=2,allow_nan=False))
    print('G3_SCALE_GEOMETRY_GATE '+json.dumps(report['summary']),flush=True)
    for e in report['edges']:
        if e['topologyTransition'] or e['endpointReview']:print('G3_SCALE_GEOMETRY_EDGE '+json.dumps(e),flush=True)
if __name__=='__main__':main()
