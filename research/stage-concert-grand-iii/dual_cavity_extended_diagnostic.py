"""Modal convergence of common exterior reference, conditional on the
previous integrated proof. The largest basis is assembled once per
quadrature, with nested subspaces projected without fitting.
"""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from scipy.linalg import block_diag
from spatial_layout import build as layout_build
from board_contour import build as contour_build,properties
from cabinet_geometry import geometry
from hybrid_cavity import build as upper_build,response as upper_response
from lower_prism import build as lower_build,response as lower_response
from recess_envelope import build as envelope
from acoustic_port_bridge import compatible
from port_coordinates import transform
from nested_acoustic_ports import reduced_panels,embedding,project,coupled_projection
from lid_exterior import load,pressure
from dual_cavity_reference_diagnostic import compare,maximum
from split_radiation import relative
from flow_modal_audit import audit_flow,pressure_defect
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())
def prerequisite(doc,angle,scale):
    s=doc.get('summary',{})
    if s.get('gate') is not True or s.get('angleDeg')!=angle or doc.get('scaleSha256')!=scale or s.get('commonFreeSpaceMonopolesOnly') is not True:
        raise ValueError('integrated reference prerequisite is not approved for this angle and scale')
    if s.get('upperApertureModes')!=36 or s.get('lowerMouthModes')!=10 or s.get('boardFields')!=4 or doc.get('frequenciesHz')!=[30.,80.,150.,200.,250.,300.]:
        raise ValueError('incompatible prior reference fixture')
    if s.get('radiationReady') is not False or s.get('fullCabinetReady') is not False:
        raise ValueError('incorrect scope of prior reference')
    for key in ('meshConvergence','quadratureConvergence'):
        metrics=s.get(key,{})
        for metric in ('impedance','upperPressure','lowerPressure','exteriorPressure','flow'):
            v=metrics.get(metric)
            if not isinstance(v,(int,float)) or isinstance(v,bool) or not np.isfinite(v) or not 0<=v<=.05:
                raise ValueError('invalid prior convergence: '+key+'/'+metric)
    cases=doc.get('cases',[])
    if len(cases)!=4 or not all(c.get('gate') is True for c in cases):
        raise ValueError('incomplete prior reference cases')
    if any([r.get('frequencyHz') for r in c.get('reports',[])]!=doc['frequenciesHz'] for c in cases):
        raise ValueError('incomplete prior frequency coverage')
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--previous',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--angle',type=float,required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sha=hashlib.sha256(raw).hexdigest();prerequisite(json.loads(a.previous.read_text()),a.angle,sha)
    sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.asarray(q['contourXY_m']);g=geometry(poly,l,read('cabinet_geometry_hypothesis.json'))
    h=-g['rimBottomZ_m'];_,center,_=properties(poly);mic=np.asarray(g['microphonesXYZ_m'])
    lp=np.array([np.r_[center,-h*.25],np.r_[center,-h*.75]])
    far=np.array([[poly[:,0].max()+2.,poly[:,1].mean(),1.5],[poly[:,0].mean(),poly[:,1].max()+2.,-.8]])
    def field(xy):
        x,y=(2*(xy-poly.min(0))/np.ptp(poly,axis=0)-1).T
        return np.stack([np.ones(len(x)),x,y,x*y],axis=1)
    u=upper_build(poly,40,14,g['rimTopZ_m'],a.angle,field,36);l=lower_build(poly,72,h,field,36)
    high=u['panels']+[l['mouth']];_,ext,_,geo=envelope(poly,g['rimTopZ_m'],g['rimBottomZ_m'],a.angle,36,field,36)
    assert len(high)==len(ext) and all(compatible(x,y) for x,y in zip(high,ext))
    E,br=transform(ext,high);assert max(br.values())<=1e-8
    freq=[30.,80.,150.,200.,250.,300.];inside=[]
    for f in freq:
        Zu,Pu,ru=upper_response(u,f,mic);Zl,Pl,rl=lower_response(l,2j*np.pi*f,lp)
        assert ru['gate'] and rl['gate'];inside.append((Zu,Pu,Zl,Pl))
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'dual_cavity_extended.json';rows=[];outputs=[];maps=[]
    counts=[x.basis.count for x in high];areas=[x.basis.area for x in high]
    def exterior(outer,inner,angular):
        ans=[]
        for f,(Z,r) in zip(freq,load(ext,freq,outer,inner,angular)):
            assert r['gate'];P=pressure(ext,np.eye(len(Z)),far,f,outer)
            ans.append((E.T@Z@E,P@E,r))
        return ans
    def run(n,m,extdata,outer,inner,angular):
        low=reduced_panels(high,[n]*(len(high)-1)+[m])
        Tu,ur=embedding(high[:-1],low[:-1]);Tl,lr=embedding(high[-1:],low[-1:])
        T=block_diag(Tu,Tl);maps.append(T)
        vals=[];reports=[]
        for f,(Zu,Pu,Zl,Pl),(Ze,Pe,er) in zip(freq,inside,extdata):
            Y,p1,p2,p3,F,r=coupled_projection(Zu,Pu,Zl,Pl,Ze,Pe,Tu,Tl,4)
            vals.append((Y,p1,p2,p3,F));reports.append(dict(frequencyHz=f,exterior=er,coupled=r,pressureDefect=pressure_defect(Zu,Zl,Ze,F,T,4)))
        row=dict(upperModesPerPanel=n,lowerModes=m,totalModes=Tu.shape[1]+Tl.shape[1],outer=outer,inner=inner,angular=angular,
            upperEmbedding=ur,lowerEmbedding=lr,reports=reports,gate=all(r['coupled']['gate'] for r in reports))
        rows.append(row);outputs.append(vals);path.write_text(json.dumps(dict(cases=rows,complete=False),indent=2,allow_nan=False))
        print('G3_DUAL_EXTENDED_CASE '+json.dumps({k:v for k,v in row.items() if k!='reports'}),flush=True)
    ex=exterior(24,42,36)
    for n,m in [(15,21),(21,21),(28,28),(36,36),(21,36),(36,21)]:run(n,m,ex,24,42,36)
    # Actual high-dimensional load is recomputed independently with finer
    # exterior quadrature, keeping every interior matrix fixed.
    ex=exterior(30,52,40);run(36,36,ex,30,52,40)
    modal=[maximum(compare(freq,outputs[i],outputs[i+1])) for i in range(3)]
    quad=maximum(compare(freq,outputs[3],outputs[6]))
    pairs=[(0,1),(1,2),(2,3),(4,3),(5,3),(3,6)]
    localization=[]
    for i,j in pairs:
        per=[]
        for f,x,y in zip(freq,outputs[i],outputs[j]):
            z=audit_flow(x[-1],y[-1],maps[i],counts,areas)
            per.append(dict(frequencyHz=f,**z))
        localization.append(dict(fromCase=i,toCase=j,frequencies=per,
            maximumPhysicalVelocityRelative=max(v['physicalVelocityRelative'] for v in per)))
    gate=all(r['gate'] for r in rows) and max(modal[-1].values())<=.05 and max(quad.values())<=.05
    gate=bool(gate and localization[2]['maximumPhysicalVelocityRelative']<=.05 and localization[-1]['maximumPhysicalVelocityRelative']<=.05
        and max(v['orthogonalClosure'] for x in localization for v in x['frequencies'])<=1e-8)
    summary=dict(gate=gate,angleDeg=a.angle,modalConvergence=modal,quadratureConvergence=quad,
        fixedInteriorMesh=True,upperN=40,upperNz=14,lowerN=72,projectedNestedModes=True,maximumModes=252,physicalFlowConvergence=localization[2]['maximumPhysicalVelocityRelative'],
        physicalFlowQuadrature=localization[-1]['maximumPhysicalVelocityRelative'],
        fullCabinetReady=False,radiationReady=False,commonFreeSpaceMonopolesOnly=True)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,flowLocalization=localization,frequenciesHz=freq,scaleSha256=sha),indent=2,allow_nan=False))
    print('G3_DUAL_EXTENDED_GATE '+json.dumps(summary),flush=True);assert gate
if __name__=='__main__':main()
