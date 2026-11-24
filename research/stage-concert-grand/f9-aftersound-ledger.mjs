// F9.6: coordinate-energy diagnostics only. The modal diagonal energy omits bridge cross terms.
export function polarizationLedger(bridge){
 const axis=a=>{const wireJ=bridge.wires.map((_,j)=>a.wireEnergy(j)),diagonalByPartial=Array(10).fill(0);for(let i=0;i<a.modes.length;i++){const m=a.modes[i];if(m.n<=10)diagonalByPartial[m.n-1]+=.5*(m.m*a.v[i]**2+m.k*a.x[i]**2);}return {wireJ,diagonalByPartial,bridgeDisplacementM:a.b,bridgeVelocityMps:a.vb};};
 return {vertical:axis(bridge.vAxis),horizontal:axis(bridge.hAxis),crossSpringJ:bridge.K.vh*bridge.vAxis.b*bridge.hAxis.b,stringLossJ:bridge.stringLossJ,bridgeLossJ:bridge.bridgeLossJ};
}
export function validateAngle(angleRad){if(![.25,.5].includes(angleRad))throw RangeError('experimental angle must be .25 or .5 rad');return angleRad;}
