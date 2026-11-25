"""Compare graded and uniform volumetric geometry without solving FEM."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from graded_volume_mesh import build,audit
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--angle',type=float,choices=[30.,55.],required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sha=hashlib.sha256(raw).hexdigest();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    doc=json.loads(a.source.read_text());s=doc['summary'];assert doc['scaleSha256']==sha and s['gate'] and s['angleDeg']==a.angle and s['surfaceOnly']
    candidates=[r for r in s['candidates'] if (r['boundaryN'],r['wedgeLayers'],r['edgeGrading'],r['layerGrading'])==(160,24,.5,.5)]
    assert len(candidates)==2 and all(r['minimumCapture']>=.95 for r in candidates)
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.asarray(q['contourXY_m']);g=geometry(poly,l,read('cabinet_geometry_hypothesis.json'));height=g['rimTopZ_m']
    a.out.mkdir(parents=True,exist_ok=True);rows=[]
    for n,b,k,eg,lg in ((40,160,24,0.,0.),(40,160,24,.5,.5)):
        m=build(poly,n,b,k,height,a.angle,eg,lg);r=audit(m,poly,b,k,height,a.angle,eg,lg)
        row=dict(interiorN=n,boundaryN=b,wedgeLayers=k,edgeGrading=eg,layerGrading=lg,**r);rows.append(row)
        print('G3_GRADED_VOLUME_CASE '+json.dumps(row),flush=True)
        (a.out/'graded_volume.json').write_text(json.dumps(dict(cases=rows,complete=False,scaleSha256=sha),indent=2,allow_nan=False))
    assert rows[0]['apertureFaces']==rows[1]['apertureFaces']==candidates[0]['traceFaces']
    summary=dict(gate=True,angleDeg=a.angle,diagnosticOnly=True,geometryOnly=True,volumeMeshGeometryValidated=True,
        matrixConditioningCertified=False,modalConvergenceCertified=False,fullCabinetReady=False,radiationReady=False)
    (a.out/'graded_volume.json').write_text(json.dumps(dict(summary=summary,cases=rows,scaleSha256=sha),indent=2,allow_nan=False))
    print('G3_GRADED_VOLUME_GATE '+json.dumps(summary),flush=True)
if __name__=='__main__':main()
