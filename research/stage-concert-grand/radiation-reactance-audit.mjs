// F7.3 diagnostic only: approximate complex Rayleigh impedance on a single prescribed mode. Self cell cosine kernel uses its static singular integral.
export function impedanceDiagnostic(p,m,f,nx,ny,hp){
 const dx=p.lengthM/nx,dy=p.widthM/ny,dS=dx*dy,omega=2*Math.PI*f,k=omega/343,rho=1.204,points=[];
 for(let i=0;i<nx;i++)for(let j=0;j<ny;j++){const x=(i+.5)*dx,y=(j+.5)*dy;points.push({x,y,z:hp.surfaceShape(m,x,y)});}
 const a=dx/2,b=dy/2,self=4*(a*Math.asinh(b/a)+b*Math.asinh(a/b));
 let re=0,im=0;for(let i=0;i<points.length;i++){const u=points[i];re+=u.z*u.z*k*dS*dS;im+=u.z*u.z*self*dS;for(let j=0;j<i;j++){const v=points[j],d=Math.hypot(u.x-v.x,u.y-v.y),s=2*u.z*v.z*dS*dS/d;re+=s*Math.sin(k*d);im+=s*Math.cos(k*d);}}
 return {nx,ny,R:rho*omega/(2*Math.PI)*re,X:rho*omega/(2*Math.PI)*im};
}
