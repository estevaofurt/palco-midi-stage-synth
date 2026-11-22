import test from 'node:test';import assert from 'node:assert/strict';

test('processor registers and sends actual signal for note-on/off and quality changes',async()=>{
 let Processor;
 globalThis.sampleRate=48000;
 globalThis.AudioWorkletProcessor=class {constructor(){this.port={messages:[],postMessage(data){this.messages.push(data)}}}};
 globalThis.registerProcessor=(name,ctor)=>{if(name==='palco-physical-piano')Processor=ctor};
 try{
   await import(`../physical-piano.js?worklet-${Math.random()}`);
   assert.ok(Processor);
   const node=new Processor();
   node.port.onmessage({data:{type:'quality',quality:'eco'}});
   node.port.onmessage({data:{type:'mechanics',enabled:true,amount:.6,sympathy:true}});
   node.port.onmessage({data:{type:'pedal',value:127}});
   assert.equal(node.engine.mechanicalTarget,1);
   assert.equal(node.engine.mechanics.pedal,1);
   node.port.onmessage({data:{type:'on',id:10,key:60,speed:.8}});
   const L=new Float32Array(128),R=new Float32Array(128),S=new Float32Array(128);
   let audible=false;
   for(let i=0;i<70;i++){
     const ok=node.process([],[[L,R],[S]]);assert.equal(ok,true);
     if(L.some(x=>Math.abs(x)>1e-5))audible=true;
   }
   assert.ok(audible);
   node.port.onmessage({data:{type:'param',id:10,brightness:.7,damping:.8}});
   node.port.onmessage({data:{type:'off',id:10,fast:true}});
   node.port.onmessage({data:{type:'pedal',value:0}});
   for(let i=0;i<1500;i++)node.process([],[[L,R],[S]]);
   assert.equal(node.engine.find(10),null);
   assert.ok(node.port.messages.some(x=>x.type==='done'&&x.ids.includes(10)));
 }finally{delete globalThis.sampleRate;delete globalThis.registerProcessor;delete globalThis.AudioWorkletProcessor;}
});
