"""Bridge geometry inventory and mesh-convergence proof, no string/board coupling."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from continuous_bridge import build,response
from spatial_layout import build as layout_build
ROOT=Path(__file__).parent
def compare(a,b):
    scale=np.tile([1.,.02],a['static'].shape[0]//2)
    def err(x,y):
        x=x*scale[:,None]*scale[None,:];y=y*scale[:,None]*scale[None,:]
        return float(np.linalg.norm(x-y)/max(np.linalg.norm(y),1e-30))
    static=err(a['static'],b['static']);mob=err(a['Y'],b['Y'])
    return dict(staticRelative=static,mobilityRelative=mob,gate=static<=.01 and mob<=.05)
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--section',choices=['bass','treble'],required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    cfg=json.loads((ROOT/'bridge_hypothesis.json').read_text());layout=layout_build(sc,json.loads((ROOT/'layout_hypothesis.json').read_text()))
    nodes=layout['bridgeAttachmentNodes'][a.section];xyz=np.array([n['xyzM'] for n in nodes])
    edges=np.diff(xyz,axis=0);lengths=np.linalg.norm(edges,axis=1);unit=edges/lengths[:,None]
    angles=np.degrees(np.arccos(np.clip(np.sum(unit[:-1]*unit[1:],axis=1),-1,1)))
    # All attachment locations remain explicit. Report sharp turns instead of hiding them.
    indices=sorted(set([0,1,len(nodes)//2,len(nodes)//2+1,len(nodes)-1]))
    frequencies=np.geomspace(100.,4000.,48)
    m=cfg['material'];sec=cfg['section'][a.section];f=cfg['fixture'];rows=[];models=[]
    for sub in (1,2,4):
        b=build(xyz,sub,m['densityKgM3'],m['youngAlongPa'],sec['widthM'],sec['heightM'],f['foundationNperM2'])
        z=response(b,indices,frequencies,f['massDampingPerS'],f['stiffnessDampingS'])
        models.append(b);rows.append(z)
    coarse=compare(rows[0],rows[1]);fine=compare(rows[1],rows[2]);z=rows[2];Y=z['Y']
    report=dict(section=a.section,attachments=len(nodes),beamLengthM=float(sum(lengths)),beamMassKg=models[2]['massKg'],
        minEdgeM=float(min(lengths)),maxEdgeM=float(max(lengths)),maxTurnDeg=float(max(angles)),turnsOver45=int(sum(angles>45)),
        selectedPorts=[nodes[i] for i in indices],lowestHz=z['lowestHz'],coarse=coarse,fine=fine,
        maxReciprocity=max(q['reciprocity'] for q in rows),minPassivity=min(q['passivityMinRelative'] for q in rows),
        crossMobilityMaxMsN=float(max(abs(Y[:,0,2]))),gate=fine['gate'],bridgeReady=False)
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'bridge.json').write_text(json.dumps(dict(summary=report,config=cfg,attachmentNodes=nodes,
        scaleSha256=hashlib.sha256(raw).hexdigest(),frequenciesHz=frequencies.tolist(),mobilityReal=Y.real.tolist(),mobilityImag=Y.imag.tolist(),
        static=z['static'].tolist(),scope='vertical arclength beam, diagnostic ground foundation; no strings or soundboard attached'),indent=2,allow_nan=False))
    print('G3_BRIDGE_GATE '+json.dumps(report),flush=True);assert report['gate'],'beam mesh convergence'
if __name__=='__main__':main()
