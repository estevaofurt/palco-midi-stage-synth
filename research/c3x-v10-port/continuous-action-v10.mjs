/**
 * C3X V10 continuous_action.py scheduler: direct offline JS translation.
 * Source: research/c3x-python/v10/stage_synth_c3x/continuous_action.py
 * This schedules hammer strikes only: NO audio, samples, VST or AudioWorklet.
 * Experimental geometry remains estimated; not a measured Yamaha action.
 */
export const DEFAULT_ACTION_V10=Object.freeze({
 key_dip_mm:10,escapement_key_fraction:.82,
 double_reset_fraction:.54,single_reset_fraction:.13,
 key_speed_ratio:.32,key_release_speed_m_s:.47,
 hammer_flight_mm:1.7,hammer_flight_drag_per_s:3,
 backcheck_double_ms:12,backcheck_single_ms:35,
 felt_rate_exponent:.055,simulation_hz:2000,
 damper_release_fraction:.22
});
const finite=x=>typeof x==='number'&&Number.isFinite(x);
const integer=x=>finite(x)&&Number.isInteger(x);
const pyRound=(x,n=0)=>{
 const k=10**n,y=x*k,l=Math.floor(y),f=y-l;
 return (f<.5?l:f>.5?l+1:l%2===0?l:l+1)/k;
};
export const hammerSpeedV10=velocity=>.45+(velocity/127)**1.45*(2.6-.45);
export const velocityFromHammerSpeedV10=speed=>{
 const f=Math.max(0,Math.min(1,(speed-.45)/(2.6-.45)));
 return Math.max(1,Math.min(127,pyRound(127*f**(1/1.45))));
};
export function validateActionV10(config={}){
 const c={...DEFAULT_ACTION_V10,...config};
 if(!Object.values(c).every(finite)||!(
 5<=c.key_dip_mm&&c.key_dip_mm<=13&&
 .55<=c.escapement_key_fraction&&c.escapement_key_fraction<=.95&&
 0<c.single_reset_fraction&&c.single_reset_fraction<c.double_reset_fraction&&
 c.double_reset_fraction<c.escapement_key_fraction&&
 .05<=c.key_speed_ratio&&c.key_speed_ratio<=1&&
 .05<=c.key_release_speed_m_s&&c.key_release_speed_m_s<=2&&
 .3<=c.hammer_flight_mm&&c.hammer_flight_mm<=5&&
 0<=c.hammer_flight_drag_per_s&&c.hammer_flight_drag_per_s<=30&&
 2<=c.backcheck_double_ms&&c.backcheck_double_ms<=c.backcheck_single_ms&&c.backcheck_single_ms<=90&&
 0<=c.felt_rate_exponent&&c.felt_rate_exponent<=.18&&
 integer(c.simulation_hz)&&500<=c.simulation_hz&&c.simulation_hz<=10000&&
 0<c.damper_release_fraction&&c.damper_release_fraction<c.single_reset_fraction+.4))
 throw RangeError('Invalid C3X V10 continuous-action parameters');
 return c;
}
function validated(c,length,isKeyframe){
 if(!Array.isArray(c)||c.length!==4||!c.every(finite))throw RangeError('Invalid C3X V10 event');
 const [t,key,d,v]=c;
 if(!(0<=t&&t<length&&integer(key)&&21<=key&&key<=108&&
  0<=d&&d<=(isKeyframe?1:length)&&integer(v)&&
  (isKeyframe?0:1)<=v&&v<=127))
 throw RangeError('C3X V10 action event out of range');
 return c;
}
/**
 * Exact control-path model of schedule_continuous_action; allocates per-note
 * arrays and MUST NOT run on a real-time AudioWorklet callback.
 */
