"""Refine free plate/rim and independently verify structural assembly.
Identical material and joint parameters; no tuning to frequency response.
"""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from scipy.linalg import cholesky
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from bridge_strings import centerline
from spline_plate import assemble
from rim_structure import assemble as rim_assemble,response as rim_response
from structural_assembly import assemble as structure,mobility
from bridge_board_interface_diagnostic import compare as interface_compare
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())
def rel(x,y):
    e=float(np.linalg.norm(x-y)/max(np.linalg.norm(y),1e-30))
    return dict(relative=e,gate=e<=.05)
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--case',choices=['rim','structure'],required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    l=layout_build(sc,read('layout_hypothesis.json'));mat=read('board_interface_hypothesis.json');rc=read('rim_structure_hypothesis.json')
    c=contour_build(l,read('board_contour_hypothesis.json'),mat);rib=read('ribbed_plate_hypothesis.json')['rib']
    poly=np.array(c['contourXY_m']);centers={s:centerline(l['bridgeAttachmentNodes'][s]) for s in ('bass','treble')}
    pts=np.array([l['bridgeAttachmentNodes'][s][len(l['bridgeAttachmentNodes'][s])//2]['footProjectionXYZ_m'][:2] for s in ('bass','treble')]+[c['centroidXY_m']])
    freq=np.geomspace(30,150,24);rows=[];Y=[]
    if a.case=='rim':
        cases=[(12,8,14,True),(18,8,14,True),(24,8,14,True),(30,8,14,True),(30,8,18,True)]
    else:
        cases=[(12,2,12,True),(18,2,12,True),(24,2,12,True),(30,2,12,True),(30,4,12,True),(30,4,16,True),(30,4,16,False)]
    cache=None;old=None
    for cells,sub,order,connected in cases:
        if old!=cells:
            cache=assemble(poly,c['ribs'],mat['plate'],rib,cells,14,False);old=cells
        m=cache
        assert m['rank']==m['fullRank'] and abs(m['areaM2']-c['summary']['areaM2'])<1e-10
        if a.case=='rim':
            z=rim_assemble(m,rc,sub,order,connected);y,rec,pas=rim_response(m,z,pts,freq)
            cross=float(np.max(abs(y[:,-1,:-1])))
            K=z['K']+z['J']
        else:
            z=structure(m,centers,read('bridge_hypothesis.json'),mat,rc,sub,8,order,connected)
            y,rec,pas=mobility(z,freq);cross=float(np.max(abs(y[:,0,2])))
            K=z['K']+z['Jrim']+z['Jbridge']
        cholesky(z['M'])
        if connected:
            cholesky(K);assert cross>0
        else:assert cross<1e-14
        Y.append(y);rows.append(dict(cells=cells,sub=sub,order=order,connected=connected,dofs=len(z['M']),plateRank=m['rank'],condition=m['condition'],
           rimMassKg=z['rimMassKg'],bridgeMassKg=z.get('bridgeMassKg'),crossMobilityMaxMsN=cross,reciprocity=rec,passivityMinRelative=pas))
    if a.case=='rim':
        checks=[rel(x,y) for x,y in zip(Y,Y[1:])];gate=checks[-2]['gate'] and checks[-1]['gate']
    else:
        checks=[interface_compare(x,y) for x,y in zip(Y[:-2],Y[1:-1])]
        # Gate independently on finest plate pair, bridge mesh pair and joint quadrature pair.
        gate=all(x['gate'] for x in checks[-3:])
    summary=dict(case=a.case,cases=rows,convergence=checks,gate=gate,boardReady=False,rimReady=False)
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'structural_assembly.json').write_text(json.dumps(dict(summary=summary,scaleSha256=hashlib.sha256(raw).hexdigest(),frequenciesHz=freq.tolist(),scope='vertical low band diagnostic, no strings or radiation'),indent=2,allow_nan=False))
    print('G3_STRUCTURE_GATE '+json.dumps(summary),flush=True);assert gate,'structural mobility convergence'
if __name__=='__main__':main()
