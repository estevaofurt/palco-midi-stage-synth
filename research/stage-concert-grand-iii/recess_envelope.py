"""Closed artificial exterior interface enclosing both acoustic domains.
The lower mouth is an interface, not a solid floor. Rim thickness omitted.
"""
import numpy as np
from neumann_envelope import envelope,geometry_audit
from lid_exterior import Panel
from lower_prism import mouth_panel
from board_contour import properties
from bem_envelope import triangulate

def build(poly,top,bottom,angle,count,field,mouth_count):
    if not bottom<0<top:raise ValueError('invalid cabinet heights')
    poly=np.asarray(poly,float);A,center,_=properties(poly)
    surfaces,ports,inside=envelope(poly,top,angle,count,field)
    upper=geometry_audit(surfaces,ports,inside)
    if surfaces[-1]['kind']!='board':raise ValueError('unexpected upper envelope')
    surfaces=surfaces[:-1];ports=ports[:-1]
    for a,b in zip(poly,np.roll(poly,-1,axis=0)):
        d=b-a;n=np.r_[d[1],-d[0],0.];n/=np.linalg.norm(n)
        v=np.array([np.r_[a,bottom],np.r_[b,bottom],np.r_[b,0.],np.r_[a,0.]])
        surfaces.append(dict(panel=Panel(v,n,1),normal=n,kind='rigid',port=None))
    mouth=mouth_panel(poly,-bottom,mouth_count);ports.append(mouth)
    surfaces.append(dict(panel=mouth,normal=np.array([0.,0.,-1.]),kind='lower-mouth',port=len(ports)-1))
    rep=geometry_audit(surfaces,ports,inside)
    expected=upper['volume']-A*bottom
    rep.update(upperVolume=upper['volume'],lowerVolume=-A*bottom,expectedVolume=expected,
        volumeError=abs(rep['volume']-expected),lowerMouthArea=mouth.basis.area,
        mouthAreaError=abs(mouth.basis.area-A))
    rep['gate']=bool(rep['gate'] and rep['volumeError']<=1e-10 and rep['mouthAreaError']<=1e-10)
    if not rep['gate']:raise ValueError('invalid recessed envelope')
    return surfaces,ports,inside,rep
