// F9.15: vary only the stiffness of the existing passive bridge-board joint.
export const JOINT_FACTORS=Object.freeze([.5,1,2]);
export function jointParameters(factor){if(!JOINT_FACTORS.includes(factor))throw RangeError('joint stiffness factor');return {jointK:1e7*factor,jointC:1};}
