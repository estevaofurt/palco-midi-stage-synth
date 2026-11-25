"""Hybrid cavity full aperture basis and independent exterior quadrature audit."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from hybrid_cavity import build,response,terminate
from closed_cavity import response as tetra
from lid_exterior import load,pressure
from split_radiation import split_load,relative
from two_sided_radiation import combine,fixture
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())
def compare(a,b,freq):
    return [dict(frequencyHz=f,**{k:relative(x,y) for k,x,y in zip(('impedance','pressure','netFlow','exteriorPressure'),v,w)})
        for f,v,w in zip(freq,a,b)]
def good(rows):return all(max(v[k] for k in ('impedance','pressure','netFlow','exteriorPressure'))<=.05 for v in rows)
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--angle',type=float,required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.asarray(q['contourXY_m']);g=geometry(poly,l,read('cabinet_geometry_hypothesis.json'))
    mic=np.asarray(g['microphonesXYZ_m']);lo=mic.copy();lo[:,2]=abs(g['rimBottomZ_m'])+.12
    far=np.array([[poly[:,0].max()+2.,poly[:,1].mean(),1.5],[poly[:,0].mean(),poly[:,1].max()+2.,1.5]])
    def field(xy,unused=None):
        x,y=(2*(xy-poly.min(0))/np.ptp(poly,axis=0)-1).T
        return np.stack([np.ones(len(x)),x,y,x*y],axis=1)
    freq=[30.,80.,150.,200.,250.,300.]
    I=np.eye(4);M=I;K=np.diag((2*np.pi*np.array([43.,69.,101.,137.]))**2);D=2*I
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'hybrid_full.json'
    rows=[];outputs=[];cross=[];cache={};ext={}
    for n,nz,outer,inner,ang,count in [(30,10,24,42,32,15),(30,10,24,42,32,21),
        (40,14,24,42,32,21),(40,14,30,52,40,15),(40,14,30,52,40,21)]:
        key=(n,nz)
        if key not in cache:
            m=build(poly,n,nz,g['rimTopZ_m'],a.angle,field,21)
            cache[key]=(m,[response(m,f,mic) for f in freq])
        m,interior=cache[key];panels=m['panels'];p0=m['prism']
        qkey=(outer,inner,ang)
        if qkey not in ext:
            ext[qkey]=(load(panels,freq,outer,inner,ang,p0['rho'],p0['c']),
                split_load(poly,field,freq,lo,outer,inner,ang))
        upper,lower=ext[qkey];ix=np.concatenate([np.arange(j*21,j*21+count) for j in range(len(panels))])
        sel=np.r_[np.arange(4),4+ix];vals=[];reports=[]
        for i,f in enumerate(freq):
            Z,P,r=interior[i];ze,er=upper[i];zd,pd,lr=lower[i]
            y,pr,u,tr=terminate(Z[np.ix_(sel,sel)],P[:,sel],ze[np.ix_(ix,ix)],4)
            full=np.zeros((len(ze),u.shape[1]),complex);full[ix]=u
            pe=pressure(panels,full,far,f,outer,p0['rho'],p0['c'])
            total,parts,cr=combine(y,zd,I,-I);V,fr=fixture(M,K,D,total,parts,f)
            vals.append((total,pr,full[::21],pe))
            reports.append(dict(frequencyHz=f,interior=r,termination=tr,exterior=er,lower=lr,combined=cr,fixture=fr))
            if n==30 and count==21 and f<=150:
                fullModel=dict(m['full'],B=np.column_stack([m['full']['B'],m['Cfull']]))
                zt,pt,rr=tetra(fullModel,2j*np.pi*f,mic)
                yt,pT,uT,rt=terminate(zt,pt,ze,4)
                tetTotal,_,ct=combine(yt,zd,I,-I)
                cross.append(dict(frequencyHz=f,impedance=relative(total,tetTotal),pressure=relative(pr,pT),
                    netFlow=relative(full[::21],uT[::21]),exteriorPressure=relative(pe,pressure(panels,uT,far,f,outer,p0['rho'],p0['c'])),
                    gate=rr['gate'] and rt['gate'] and ct['gate']))
        row=dict(n=n,nz=nz,outer=outer,inner=inner,angular=ang,modesPerPanel=count,
            gate=all(all(v[k]['gate'] for k in ('interior','termination','exterior','lower','combined','fixture')) for v in reports),reports=reports)
        rows.append(row);outputs.append(vals)
        path.write_text(json.dumps(dict(cases=rows,complete=False),indent=2,allow_nan=False))
        print('G3_HYBRID_FULL_CASE '+json.dumps({k:v for k,v in row.items() if k!='reports'}),flush=True)
    modalCoarse=compare(outputs[0],outputs[1],freq);mesh=compare(outputs[1],outputs[2],freq)
    quad=compare(outputs[2],outputs[4],freq);modal=compare(outputs[3],outputs[4],freq)
    gate=all(r['gate'] for r in rows) and all(good(v) for v in (mesh,quad,modal,cross)) and all(v['gate'] for v in cross)
    summary=dict(gate=gate,angleDeg=a.angle,modalCoarse=modalCoarse,modalConvergence=modal,meshConvergence=mesh,
        quadratureConvergence=quad,tetrahedralCrossCheck=cross,independentDomainsOnly=True,screenCorrectionIncluded=False,
        completeExteriorReady=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,frequenciesHz=freq,scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_HYBRID_FULL_GATE '+json.dumps(summary),flush=True);assert gate
if __name__=='__main__':main()
