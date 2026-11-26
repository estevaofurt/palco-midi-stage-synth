import {parsePolyphony} from './polyphony_policy.mjs';
// Experimental ceilings derived from isolated Node tests, not device certification.
export function candidateModalCapacity(request,profile,rate){
  const choice=parsePolyphony(request);
  const cap=profile==='lite'||!Number.isFinite(rate)||rate>48000?64:192;
  return Math.min(choice==='auto'?32:choice,cap);
}
export function candidateVoiceLimit(request,legacy,modal,modalOnly){
  const choice=parsePolyphony(request);
  return modalOnly?modal:Math.min(legacy,choice==='auto'?legacy:choice);
}
