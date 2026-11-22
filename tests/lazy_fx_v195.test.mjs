import test from 'node:test';
import assert from 'node:assert/strict';
import {engines,loadState} from '../patches.js';
import {FXRack} from '../fx-rack.js';

class FakeParam {
  constructor(value=0){this.value=value;}
  setTargetAtTime(value){this.value=value;}
}
class FakeNode {
  constructor(){for(const key of ['gain','frequency','Q','delayTime','pan','threshold','ratio','attack','release','knee'])this[key]=new FakeParam();this.connections=[];this.reduction=0;}
  connect(target){this.connections.push(target);return target;}
  disconnect(target){if(target)this.connections=this.connections.filter(node=>node!==target);else this.connections=[];}
  start(){}
}
function fakeContext(){
  const calls={gain:0,filter:0,comp:0,convolver:0,osc:0};
  const ctx={currentTime:0,sampleRate:4000,
    createGain(){calls.gain++;return new FakeNode()},
    createBiquadFilter(){calls.filter++;return new FakeNode()},
    createDynamicsCompressor(){calls.comp++;return new FakeNode()},
    createConvolver(){calls.convolver++;return new FakeNode()},
    createDelay(){return new FakeNode()},
    createOscillator(){calls.osc++;return new FakeNode()},
    createWaveShaper(){return new FakeNode()},
    createBuffer(channels,length){const data=Array.from({length:channels},()=>new Float32Array(length));return {getChannelData:i=>data[i],sampleRate:this.sampleRate,length}}
  };
  return {ctx,calls};
}

test('FX não cria processadores na inicialização, mesmo em PC completo',()=>{
  const {ctx,calls}=fakeContext(),state=loadState(null);
  const master=new FakeNode(),buses=Object.fromEntries(Object.keys(engines).map(x=>[x,new FakeNode()]));
  const rack=new FXRack(ctx,master,state,buses,{lite:false});
  assert.deepEqual(calls,{gain:0,filter:0,comp:0,convolver:0,osc:0});
  assert.equal(Object.values(rack.inserts).filter(Boolean).length,0);
  assert.equal(Object.values(rack.nodes).filter(x=>x?.input).length,0);
});

test('ativar EQ/Comp aloca apenas insert do destino, e mantém bypass limpo',()=>{
  const {ctx,calls}=fakeContext(),state=loadState(null),master=new FakeNode();
  const buses=Object.fromEntries(Object.keys(engines).map(x=>[x,new FakeNode()]));
  const rack=new FXRack(ctx,master,state,buses,{lite:false});
  state.fx.enabled.piano=true;state.fx.slots.eq.active=true;state.fx.slots.eq.targets=['piano'];rack.update();
  assert.ok(rack.inserts.piano);assert.equal(rack.inserts.electric,null);
  assert.ok(calls.filter>=10);
  const before=calls.comp;
  state.fx.slots.comp.active=true;state.fx.slots.comp.targets=['piano'];rack.update();
  assert.equal(calls.comp,before,'insert EQ e Comp reutilizam o mesmo grafo');
  state.fx.enabled.piano=false;rack.update();
  assert.equal(rack.inserts.piano.eqDry.gain.value,1);
  assert.equal(rack.inserts.piano.compDry.gain.value,1);
  assert.equal(rack.inserts.piano.compWet.gain.value,0);
});

test('reverb só é instanciado após ativar um destino FX',()=>{
  const {ctx,calls}=fakeContext(),state=loadState(null),master=new FakeNode();
  const buses=Object.fromEntries(Object.keys(engines).map(x=>[x,new FakeNode()]));
  const rack=new FXRack(ctx,master,state,buses,{lite:false});
  state.fx.slots.reverb1.active=true;state.fx.slots.reverb1.targets=['piano'];rack.update();
  assert.equal(calls.convolver,0,'destino com FX desligado não cria reverberação');
  state.fx.enabled.piano=true;rack.update();
  assert.equal(calls.convolver,2,'instancia apenas os convolvers da sessão usada');
  assert.equal(rack.sends.reverb1.piano.gain.value,1);
});
