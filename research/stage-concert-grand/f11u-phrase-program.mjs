// Original listening phrase: bass and arpeggiated C major, repeated E4,
// contrasted velocities, release under sustain and pedal-up tail.
export const phraseNotes=[48,60,64,67,72];
export function phrase(){
 const e=[{ms:0,type:'pedal',value:127}];
 for(const [ms,midi,velocity,length] of [[0,48,76,700],[240,60,52,650],[480,64,64,600],[720,67,76,650],[960,72,76,700],[1900,64,44,250],[2350,64,88,300],[2800,67,76,600],[3500,60,76,900],[3500,64,76,900],[3500,67,76,900],[3500,72,76,900],[6500,48,44,500],[6750,60,52,500],[7000,64,64,500],[7250,67,76,600]]){
 e.push({ms,type:'on',midi,velocity},{ms:ms+length,type:'off',midi});
 }
 e.push({ms:5400,type:'pedal',value:0},{ms:6400,type:'pedal',value:127},{ms:8200,type:'pedal',value:0});
 return e.sort((a,b)=>a.ms-b.ms);
}
