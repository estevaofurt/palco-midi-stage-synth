"""G3.01 inventory and dimensionally consistent published-model priors.
Never exports a playable scale. Unknown physical G3 parameters remain null.
"""
import json,math,argparse
from pathlib import Path
ROOT=Path(__file__).parent
def derive(a,E):
    L=a['L'];d=a['dMm']/1000;rho=a['rho'];T=a['T']
    if not all(math.isfinite(v) and v>0 for v in (L,d,rho,T,E,a['fPublished'])) or not 0<a['strikeM']<L:raise ValueError('anchor domain')
    area=math.pi*d*d/4;mu=rho*area;EI=E*math.pi*d**4/64
    B=math.pi**2*EI/(T*L**2);f=math.sqrt(T/mu)/(2*L)*math.sqrt(1+B)
    return dict(linearDensityKgM=mu,bendingNm2=EI,inharmonicity=B,impedanceNsM=math.sqrt(T*mu),equivalentVibratingMassKg=mu*L,nominalFixedEndHz=f,frequencyGapCents=1200*math.log2(f/a['fPublished']),strikeFraction=a['strikeM']/L)
def hammer(key,h):
    i=key-20;a,b,c=h['exponentCoefficients'];p=a+b*i+c*i*i
    m=h['massInterceptKg']+h['massSlopeKg']*i;K=10**(h['log10KIntercept']+h['log10KSlope']*i)
    if not (m>0 and p>1 and K>0):raise ValueError('hammer domain')
    return dict(massKg=m,power=p,K_N_per_m_pow_p=K,forceAt1mmN=K*.001**p,tangentAt1mmNm=p*K*.001**(p-1),source=h['source'],status=h['status'])
def build(s):
    anchors={a['key']:a for a in s['anchors']}
    if len(anchors)!=len(s['anchors']) or not set(anchors)<=set(range(21,109)):raise ValueError('anchors')
    rows=[]
    for k in range(21,109):
        prior=anchors.get(k)
        unknown={field:None for field in ('speakingLengthM','coreDiameterM','wrapDiameterM','wrapLengthM','linearDensityKgM','bendingNm2','tensionN','inharmonicity','impedanceNsM','stringCount','strikePositionM','damperPositionM','bridgePositionM','hammerMassKg','feltMemory','lossLaw')}
        row=dict(key=k,nominalHz=440*2**((k-69)/12),targetPhysical=unknown,targetStatus='unknown',hammerPrior=hammer(k,s['hammer']),stringPrior=None)
        if prior is not None:row['stringPrior']=dict(source=s['anchorSource'],status='published_equivalent_model',raw=prior,derived=derive(prior,s['material']['equivalentStringYoungPa']))
        rows.append(row)
    return dict(scope=s['scope'],rows=rows,summary=dict(keys=len(rows),hammerPriors=len(rows),stringAnchorPriors=len(anchors),identifiedTargetKeys=0,scaleReady=False),limitations=['equivalent wound material is not actual steel/copper density','fixed-end Euler-Bernoulli diagnostic does not exactly reproduce Timoshenko published frequencies','no string-count or bridge map inferred','no uncertainty or voicing measured on Yamaha','no motor parameters selected'])
def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    s=json.loads((ROOT/'physical_sources.json').read_text());report=build(s)
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'inventory.json').write_text(json.dumps(report,indent=2,allow_nan=False))
    print('G3_PHYSICAL_INVENTORY '+json.dumps(report['summary']))
if __name__=='__main__':main()
