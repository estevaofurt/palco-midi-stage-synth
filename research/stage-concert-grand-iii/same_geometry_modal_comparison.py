"""G3.10p: compare fixed 355, polynomial 385 and enriched 429 modes
using identical archived operators and geometry. No new FEM or quadrature."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from enriched_coupling_replay import require,read
from enriched_aperture_reference import enrich
from high_modal_allocation import require_archive
from acoustic_matrix_archive import read_npz,replay_full,modal_replay
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from recess_envelope import build as envelope
from dual_cavity_spatial_diagnostic import FREQ,compare_spatial
from fixed_355_validation import COUNTS,require_common
from split_radiation import relative

def maps(counts,idx):
    if list(counts)!=[61,63,63,63,63,61,55]:raise ValueError('unexpected enriched basis')
    offsets=np.r_[0,np.cumsum(counts)]
    expected=np.concatenate([np.arange(j,j+55) for j in offsets[:-1]])
    if not np.array_equal(idx,expected):raise ValueError('invalid polynomial coordinates')
    chosen=np.concatenate([np.arange(j,j+n) for j,n in zip(offsets[:-1],COUNTS)])
    if len(chosen)!=355 or not set(chosen)<=set(expected):raise ValueError('invalid fixed subset')
    return {385:(np.eye(374)[:,expected[:330]],np.eye(55)),
            355:(np.eye(374)[:,chosen[chosen<374]],np.eye(55)[:,:COUNTS[-1]])}

def main():
    p=argparse.ArgumentParser()
    for key in ('scale','archive','smooth','upper','coupled','common','out'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--angle',type=float,choices=[30.,55.],required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sha=hashlib.sha256(raw).hexdigest();sc=json.loads(raw)
    assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    require_common(json.loads(a.common.read_text()),sha)
    doc=json.loads((a.archive/'dual_cavity_high_modal.json').read_text());require_archive(doc,a.angle,sha)
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.asarray(q['contourXY_m']);g=geometry(poly,l,read('cabinet_geometry_hypothesis.json'));nf=len(FREQ);nm=len(g['microphonesXYZ_m'])
    def field(xy):
        x,y=(2*(xy-poly.min(0))/np.ptp(poly,axis=0)-1).T
        return np.stack([np.ones(len(x)),x,y,x*y],axis=1)
    _,old,_,geo=envelope(poly,g['rimTopZ_m'],g['rimBottomZ_m'],a.angle,55,field,55);assert geo['gate']
    panels,counts,idx,_=enrich(old);areas=np.array([v.basis.area for v in panels]);T=maps(counts,idx)
    sd=json.loads((a.smooth/'enriched_smooth.json').read_text());require(sd,a.angle,sha,dict(modes=429,counts=counts,width=.06,smoothQuadratureApproved=True))
    if sd['polynomialIndices']!=idx.tolist():raise ValueError('invalid smooth basis')
    sm=read_npz(a.smooth,sd['archive'],dict(R=(nf,429,429),Pe=(nf,2,429)),FREQ)
    ud=json.loads((a.upper/'enriched_upper.json').read_text());require(ud,a.angle,sha,dict(modes=374,counts=counts[:6],width=.06,algebraicStabilityGate=True))
    if ud['polynomialIndices']!=np.r_[np.arange(4),4+idx[:330]].tolist():raise ValueError('invalid upper basis')
    up=read_npz(a.upper,ud['archive'],dict(Zu=(nf,378,378),Pu=(nf,nm,378)),FREQ)
    sh=read_npz(a.archive,doc['shared'],dict(areas=(7,),Zl=(nf,59,59),Pl=(nf,2,59),Ze=(nf,385,385),Pe=(nf,2,385)),FREQ)
    if relative(areas,sh['areas'])>1e-10:raise ValueError('incompatible areas')
    cd=json.loads((a.coupled/'enriched_coupled.json').read_text())
    require(cd,a.angle,sha,dict(modes=429,approvedBlocks=28,modalConvergenceCertified=False,fullCabinetReady=False))
    if [v['frequencyHz'] for v in cd['reports']]!=FREQ or not all(v['coupled']['gate'] for v in cd['reports']):raise ValueError('incomplete coupling evidence')
    cm=read_npz(a.coupled,cd['archive'],dict(Ze=(nf,429,429),Y=(nf,4,4),flow=(nf,429,4)),FREQ)
    if not np.array_equal(cm['Ze'].real,sm['R']):raise ValueError('resistance mismatch')
    outputs={355:[],385:[],429:[]};reports=[]
    for i,f in enumerate(FREQ):
        x=tuple(v[i] for v in (up['Zu'],up['Pu'],sh['Zl'],sh['Pl'],cm['Ze'],sm['Pe']))
        y,rr=replay_full(*x,cm['Y'][i],cm['flow'][i],4)
        outputs[429].append(y);row=dict(frequencyHz=f,archiveReplay=rr)
        for n,(Tu,Tl) in T.items():
            v,r=modal_replay(x,Tu,Tl,4,counts,areas,y);outputs[n].append(v)
            row[str(n)]=r
        reports.append(row)
    pairs={'355vs385':(355,385),'385vs429':(385,429),'355vs429':(355,429)}
    comparisons={k:compare_spatial(FREQ,outputs[i],outputs[j],counts,areas) for k,(i,j) in pairs.items()}
    for k,v in cd['summary']['comparison'].items():
        if abs(v-comparisons['385vs429']['maximum'][k])>1e-8:raise ValueError('archived comparison changed')
    gate=all(v['gate'] for v in comparisons.values())
    summary=dict(gate=gate,angleDeg=a.angle,diagnosticOnly=True,referenceModes=429,fixedCounts=list(COUNTS),sameGeometry=True,
        sameOperators=True,modalConvergenceCertified=False,fullCabinetReady=False,radiationReady=False,
        maximum={k:v['maximum'] for k,v in comparisons.items()})
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'same_geometry_modal_comparison.json').write_text(json.dumps(dict(summary=summary,comparisons=comparisons,reports=reports,
        scaleSha256=sha,frequenciesHz=FREQ),indent=2,allow_nan=False))
    print('G3_SAME_GEOMETRY_MODAL_GATE '+json.dumps(summary),flush=True)
    if not gate:raise ValueError('fixed modal candidate not approved against enriched reference')
if __name__=='__main__':main()
