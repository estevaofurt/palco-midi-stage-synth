import assert from 'node:assert/strict';
import {boardResponse,solveReal} from './f11u-r9-transfer.mjs';
assert.deepEqual(solveReal([[0,1],[2,1]],[3,5]),[1,3]);
const f=100,w=2*Math.PI*f,b={modes:[{coeff:{k:w*w,massKg:1,dampingNsM:2}}],blocks:[{indices:[0],R:[[3]]}]};
const r=boardResponse(b,[1],f,[[0],[0]],()=>({re:1,im:0}));
assert(Math.abs(r.mobility.re-.2)<1e-12);
assert(Math.abs(r.mobility.im)<1e-12);
assert(Math.abs(r.stereoMagnitude-w/5)<1e-9);
console.log('R9_TRANSFER_UNIT_PASS');
