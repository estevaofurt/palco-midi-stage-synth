// Research-only configuration contract. Not wired to the live Stage.
export const OPTIONS=Object.freeze(['auto',32,64,88,96,128,192,256]);
export const STORAGE_KEY='palco-stage-polyphony-v1';
export function parsePolyphony(value){
  if(value==='auto'||value===null||value===undefined)return 'auto';
  if(typeof value==='string'&&!/^(32|64|88|96|128|192|256)$/.test(value))return 'auto';
  if(typeof value!=='number'&&typeof value!=='string')return 'auto';
  const n=Number(value);return OPTIONS.includes(n)?n:'auto';
}
export function resolvePolyphony(requested,{profile='lite',engineCapacity,verifiedCapacity}={}){
  const fallback=profile==='full'?64:32;
  // Unknown/uncertified engines keep their existing limits. A benchmark
  // of an isolated kernel must never automatically authorize the app.
  const valid=v=>Number.isInteger(v)&&v>0&&v<=256;
  const cap=Math.min(valid(engineCapacity)?engineCapacity:fallback,valid(verifiedCapacity)?verifiedCapacity:fallback);
  const choice=parsePolyphony(requested);
  const effective=Math.min(choice==='auto'?fallback:choice,cap);
  return {requested:choice,effective,capacity:cap,limited:choice!=='auto'&&effective!==choice};
}
