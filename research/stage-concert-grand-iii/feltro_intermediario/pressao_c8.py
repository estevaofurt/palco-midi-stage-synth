"""G3 C8 force, flow and observer pressure with matched impact controls."""
import argparse
from copy import deepcopy
import math
import json
from pathlib import Path

import numpy as np
from scipy.fft import irfft, next_fast_len, rfft

from ensaio import AcousticTarget, build_acoustic, RATE
from contato import KEYS
from action_launch import launch
from assembly_rank import SPREAD
from compact_mechanics import CompactWet
from felt_law import params
from physical_hammer_contact import Impact
from regional_compact import assemble_regional
from voicing_candidate import candidate, REF
from physical_inventory import hammer as hammer_prior
from wet_sparse import Cache


def intermediate(key, source):
    original = hammer_prior(key, source['hammer'])
    graded = hammer_prior(key, candidate(key, source)['hammer'])
    exponent = .5 * (original['power'] + graded['power'])
    log_force = .5 * sum(math.log(h['K_N_per_m_pow_p']) +
                         h['power'] * math.log(REF) for h in (original, graded))
    prior = deepcopy(source)
    prior['hammer'].update(exponentCoefficients=[exponent, 0., 0.],
                           log10KIntercept=(log_force - exponent*math.log(REF))/math.log(10),
                           log10KSlope=0., status='engineering_hypothesis',
                           source='G3 midpoint at reference compression')
    return prior, dict(exponent=exponent, reference_compression_m=REF,
                       reference_force_N=math.exp(log_force))


class TraceTarget(AcousticTarget):
    def __init__(self, engine, projection):
        super().__init__(engine, projection)
        self.flows = []
        self.cavity_state = engine.c.obj.c

    def step(self, force):
        result = self.engine.step(self.P @ force)
        self.cavity = result['Ei']
        self.continuity = max(self.continuity, result['continuity'])
        self.flows.append(result['u'].ravel())
        if len(self.flows) == round(.060 * RATE):
            self.snapshot = dict(board_q=self.engine.q[:80].copy(),
                                 board_v=self.engine.v[:80].copy(),
                                 cavity_q=self.cavity_state.x.copy(),
                                 cavity_v=self.cavity_state.v.copy())
        return (self.P.T @ result['v'], result['w'],
                result['dm'] + result['dc'] + result['we'])


def observe(flow, observer):
    length = next_fast_len(len(flow) + len(observer) - 1)
    bins = np.zeros((length//2+1, 2), complex)
    for start in range(0, flow.shape[1], 12):
        columns = slice(start,start+12)
        bins += np.einsum('fkp,fp->fk',
                          rfft(observer[:,:,columns], n=length, axis=0),
                          rfft(flow[:,columns], n=length, axis=0))
    return irfft(bins,n=length,axis=0)[:len(flow)+len(observer)-1]


def main():
    p = argparse.ArgumentParser()
    for name in ('work','priors','output'):
        p.add_argument(name,type=Path)
    p.add_argument("--midi",type=int,choices=(24,76),required=True)
    p.add_argument("--partials",type=int,choices=(64,128),default=64)
    p.add_argument("--key", type=int, choices=(107,108), required=True)
    args = p.parse_args()
    keys = tuple(sorted(set(KEYS) | {args.key}))
    root = args.work/'G3_consolidacao_20261127'
    geometry = json.loads((args.work/'sustain/scale_geometry.json').read_text())
    src, felt = (json.loads((args.priors/(name+'.json')).read_text())
                 for name in ('physical_sources','felt_hypothesis'))
    action = json.loads((args.priors/'action_hypothesis.json').read_text())
    speed = launch(args.key,args.midi,src,action)['impactSpeedMps']
    ranks = dict.fromkeys(keys,args.partials)
    with np.load(root/'G3_Base_Estrutural/integrated_80.npz') as base:
        m,k,d,P,wires = assemble_regional(base,geometry,[],ranks,
                                         {key:SPREAD.get(key,0.) for key in keys},
                                         dict.fromkeys(keys,0.))
    P = P[:,[i for i,(wire,*_) in enumerate(wires) if wire['key']==args.key]]
    steps = round(.100*RATE)
    cavity, exterior, z, scale = build_acoustic(args.work, horizon=steps)
    with np.load(args.work/'G3_Observadores_369/receiver369.npz') as data:
        observer = data['H']
    prior, voicing = intermediate(args.key, src)
    hammer, material = params(args.key,P.shape[1],prior,felt)
    target = TraceTarget(CompactWet(Cache(cavity),Cache(exterior),z,scale,m,k,d),P)
    model = Impact(target,np.zeros(P.shape[1],int),[hammer['massKg']],
                   [material]*P.shape[1],[speed])
    force, capture, balance = [], None, 0.
    for i in range(steps):
        f,*_ = model.step()
        force.append(f)
        balance = max(balance,abs(model.storage()+model.loss+model.feltloss+
                                  model.captureloss-model.initial)/model.initial)
        if capture is None and not model.active[0]:
            capture = i+1
    f = np.asarray(force)
    assert capture is not None and np.all(f[capture:]==0)
    assert balance < 1e-8 and target.continuity < 1e-10
    flow = np.asarray(target.flows)
    y = observe(flow, observer)
    for t in (600, steps//2, steps-1):
        j = np.arange(max(0,t-len(observer)+1),t+1)
        direct = np.einsum('tmp,tp->m',observer[t-j],flow[j])
        np.testing.assert_allclose(y[t], direct, rtol=1e-8,
                                   atol=1e-11*np.max(abs(y)))
    assert np.isfinite(y).all() and np.all(np.linalg.norm(y[:steps],axis=0)>0)
    metrics = dict(capture_step=capture, energy_residual=balance,
                   continuity=target.continuity, peak_N=float(f.sum(axis=1).max()),
                   impulse_Ns=float(f.sum()/RATE))
    args.output.mkdir()
    np.savez_compressed(args.output/'sinais.npz', pressure=y[:steps], force=f[:capture])
    result = dict(rate_hz=RATE, steps=steps, key=args.key, impact_speed_mps=speed,
                  midi=args.midi, partials=args.partials, voicing=voicing, **metrics)
    (args.output/'resultados.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(result, flush=True)


if __name__=='__main__':
    main()
