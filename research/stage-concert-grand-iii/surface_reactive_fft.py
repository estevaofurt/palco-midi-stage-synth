"""G3.12c: cell-integrated reactive Rayleigh kernel accelerated by FFT.
Piecewise-constant surface averages are a new approximation; test grid
convergence without promoting a causal fit or a complete piano cabinet."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from scipy.fft import rfft2,irfft2
from numpy.polynomial.legendre import leggauss
from spline_plate import clip,assemble
from ribbed_plate import quadrature
from enriched_baffle import load_source
from acoustic_matrix_archive import read_npz
from dry_structural_modal import read
from spatial_layout import build as layout_build
from board_contour import build as contour_build,properties
from polygon_radiation import SurfaceModes
from split_radiation import relative
from dual_cavity_spatial_diagnostic import save_matrices

def cell_integrals(poly,field,n,order=4):
    """Integrate zero-extended field on rectangular cells. Full cells
    use tensor Gauss, cut cells use polygon quadrature; no center mask."""
    lo=poly.min(0);dx,dy=np.ptp(poly,axis=0)/n
    ix,iy=np.meshgrid(np.arange(n),np.arange(n),indexing='ij')
    origins=lo+np.column_stack((ix.ravel()*dx,iy.ravel()*dy))
    corners=origins[:,None,:]+np.array([[0,0],[dx,0],[dx,dy],[0,dy]])
    a=poly;e=np.roll(a,-1,axis=0)-a;_,center,_=properties(poly)
    normal=np.column_stack((-e[:,1],e[:,0]));normal*=np.sign(np.sum((center-a)*normal,axis=1))[:,None]
    signed=np.einsum('cvi,ei->cve',corners,normal)-np.sum(a*normal,axis=1)
    inside=np.all(signed>=-1e-13,axis=(1,2));outside=np.any(np.all(signed<-1e-13,axis=1),axis=1)
    z,w=leggauss(order);t=(z+1)/2;w=w/2
    u,v=np.meshgrid(t,t,indexing='ij');offset=np.column_stack((u.ravel()*dx,v.ravel()*dy))
    wt=(w[:,None]*w[None,:]).ravel()*dx*dy
    nf=field(center[None,:]).shape[1];B=np.zeros((n*n,nf));area=0.
    ids=np.flatnonzero(inside)
    for i in range(0,len(ids),512):
        j=ids[i:i+512];x=origins[j,None,:]+offset[None,:,:]
        S=field(x.reshape(-1,2)).reshape(len(j),len(wt),nf)
        B[j]=np.einsum('q,cqf->cf',wt,S);area+=len(j)*dx*dy
    for j in np.flatnonzero(~inside & ~outside):
        x,y=origins[j];q=poly.copy()
        for axis,bound,sign in ((0,x,1),(0,x+dx,-1),(1,y,1),(1,y+dy,-1)):
            q=clip(q,axis,bound,sign)
            if len(q)<3:break
        if len(q)<3:continue
        ar,_,_=properties(q)
        if ar<1e-14:continue
        xy,w=quadrature(q,order);B[j]=w@field(xy);area+=float(w.sum())
    return B.reshape(n,n,nf),dx,dy,area

def average_kernel(n,dx,dy,k,order):
    """Average cos(k*r)/r over two equal rectangular cells.
    Difference distribution is triangular in each coordinate. For
    singular quadrants, Duffy triangles cancel radial Jacobian exactly."""
    z,w=leggauss(order);t=(z+1)/2;w=w/2
    u,v=np.meshgrid(t,t,indexing='ij');u=u.ravel();v=v.ravel()
    wt=(w[:,None]*w[None,:]).ravel()
    i,j=np.meshgrid(np.arange(n),np.arange(n),indexing='ij')
    i=i.ravel();j=j.ravel();K=np.zeros(n*n)
    for sx in (-1,1):
        for sy in (-1,1):
            singular=(i<=1)&(j<=1)&((i==0)|(sx==-1))&((j==0)|(sy==-1))
            ids=np.flatnonzero(~singular)
            for start in range(0,len(ids),2048):
                a=ids[start:start+2048]
                X=dx*(i[a,None]+sx*u);Y=dy*(j[a,None]+sy*v)
                R=np.hypot(X,Y)
                K[a]+=np.sum(np.cos(k*R)/R*(wt*(1-u)*(1-v))[None,:],axis=1)
            for a in np.flatnonzero(singular):
                # distance from the zero corner in each unit quadrant:
                # q_x,q_y in [0,1]. Split square at diagonal.
                value=0.
                for x,y in ((u,u*v),(u*v,u)):
                    L=np.hypot(dx*(x/u),dy*(y/u))
                    tx=x if i[a]==0 else 1-x
                    ty=y if j[a]==0 else 1-y
                    value+=float(np.sum(wt*(1-tx)*(1-ty)*np.cos(k*u*L)/L))
                K[a]+=value
    return K.reshape(n,n)

def reactive(B,dx,dy,f,order,rho=1.204,c=343.):
    n=B.shape[0];m=B.shape[2]
    if B.shape!=(n,n,m) or min(dx,dy,f,rho,c)<=0:raise ValueError('invalid cells')
    K=average_kernel(n,dx,dy,2*np.pi*f/c,order)
    # Zero padding separates periodic images. Embedding uses signed
    # offsets, and the unused +/-n row and column are zero.
    idx=np.minimum(np.arange(2*n),2*n-np.arange(2*n))
    valid=idx<n;J=np.minimum(idx,n-1);pad=K[np.ix_(J,J)]*(valid[:,None]&valid[None,:])
    H=rfft2(pad);flat=B.reshape(-1,m);X=np.empty((m,m))
    for i in range(0,m,8):
        conv=irfft2(rfft2(B[:,:,i:i+8],s=(2*n,2*n),axes=(0,1))*H[:,:,None],s=(2*n,2*n),axes=(0,1))[:n,:n]
        X[:,i:i+8]=flat.T@conv.reshape(n*n,-1)
    return rho*f*X

def wet_response(k,D,P,A,Z,H,f):
    om=2*np.pi*f;V=1j*om*np.linalg.solve(np.diag(k-om*om)+1j*om*(D+A.T@Z@A),P)
    Y=P.T@V;O=H@A@V;power=(Y+Y.conj().T)/2
    loss=V.conj().T@(D+A.T@Z.real@A)@V
    return Y,O,dict(powerRelative=relative(power,loss),reciprocity=relative(Y,Y.T),
        passivityMinRelative=float(np.linalg.eigvalsh(power).min()/max(np.linalg.norm(power),1e-30)))

def main():
    p=argparse.ArgumentParser()
    for k in ('scale','source','baffle','out'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();z,sha=load_source(a.source,a.scale)
    raw=(a.baffle/'enriched_baffle.json').read_bytes();b=json.loads(raw);s=b['summary'];freq=[30.,150.,300.]
    if b['sourceFrozenSha256']!=sha or b['frequenciesHz']!=freq or any(s.get(k)!=v for k,v in dict(gate=True,fields=72,oneSidedIdealBaffle=True,resistanceOnly=True,reactanceIncluded=False,radiationReady=False).items()):raise ValueError('incompatible resistance source')
    old=read_npz(a.baffle,b['archive'],dict(resistance=(3,72,72),pressure=(3,2,72),mobility=(3,4,4),observation=(3,2,4)),freq)
    sc=json.loads(a.scale.read_bytes());l=layout_build(sc,read('layout_hypothesis.json'));mat=read('board_interface_hypothesis.json')
    q=contour_build(l,read('board_contour_hypothesis.json'),mat);rib=read('ribbed_plate_hypothesis.json')['rib']
    poly=np.asarray(q['contourXY_m']);plate=assemble(poly,q['ribs'],mat['plate'],rib,30,14,False)
    W=z['fieldVectors'];ev=z['fieldEigenvalues'];A=z['fieldMap']
    field=SurfaceModes(plate,z['physicalLift'][:plate['rank']]@W/np.sqrt(ev)[None,:])
    grids=(60,120,240);results=[];areas=[];audits=[]
    for n in grids:
        B,dx,dy,area=cell_integrals(poly,field,n)
        ae=abs(area-plate['areaM2'])/plate['areaM2'];areas.append(ae)
        if ae>1e-9:raise ValueError('cell area mismatch')
        row=[]
        for f in freq:
            X=reactive(B,dx,dy,f,8)
            asym=relative(X,X.T)
            if asym>1e-10:raise ValueError('reactive reciprocity failure')
            row.append(X)
            print('G3_REACTIVE_GRID '+json.dumps(dict(grid=n,frequencyHz=f,reciprocity=asym,areaRelative=ae)),flush=True)
        results.append(np.stack(row))
        if n==grids[-1]:
            X12=reactive(B,dx,dy,150.,12);kernelError=relative(X12,row[1])
    rows=[];ZZ=[];YY=[];OO=[]
    for i,f in enumerate(freq):
        coarse=relative(results[0][i],results[1][i]);fine=relative(results[1][i],results[2][i])
        X=(results[2][i]+results[2][i].T)/2;Z=old['resistance'][i]+1j*X
        Y,O,audit=wet_response(z['stiffness'],z['damping'],z['ports'],A,Z,old['pressure'][i],f)
        gate=bool(fine<=.005 and fine<coarse and kernelError<=1e-6 and max(audit['powerRelative'],audit['reciprocity'])<=1e-8 and audit['passivityMinRelative']>=-1e-8)
        row=dict(frequencyHz=f,coarseRelative=coarse,fineRelative=fine,wetAudit=audit,
            mobilityChangeRelative=relative(Y,old['mobility'][i]),gate=gate)
        rows.append(row);ZZ.append(Z);YY.append(Y);OO.append(O)
        print('G3_REACTIVE_CASE '+json.dumps(row),flush=True)
    a.out.mkdir(parents=True,exist_ok=True)
    entry=save_matrices(a.out,'surface_reactive_fft',frequencies=freq,impedance=np.stack(ZZ),pressure=old['pressure'],
        mobility=np.stack(YY),observation=np.stack(OO))
    summary=dict(gate=all(v['gate'] for v in rows),diagnosticOnly=True,physicalHypothesis=True,fields=72,
        oneSidedIdealBaffle=True,reactanceIncluded=True,cellAverageApproximation=True,gridSizes=list(grids),
        maximumFineError=max(v['fineRelative'] for v in rows),kernelOrderRelative=kernelError,maximumAreaError=max(areas),
        calibratedParameters=False,acousticFitAccepted=False,timeDomainReady=False,radiationReady=False,polyphonyValidated=False)
    (a.out/'surface_reactive_fft.json').write_text(json.dumps(dict(summary=summary,cases=rows,archive=entry,sourceFrozenSha256=sha,
        resistanceManifestSha256=hashlib.sha256(raw).hexdigest(),frequenciesHz=freq),indent=2,allow_nan=False))
    print('G3_REACTIVE_GATE '+json.dumps(summary),flush=True)
    if not summary['gate']:raise ValueError('reactive grid convergence not accepted')
if __name__=='__main__':main()
