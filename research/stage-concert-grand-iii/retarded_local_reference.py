"""Use one locally rebuilt structural basis for all acoustic operators.
Compare independent archives only at shared physical force/pressure ports."""
import numpy as np
from polygon_radiation import SurfaceModes
from hybrid_temporal_surface import surface_gram,surface_basis
from enriched_baffle import samples
from surface_reactive_fft import cell_integrals
from new_baffle_grid import kernel
from modal_string_radiation import response
from split_radiation import relative

def geometry(plate,poly,lift):
    base=SurfaceModes(plate,lift)
    H0,a0=surface_gram(plate['basis'],base,8,lift.shape[1])
    H,a=surface_gram(plate['basis'],base,12,lift.shape[1])
    ev,W=surface_basis(H);B=np.sqrt(ev)[:,None]*W.T
    field=SurfaceModes(plate,lift@W/np.sqrt(ev)[None,:])
    quad=(*samples(plate,field,6),*samples(plate,field,8))
    x,w,S=quad[3:]
    errors=dict(surfaceGram=relative(H,H0),fieldMap=relative(B.T@B,H),
        normalizedGram=relative(S.T@(w[:,None]*S),np.eye(len(ev))),
        area=max(abs(a-plate['areaM2']),abs(a0-plate['areaM2']))/plate['areaM2'])
    if max(errors.values())>1e-7:raise ValueError('local surface geometry '+str(errors))
    grids={}
    for n in (120,240):
        C,dx,dy,area=cell_integrals(poly,field,n)
        if abs(area-plate['areaM2'])/plate['areaM2']>1e-9:raise ValueError('cell area')
        grids[n]=(C,dx,dy)
    center=poly.mean(0);mic=np.array([[*center,.5],[center[0]+.25,center[1],1.5]])
    return B,field,quad,grids,mic,errors

def local_group(freq,grids,quad,mic,B,A,ctx,archived):
    Zs=[];Hs=[];Ys=[];Os=[];audit=[]
    for i,f in enumerate(freq):
        Z,H,k=kernel(f,grids,quad,mic)
        if not k['gate']:raise ValueError('local acoustic kernel convergence '+str(k))
        Y=[];O=[];checks=[]
        for j,(md,wires) in enumerate(ctx):
            yy,oo,p=response(md,A,wires,B.T@Z@B,H@B,f)
            if not p['gate']:raise ValueError('local harmonic algebra')
            Y.append(yy);O.append(oo)
            checks.append(dict(mobility=relative(yy,archived['mobility'][j,i]),pressure=relative(oo,archived['observation'][j,i])))
        Zs.append(Z);Hs.append(H);Ys.append(Y);Os.append(O)
        audit.append(dict(frequencyHz=f,kernel=k,externalReplay=checks,
            externalMaximum=max(max(v.values()) for v in checks)))
    return dict(impedance=np.stack(Zs),pressure=np.stack(Hs),mobility=np.stack(Ys,axis=1),observation=np.stack(Os,axis=1)),audit