export function scheduleContinuousV10(events=[],length=1,{
 keyframes=null,config={},mode='double',includeTrajectories=false
}={}){
 const cfg=validateActionV10(config);
 if(mode!=='double'&&mode!=='single')throw RangeError('Unknown action mode');
 if(!finite(length)||length<=0||length>60)throw RangeError('Invalid render duration');
 if(!Array.isArray(events)||keyframes!==null&&!Array.isArray(keyframes))throw TypeError('events/keyframes arrays required');
 if(keyframes!==null&&events.length)throw RangeError('events and keyframes are exclusive');
 let frames;
 if(keyframes!==null)frames=keyframes.map(e=>validated(e,length,true));
 else {
  frames=[];
  const ordered=events.map(e=>validated(e,length,false))
   .sort((a,b)=>a[0]-b[0]||a[1]-b[1]);
  for(const [t,key,hold,vel] of ordered){
   frames.push([t,key,1,vel]);
   if(t+hold<length)frames.push([t+hold,key,0,0]);
  }
 }
 const byKey=new Map();
 for(const [t,key,depth,vel] of frames){
  if(!byKey.has(key))byKey.set(key,[]);
  byKey.get(key).push([t,depth,vel]);
 }
 const dt=1/cfg.simulation_hz,count=Math.ceil(length*cfg.simulation_hz);
 const reset=mode==='double'?cfg.double_reset_fraction:cfg.single_reset_fraction;
 const rearm=(mode==='double'?cfg.backcheck_double_ms:cfg.backcheck_single_ms)*.001;
 const scheduled=[],impacts=[],blocked=[],rearmlist=[],traj={};
 for(const key of [...byKey.keys()].sort((a,b)=>a-b)){
  const commands=byKey.get(key).sort((a,b)=>a[0]-b[0]||a[1]-b[1]);
  let position=0,target=0,currentVel=90,state='ready',flightEnd=null;
  let lastImpact=-1e9,cmdIndex=0,lastPressedTime=0;
  const holds=[],strikes=[],positions=[];
  for(let i=0;i<count;i++){
   const t=i*dt;
   while(cmdIndex<commands.length&&commands[cmdIndex][0]<=t+1e-10){
    const [ct,dep,vel]=commands[cmdIndex++];
    target=dep;
    if(dep>position+1e-9&&vel>0)currentVel=vel;
    if(dep>=cfg.escapement_key_fraction)lastPressedTime=ct;
   }
   const prev=position;
   const downRate=cfg.key_speed_ratio*hammerSpeedV10(currentVel)/(.001*cfg.key_dip_mm);
   const upRate=cfg.key_release_speed_m_s/(.001*cfg.key_dip_mm);
   const movement=(target>=position?downRate:-upRate)*dt;
   position=movement>0?Math.min(target,position+movement):Math.max(target,position+movement);
   if(includeTrajectories&&i%10===0)positions.push([pyRound(t,5),pyRound(position,5),state]);
   if(state==='flying'&&flightEnd!==null&&t+1e-12>=flightEnd.impact_s){
    const strike={...flightEnd,midi:key,position_at_impact:pyRound(position,5)};
    strikes.push(strike);impacts.push(strike);
    lastImpact=t;state='checked';flightEnd=null;
   }
   if(state==='checked'&&position<=reset){
    state='rearming';
    rearmlist.push({midi:key,at_s:pyRound(t,5),key_position:pyRound(position,4)});
   }
   if(state==='rearming'&&position<=reset&&t>=lastImpact+rearm)state='ready';
   if(state==='rearming'&&position>reset)state='checked';
   if(prev<cfg.escapement_key_fraction&&cfg.escapement_key_fraction<=position){
    if(state==='ready'){
     const speed=hammerSpeedV10(currentVel);
     const flight=cfg.hammer_flight_mm*.001/Math.max(speed,1e-9);
     const speedImpact=speed*Math.exp(-cfg.hammer_flight_drag_per_s*flight);
     flightEnd={
      command_at_s:lastPressedTime,
      escapement_at_s:pyRound(t,6),
      impact_s:pyRound(t+flight,6),
      hammer_speed_m_s:speedImpact,
      velocity_midi:velocityFromHammerSpeedV10(speedImpact),
      key_speed_m_s:cfg.key_speed_ratio*speed,
      mode
     };
     state='flying';
    }else blocked.push({midi:key,at_s:pyRound(t,6),reason:'jack_not_reset',state});
   }
   holds.push(position);
  }
  for(const strike of strikes){
   const ix=Math.min(count-1,Math.max(0,pyRound(strike.impact_s*cfg.simulation_hz)));
   let end=length;
   for(let k=ix+1;k<count;k++)if(holds[k]<=cfg.damper_release_fraction){end=k*dt;break;}
   scheduled.push([strike.impact_s,key,Math.max(.012,end-strike.impact_s),strike.velocity_midi]);
   strike.key_off_s=pyRound(end,6);
  }
  if(includeTrajectories)traj[key]=positions;
 }
 scheduled.sort((a,b)=>a[0]-b[0]||a[1]-b[1]);
 impacts.sort((a,b)=>a.impact_s-b.impact_s||a.midi-b.midi);
 return {scheduled,diagnostics:{
  action_events:impacts,keyframe_count:frames.length,
  blocked_events:blocked,blocked_count:blocked.length,strike_count:impacts.length,
  rearm_events:rearmlist,unique_key_count:byKey.size,mode,
  key_trajectories:includeTrajectories?traj:null
 }};
}
