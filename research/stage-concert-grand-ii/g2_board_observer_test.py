"""Preparation only: compare observer to frozen control; prescribed synthetic source."""
import copy,json
from pathlib import Path
import numpy as np
from g2_acoustic_integrated import modes,freqs,make_kernels,render,rel,SR,C
from g2_treble_candidate_audio import energy
from g2_board_observer import BoardObserver
def main():
    m=[x for x in modes if x['f']<6000];o=BoardObserver(modes);n=len(m)
    assert n==int(np.sum(freqs<6000))
    a=np.zeros((n,2048));t=np.arange(a.shape[1])/SR
    for i in (0,n//3,2*n//3,n-1):a[i]=np.sin(2*np.pi*m[i]['f']*t)*np.sin(np.pi*np.arange(len(t))/(len(t)-1))**2
    original=[k[:n] for k in make_kernels(128,96)];new=o.make_kernels(128,96)
    kerr=max(float(np.linalg.norm(x-y)/max(np.linalg.norm(x),1e-30)) for x,y in zip(original,new))
    old=render(a,original);p=o.render(a,o.basis_sha)
    perr=rel(p,old);e=energy(a,8,16);ee=o.energy(a,o.basis_sha,8,16)
    err=abs(e-ee)/max(e,1e-30)
    assert max(kerr,perr,err)<=1e-9 and e>0 and np.all(p[:,:int(np.floor(SR/C+.5))]==0)
    # Equivalent modal coordinates with changed ordering/sign: pressure and energy invariant.
    alt=copy.deepcopy(m[::-1]);altacc=a[::-1].copy()
    for c in alt[0]['components']:c['coefficient']*=-1
    altacc[0]*=-1;other=BoardObserver(alt)
    assert other.basis_sha!=o.basis_sha
    p2=other.render(altacc,other.basis_sha);e2=other.energy(altacc,other.basis_sha,8,16)
    pe=rel(p2,p);en=abs(e2-ee)/max(ee,1e-30)
    assert max(pe,en)<=1e-9
    try:other.render(a,o.basis_sha)
    except ValueError:rejected=True
    else:raise AssertionError('cross-basis mismatch accepted')
    row=dict(modes=n,kernelError=kerr,pressureError=perr,energyError=err,coordinatePressureError=pe,coordinateEnergyError=en,mismatchRejected=rejected,gate=True,scope='synthetic prescribed source; no physical candidate or audio')
    Path('/tmp/observer-proof.json').write_text(json.dumps(row,indent=2,allow_nan=False))
    print('G2_R3_OBSERVER_PREP_GATE '+json.dumps(row,allow_nan=False),flush=True)
if __name__=='__main__':main()
