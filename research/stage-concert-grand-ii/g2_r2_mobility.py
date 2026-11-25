"""R2 preparation: forced harmonic mobility on the frozen coupled physical model."""
import argparse,json
from pathlib import Path
import numpy as np
from scipy.linalg import solve
from g2_damped_events import modal,ROOT
from g2_shared_board import KJ,CJ
from g2_acoustic_integrated import make_kernels,freqs,SR
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--key',type=int,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    model=json.loads((ROOT/'octave.json').read_text())
    keys=[x['key'] for x in model['groups']];j=keys.index(a.key);ng=len(keys)
    groups=[modal(x) for x in model['groups']]
    board=[x for x in model['boards'][0]['modes'] if x['f']<6000]
    w2=np.array([x['lambda'] for x in board]);D=2*(2+.0005*np.sqrt(w2));P=np.array([x['w'] for x in board])
    assert len(w2)==int(np.sum(freqs<6000))
    ks=[x[:len(w2)] for x in make_kernels(128,96)]
    rows=[]
    for mode in ('bypass','dry-held'):
        prepared=[]
        for i,(e,d,p) in enumerate(groups):
            # Same experimental R1 coefficient, applied only to inactive groups.
            dc=p[:,1:]@p[:,1:].T if mode=='dry-held' and i!=j else np.zeros_like(d)
            prepared.append((e,d+dc,p,d,dc))
        for harmonic in range(1,9):
            nominal=440*2**((a.key-69)/12)*harmonic
            if nominal*1.01>=6000:continue
            for ratio in (.99,1.,1.01):
                f=nominal*ratio;w=2*np.pi*f;z=KJ+1j*w*CJ
                bb=1/(w2-w*w+1j*w*D);hb=P.T@(bb[:,None]*P)
                local=[];free=np.zeros(ng,complex)
                for i,(e,d,p,_,_) in enumerate(prepared):
                    A=np.diag(e-w*w)+1j*w*d
                    external=p[:,1:].mean(axis=1) if i==j else np.zeros(len(e))
                    x=solve(A,np.column_stack((p[:,0],external)),assume_a='gen')
                    local.append((x,external));free[i]=p[:,0]@x[:,1]
                h=np.array([p[:,0]@x[:,0] for (_,_,p,_,_),(x,_) in zip(prepared,local)])
                jf=solve(np.eye(ng)+z*(hb+np.diag(h)),-z*free)
                qb=-bb*(P@jf);q=[x[:,1]+x[:,0]*jf[i] for i,(x,_) in enumerate(local)]
                xg=np.array([p[:,0]@v for (_,_,p,_,_),v in zip(prepared,q)]);xb=P.T@qb
                jointres=np.linalg.norm(jf+z*(xg-xb))/max(np.linalg.norm(jf),1e-30)
                inputPower=.5*float(np.real(np.vdot(1j*w*q[j],local[j][1])))
                boardLoss=.5*w*w*float(np.sum(D*abs(qb)**2))
                boardWork=.5*float(np.real(np.vdot(1j*w*xb,-jf)))
                stringLoss=.5*w*w*sum(float(np.real(np.vdot(v,d@v))) for (_,_,_,d,_),v in zip(prepared,q))
                damperLoss=.5*w*w*sum(float(np.real(np.vdot(v,d@v))) for (_,_,_,_,d),v in zip(prepared,q))
                jointLoss=.5*CJ*w*w*float(np.sum(abs(xg-xb)**2))
                total=boardLoss+stringLoss+damperLoss+jointLoss
                balance=abs(inputPower-total)/max(inputPower,1e-30)
                boardBalance=abs(boardWork-boardLoss)/max(boardLoss,1e-30)
                assert min(inputPower,boardLoss,stringLoss,damperLoss,jointLoss)>=-1e-12 and inputPower>0
                assert max(balance,boardBalance,jointres)<=1e-6
                pressure=[complex((k@np.exp(-1j*w*np.arange(k.shape[1])/SR))@(-w*w*qb)) for k in ks]
                row=dict(key=a.key,mode=mode,harmonic=harmonic,frequencyHz=f,ratio=ratio,inputMobilityAbs=float(abs(1j*w*np.vdot(local[j][1],q[j]))),inputPowerW=inputPower,
                    boardWorkW=boardWork,boardLossW=boardLoss,stringLossW=stringLoss,damperLossW=damperLoss,jointLossW=jointLoss,
                    bridgeVelocityAbsMps=float(abs(w*xg[j])),boardVelocityAbsMps=float(abs(w*xb[j])),
                    boardModalVelocityNorm=float(np.linalg.norm(w*qb)),pressurePaPerN=[abs(x) for x in pressure],
                    boardFraction=boardLoss/inputPower,balance=balance,boardBalance=boardBalance,jointResidual=float(jointres))
                rows.append(row)
    assert rows and all(np.isfinite(r['pressurePaPerN']).all() for r in rows)
    summary=[r for r in rows if r['ratio']==1.]
    for row in summary:print('G2_R2_MOBILITY '+json.dumps(row,allow_nan=False),flush=True)
    report=dict(key=a.key,rows=rows,gate=True,scope='linear forced harmonic response, 1N total shared across contacts, not hammer or note spectrum')
    (a.out/'mobility.json').write_text(json.dumps(report,indent=2,allow_nan=False))
    print('G2_R2_MOBILITY_GATE '+json.dumps(dict(key=a.key,cases=len(rows),maxBalance=max(r['balance'] for r in rows),maxBoardBalance=max(r['boardBalance'] for r in rows),maxJointResidual=max(r['jointResidual'] for r in rows),gate=True)),flush=True)
if __name__=='__main__':main()
