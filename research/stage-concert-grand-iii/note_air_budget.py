"""G3.14a: per-note harmonic acoustic-feedback budget.
Reference ideal baffle only: no causal load, no tuning, no new WAV."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from scipy.linalg import solve
from wire_physical_midpoint import load
from structural_passive_fit import read_reference
from response_weighted_fit import read_group
from wire_baffle_reference import FREQ
from new_baffle_grid import DEVELOPMENT,RESERVED,EXTENSION
from unison_profiles import KEYS,profiles_for_key,detune_profile
from mode_selective_loss import mode_loss
from modal_string_radiation import response
from split_radiation import relative

def powers(md,A,wires,Z,f,j,Y):
    # Reconstruct the physical wire velocities under a unit harmonic force
    # on the specified hammer port. Convention: twice time-averaged power.
    w=2*np.pi*f
    G=md['K']-w*w*md['M']+1j*w*(md['D']+Z)
    rhs=md['P'][:,j].astype(complex);local=[]
    for a,b in zip(A,wires):
        z,g,_,iv,ip=b.condense(w)
        G+=z*np.outer(a,a)
        force=float(b.port==j);rhs+=g*a*force
        local.append((a,b,iv,ip,force))
    x=solve(G,rhs);v=1j*w*x
    board=float(np.vdot(v,md['D']@v).real)
    air=float(np.vdot(v,Z.real@v).real)
    losses=[]
    for a,b,iv,ip,F in local:
        q=np.r_[a@x,ip*F-iv*(a@x)]
        u=1j*w*q
        losses.append(float(np.vdot(u,b.D@u).real))
    total=float(Y[j,j].real)
    return power_budget(total,board,air,losses)

def power_budget(total,board,air,wires):
    vals=np.asarray([board,air,*wires],float)
    if not np.isfinite(total) or not np.isfinite(vals).all() or total<=0:raise ValueError('invalid input power')
    error=abs(total-vals.sum())/total
    if error>1e-6 or min(vals)<-1e-10*total:raise ValueError('note power balance')
    return dict(inputTwiceMeanW=total,structureFraction=board/total,airFraction=air/total,
        wireFractions=(vals[2:]/total).tolist(),powerRelative=error)

def one(md,A,wires,Z,H,f,j):
    Y,O,wet=response(md,A,wires,Z,H,f)
    Y0,O0,dry=response(md,A,wires,np.zeros_like(Z),H,f)
    if not wet['gate'] or not dry['gate']:raise ValueError('harmonic reference gate')
    b=powers(md,A,wires,Z,f,j,Y)
    b0=powers(md,A,wires,np.zeros_like(Z),f,j,Y0)
    return dict(frequencyHz=f,wet=b,dry=b0,wireIds=[w.id for w in wires],
        noteMobilityRelative=relative(Y[:,j],Y0[:,j]),notePressureRelative=relative(O[:,j],O0[:,j]),
        wetPressurePaPerN=np.abs(O[:,j]).tolist(),dryPressurePaPerN=np.abs(O0[:,j]).tolist(),
        maximumPowerError=max(b['powerRelative'],b0['powerRelative']))

def main():
    p=argparse.ArgumentParser()
    for name in ('scale','source','reference','grid','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();_,wires,sha=load(a.source,a.scale);z,rh=read_reference(a.reference,sha)
    data=[('original',FREQ,z)];hashes={}
    # Only use the primary, converged grid through 300 Hz. The extension
    # has separate convergence requirements and is not silently accepted.
    for role,freq in [('development',DEVELOPMENT),('reserved',RESERVED)]:
        d,h=read_group(a.grid,role,freq,sha,rh);data.append((role,freq,d));hashes[role]=h
    rows={x['key']:x for x in json.loads(a.scale.read_text())['rows']};B=z['fieldMap']
    results=[]
    for j,key in enumerate(KEYS):
        profile=profiles_for_key(key)[0][1]
        ww,_=detune_profile(wires,rows,profile);ww=mode_loss(ww,4.,2. if key==64 else 4.)
        md=dict(M=np.eye(80),K=np.diag(z['stiffness']),D=z['damping'],P=z['ports'])
        for role,freq,d in data:
            for f,Z,H in zip(freq,d['impedance'],d['pressure']):
                row=one(md,z['wirePorts'],ww,B.T@Z@B,H@B,float(f),j)
                row.update(key=key,role=role,nominalProfile=list(profile))
                results.append(row)
                print('G3_NOTE_AIR_CASE '+json.dumps(row,allow_nan=False),flush=True)
    summary=dict(gate=True,diagnosticOnly=True,selectedParameters=None,causalFeedbackAccepted=False,
        idealBaffleOnly=True,nominalStructure=True,noOutputEQ=True,notes=list(KEYS),frequencyPoints=22,
        cases=len(results),sourceFrozenSha256=sha,referenceManifestSha256=rh,gridManifestSha256=hashes,
        maximumPowerError=max(r['maximumPowerError'] for r in results),
        audibleSustainMeasured=False,frequencyRangeHz=[30.,300.])
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'note_air_budget.json').write_text(json.dumps(dict(summary=summary,results=results),indent=2,allow_nan=False))
    print('G3_NOTE_AIR_GATE '+json.dumps(summary,allow_nan=False),flush=True)
if __name__=='__main__':main()
