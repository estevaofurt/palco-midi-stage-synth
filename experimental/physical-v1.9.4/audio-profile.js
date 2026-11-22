// Perfis de processamento separados dos presets musicais.
export const PROFILES = Object.freeze({lite:{voices:32,meterInterval:240},full:{voices:64,meterInterval:80}});
export const PROFILE_STORAGE_KEY='palco-stage-audio-profile-v1';
export function defaultProfile(navigatorLike={}){
  const ua=navigatorLike.userAgent||'';
  const lowMemory=Number(navigatorLike.deviceMemory)>0&&Number(navigatorLike.deviceMemory)<=4;
  const lowCores=Number(navigatorLike.hardwareConcurrency)>0&&Number(navigatorLike.hardwareConcurrency)<=4;
  return /Android|iPhone|iPad|Mobile/i.test(ua)||lowMemory||lowCores?'lite':'full';
}
export function getProfile(storage,navigatorLike={}){
  let saved;try{saved=storage?.getItem(PROFILE_STORAGE_KEY)}catch{}
  return Object.hasOwn(PROFILES,saved)?saved:defaultProfile(navigatorLike);
}
export function profilePolyphony(profile){return PROFILES[profile]?.voices||32}
