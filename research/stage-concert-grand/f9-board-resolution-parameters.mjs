// Numerical resolution experiment; no material or damping parameter changes.
export const BOARD_RESOLUTIONS=Object.freeze({
 reference:Object.freeze({basisHz:4000,cutoffHz:3000}),
 basis8:Object.freeze({basisHz:8000,cutoffHz:3000}),
 cutoff5:Object.freeze({basisHz:8000,cutoffHz:5000}),
 basis12:Object.freeze({basisHz:12000,cutoffHz:5000})
});
export function boardResolution(name){if(!Object.hasOwn(BOARD_RESOLUTIONS,name))throw RangeError('board resolution');return BOARD_RESOLUTIONS[name];}
export function resolutionMetrics(solution,cutoffHz){
 if(!Number.isFinite(cutoffHz)||cutoffHz<=0||!Number.isFinite(solution.residual)||solution.residual>1e-7||!Number.isFinite(solution.orthogonality)||solution.orthogonality>1e-7||!Number.isInteger(solution.basisCount)||solution.basisCount<1)throw Error('eigensystem quality');
 const modes=solution.modes.filter(m=>m.frequencyHz<cutoffHz);
 if(!modes.length||modes.some(m=>!Number.isFinite(m.frequencyHz)||m.frequencyHz<=0))throw Error('invalid retained modes');
 return {modes,basisCount:solution.basisCount,modeCount:modes.length,eigenResidual:solution.residual,massOrthogonality:solution.orthogonality,maxModeHz:modes.at(-1).frequencyHz};
}
