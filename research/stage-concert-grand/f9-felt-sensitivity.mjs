import {renderStringLoss} from './f9-string-loss.mjs';
// Scale both nonlinear elastic branches while preserving exponent and recovery time.
export const FELT_FACTORS=Object.freeze([.75,1,1.5]);
export function feltParameters(factor){
 if(!FELT_FACTORS.includes(factor))throw RangeError('felt stiffness factor');
 return {ke:1.4e9*factor,km:.6e9*factor,kr:1000,viscosity:1,power:2.5};
}
export function renderFeltSensitivity(hp,{feltFactor=1,prior=null,seconds=.5,velocity=1,scale=1,boardFactor=.5,angleRad=.5,spreadCents=.5,lossCase='both-half'}={}){
 const felt=feltParameters(feltFactor);
 if(scale!==1||boardFactor!==.5||angleRad!==.5||spreadCents!==.5||lossCase!=='both-half')throw RangeError('fixed B configuration');
 if(prior&&prior.feltFactor!==feltFactor)throw Error('felt checkpoint mismatch');
 let hammer=null,first=null,last=null,activeSteps=0,peakForce=0,peakCompression=0;
 class ObservedHammer extends hp.PolarizedHammer{
  constructor(bridge,options){super(bridge,{...options,felt});hammer=this;}
  step(){
   const t=this.time,q=super.step();
   if(q.sum>1e-9){first=first??t;last=t+this.h;activeSteps++;peakForce=Math.max(peakForce,q.sum);}
   peakCompression=Math.max(peakCompression,...q.compression);
   return q;
  }
 }
 const result=renderStringLoss({...hp,PolarizedHammer:ObservedHammer},{prior,seconds,velocity,scale,boardFactor,angleRad,spreadCents,lossCase});
 // Original renderer requires separation before returning. Contact interval is measured
 // using the step-average force threshold, not continuous contact event localization.
 const attack=first===null?null:{firstForceS:first,lastForceEndS:last,contactSpanS:last-first,activeContactS:activeSteps*hammer.h,activeSteps,peakForceN:peakForce,peakCompressionM:peakCompression,impulseNs:hammer.impulseNs,reboundMps:hammer.v,hammerLossJ:hammer.lossJ};
 if(!prior&&(!attack||!(attack.contactSpanS>0&&attack.reboundMps<0)))throw Error('missing attack or rebound');
 return {...result,checkpoint:{...result.checkpoint,feltFactor},meta:{...result.meta,feltFactor,felt,attack,hammerLossJ:hammer.lossJ,hammerImpulseNs:hammer.impulseNs}};
}
