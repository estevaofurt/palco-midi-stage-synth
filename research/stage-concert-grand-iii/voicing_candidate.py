"""G3.02h: dimensional force-normalized voicing hypothesis, never automatic adoption."""
import argparse,copy,json,math,hashlib
from pathlib import Path
from physical_inventory import hammer
from felt_law import params,force
ROOT=Path(__file__).parent
REF=.0005
START=72
END=96
# Hall/Askenfelt prior used in G3.02e, not a Yamaha measurement.
K7=1e12
P7=3.
def candidate(key,s):
    if not 21<=key<=108:raise ValueError('key domain')
    if key<=START:return copy.deepcopy(s)
    h=hammer(START,s['hammer']);F0=h['K_N_per_m_pow_p']*REF**h['power'];F7=K7*REF**P7
    t=min(1.,(key-START)/(END-START))
    # Smooth slope at both ends of the interpolation region. Constant Fref and p
    # beyond C7 is an explicit engineering extension, not published C8 data.
    u=t*t*(3-2*t)
    p=h['power']+(P7-h['power'])*u
    F=math.exp(math.log(F0)+(math.log(F7)-math.log(F0))*u)
    K=F/REF**p
    out=copy.deepcopy(s);out['hammer'].update(exponentCoefficients=[p,0.,0.],log10KIntercept=math.log10(K),log10KSlope=0.,source='G3 force-normalized candidate; C5 CD2012 and C7 Hall/Askenfelt prior',status='engineering_hypothesis')
    return out
def inventory(s,c,scale):
    rows=[]
    for r in scale['rows']:
        k=r['key'];n=r['count'];prior=candidate(k,s);h0,f0=params(k,n,s,c);h1,f1=params(k,n,prior,c)
        assert h0['massKg']==h1['massKg']
        values=[]
        for d in (.0001,.00025,.0005,.001):
            values.append(dict(compressionM=d,originalN=n*force(d,0.,f0),candidateN=n*force(d,0.,f1)))
        rows.append(dict(key=k,massKg=h0['massKg'],pOriginal=f0.p,pCandidate=f1.p,force=values,status='unchanged CD2012' if k<=START else 'engineering extension of C7 prior' if k>END else 'interpolated engineering hypothesis'))
    assert [r['key'] for r in rows]==list(range(21,109))
    assert all(x['force']==[dict(compressionM=q['compressionM'],originalN=q['originalN'],candidateN=q['originalN']) for q in x['force']] for x in rows[:52])
    assert all(a['force'][2]['candidateN']<=b['force'][2]['candidateN']+1e-10 for a,b in zip(rows[51:],rows[52:]))
    return dict(summary=dict(keys=88,unchanged=52,modified=36,selected=False,gate=True),rows=rows,scope='instantaneous unrelaxed total contact force, not dynamic hardness or measured Yamaha')
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    s=json.loads((ROOT/'physical_sources.json').read_text());c=json.loads((ROOT/'felt_hypothesis.json').read_text());raw=a.scale.read_bytes();scale=json.loads(raw)
    assert scale['version']=='G3-scale-hypothesis-02' and scale['summary']['gate']
    report=inventory(s,c,scale);report['scaleSha256']=hashlib.sha256(raw).hexdigest();a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'voicing.json').write_text(json.dumps(report,indent=2,allow_nan=False))
    print('G3_VOICING_INVENTORY '+json.dumps(report['summary']),flush=True)
    for q in report['rows']:
        if q['key'] in (60,72,78,84,90,96,108):print('G3_VOICING_KEY '+json.dumps(q),flush=True)
if __name__=='__main__':main()
