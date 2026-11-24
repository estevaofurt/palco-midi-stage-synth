// Experimental strike geometry, no change to the reference felt or string losses.
export const STRIKE_FRACTIONS=Object.freeze([.08,.10,.13]);
export function validateStrike(fraction){if(!STRIKE_FRACTIONS.includes(fraction))throw RangeError('strike fraction');return fraction;}
