"""Low-frequency full structure with selected complete unison groups.
A proof only: no actual hammer, no duplex or lateral motion, no calibrated structure.
"""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from bridge_strings import centerline
from spline_plate import assemble
from structural_assembly import assemble as structure
from string_structure import setup,response
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())
def compare(x,y):
    e=float(np.linalg.norm(x-y)/max(np.linalg.norm(y),1e-30))
    return dict(relative=e,gate=e<=.05)
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    l=layout_build(sc,read('layout_hypothesis.json'));mat=read('board_interface_hypothesis.json');rc=read('rim_structure_hypothesis.json')
    c=contour_build(l,read('board_contour_hypothesis.json'),mat);rib=read('ribbed_plate_hypothesis.json')['rib']
    poly=np.array(c['contourXY_m']);centers={s:centerline(l['bridgeAttachmentNodes'][s]) for s in ('bass','treble')}
    rr={r['key']:r for r in sc['rows']};keys=[45,48];assert keys[0] in centers['bass']['keys'] and keys[1] in centers['treble']['keys']
    freq=np.geomspace(30,150,24);rows=[];Y=[];old=None;m=None;z=None
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'string_structure.json'
    for cells,N,connected in [(24,64,True),(30,64,True),(30,128,True),(30,128,False)]:
        key=(cells,connected)
        if key!=old:
            if old is None or old[0]!=cells:m=assemble(poly,c['ribs'],mat['plate'],rib,cells,14,False)
            z=structure(m,centers,read('bridge_hypothesis.json'),mat,rc,2,8,14,connected);old=key
        P,wires,labels=setup(z,centers,rr,keys,2,N)
        y,s,d=response(z['M'],z['K']+z['Jrim']+z['Jbridge'],z['D'],P,wires,freq);Y.append(y)
        cross=float(np.max(abs(y[:,0,1])))
        record=dict(cells=cells,N=N,connected=connected,structureDofs=len(z['M']),wireCount=len(wires),wireIds=[w.id for w in wires],
          crossMobilityMaxMsN=cross,crossGate=bool(cross>0 if connected else cross<1e-14),metrics=s,perFrequency=d)
        rows.append(record);path.write_text(json.dumps(dict(cases=rows,complete=False),indent=2,allow_nan=False))
        print('G3_STRING_STRUCTURE_CASE '+json.dumps({k:v for k,v in record.items() if k!='perFrequency'}),flush=True)
    mesh=compare(Y[0],Y[1]);basis=compare(Y[1],Y[2])
    summary=dict(keys=keys,ports=labels,cases=len(rows),mesh=mesh,basis=basis,gate=mesh['gate'] and basis['gate'] and all(q['metrics']['gate'] and q['crossGate'] for q in rows),boardReady=False,integratedReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,scaleSha256=hashlib.sha256(raw).hexdigest(),frequenciesHz=freq.tolist(),mobilityReal=Y[2].real.tolist(),mobilityImag=Y[2].imag.tolist(),scope='vertical linear fixed-front unison groups, temporary joints and rim foundation'),indent=2,allow_nan=False))
    print('G3_STRING_STRUCTURE_GATE '+json.dumps(summary),flush=True);assert summary['gate'],'string structure convergence'
if __name__=='__main__':main()
