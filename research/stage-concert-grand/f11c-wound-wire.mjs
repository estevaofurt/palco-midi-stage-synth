// F11c preparation: homogenized single helical winding, ideal pinned ends.
// Core carries axial load and bending; winding contributes mass only.
// No measured piano dimensions, end effects, winding contact stiffness or safety claim.
export function woundWire({lengthM,coreDiameterM,wrapDiameterM,pitchM=wrapDiameterM,f1Hz,coreYoungPa=200e9,coreDensityKgM3=7850,wrapDensityKgM3=8960}){
 const inputs=[lengthM,coreDiameterM,wrapDiameterM,pitchM,f1Hz,coreYoungPa,coreDensityKgM3,wrapDensityKgM3];
 if(!inputs.every(x=>Number.isFinite(x)&&x>0)||pitchM<wrapDiameterM)throw RangeError('wound wire geometry');
 const areaM2=Math.PI*coreDiameterM**2/4,wrapAreaM2=Math.PI*wrapDiameterM**2/4;
 const helixRatio=Math.hypot(1,Math.PI*(coreDiameterM+wrapDiameterM)/pitchM);
 const coreMu=coreDensityKgM3*areaM2,wrapMu=wrapDensityKgM3*wrapAreaM2*helixRatio,linearDensityKgM=coreMu+wrapMu;
 const EI=coreYoungPa*Math.PI*coreDiameterM**4/64;
 const tensionN=4*lengthM**2*linearDensityKgM*f1Hz**2-Math.PI**2*EI/lengthM**2;
 const B=Math.PI**2*EI/(tensionN*lengthM**2),stressPa=tensionN/areaM2;
 if(![linearDensityKgM,EI,tensionN,B,stressPa,helixRatio].every(x=>Number.isFinite(x)&&x>0))throw RangeError('invalid wound wire');
 return {kind:'single-wound-core-only-EI-hypothesis',lengthM,coreDiameterM,wrapDiameterM,pitchM,outerDiameterM:coreDiameterM+2*wrapDiameterM,coreYoungPa,coreDensityKgM3,wrapDensityKgM3,coreMu,wrapMu,helixRatio,linearDensityKgM,EI,tensionN,B,stressPa,f1Hz,areaM2,massKg:linearDensityKgM*lengthM};
}
