import {renderStringLoss} from './f9-string-loss.mjs';
export const QUADRATURES=Object.freeze({reference:Object.freeze({nt:12,np:24}),medium:Object.freeze({nt:24,np:48}),fine:Object.freeze({nt:48,np:96})});
export function quadrature(name){if(!Object.hasOwn(QUADRATURES,name))throw RangeError('quadrature');return QUADRATURES[name];}
// Reuse the frozen F9.8 integrator, not a copy. Only the board constructor's angular integration changes.
export function renderRadiationRefinement(hp,{quadratureCase='reference',prior=null,seconds=.5,velocity=1,scale=1,boardFactor=.5,angleRad=.5,spreadCents=.5,lossCase='both-half'}={}){
 const q=quadrature(quadratureCase);
 if(scale!==1||boardFactor!==.5||angleRad!==.5||spreadCents!==.5||lossCase!=='both-half')throw RangeError('fixed reference configuration');
 if(prior&&prior.quadratureCase!==quadratureCase)throw Error('quadrature checkpoint mismatch');
 class RefinedBoard extends hp.ResistiveBoard{
  constructor(p,modes,patch,h,options,helpers){super(p,modes,patch,h,{...options,radiation:{...options.radiation,...q}},helpers);}
 }
 const result=renderStringLoss({...hp,ResistiveBoard:RefinedBoard},{prior,seconds,velocity,scale,boardFactor,angleRad,spreadCents,lossCase});
 return {...result,checkpoint:{...result.checkpoint,quadratureCase},meta:{...result.meta,quadratureCase,nt:q.nt,np:q.np}};
}
