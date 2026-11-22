// Performance utilities layered on top of Stage. No extra audio engine or external timers.
const chords={off:[0],major:[0,4,7],minor:[0,3,7],sus2:[0,2,7],sus4:[0,5,7],fifth:[0,7,12]};
export const chordIntervals=id=>chords[id]||chords.off;
export const stepDuration=(bpm,rate)=>60000/Math.max(40,Math.min(240,bpm))*(rate==='1/4'?1:rate==='1/16'?.25:.5);
export class Performance{
  constructor(getStage,settings,onStatus=()=>{}){
    this.getStage=getStage;this.settings=settings;this.onStatus=onStatus;
    this.held=new Map();this.serial=0;this.arpTimer=null;this.arpVoice=null;this.position=0;
    this.recording=false;this.events=[];this.recordStart=0;this.loopTimer=null;this.loopStart=0;
    this.loopHeld=new Map();this.loopPlaying=false;
  }
  voiceNotes(item){return chordIntervals(this.settings.chord).map(n=>item.key+n).filter(n=>n>=0&&n<=127)}
  noteOn(source,channel,key,velocity,{fromLoop=false}={}){
    if(!Number.isInteger(key)||key<0||key>127||!Number.isFinite(velocity)||velocity<=0)return null;
    const item={id:++this.serial,source,channel,key,velocity,voices:[]};
    this.held.set(item.id,item);
    if(this.settings.arp){this.ensureArp()}else this.sound(item);
    if(this.recording&&!fromLoop)this.record('on',item);
    this.onStatus();return item.id;
  }
  sound(item){const st=this.getStage();if(!st)return;
    for(const note of this.voiceNotes(item)){
      const voice=st.startNote(item.source,item.channel,note,item.velocity);
      if(voice)item.voices.push(voice);
    }
  }
  noteOffId(id,{fromLoop=false}={}){
    const item=this.held.get(id);if(!item)return;
    this.held.delete(id);const st=this.getStage();
    for(const voice of item.voices)st?.releaseId(voice);
    if(this.recording&&!fromLoop)this.record('off',item);
    if(!this.held.size)this.haltArp();this.onStatus();
  }
  noteOff(source,channel,key){
    const item=[...this.held.values()].find(x=>x.source===source&&x.channel===channel&&x.key===key);
    if(item)this.noteOffId(item.id);
  }
  allNotesOff(source=null,channel=null){
    for(const item of [...this.held.values()]){
      if(source!==null&&item.source!==source)continue;
      if(channel!==null&&item.channel!==channel)continue;
      this.noteOffId(item.id);
    }
    if(!this.held.size)this.haltArp();
  }
  message(source,data){
    if(!data?.length)return;const [status,a,b=0]=data,op=status&240,ch=status&15;
    if(op===144&&b>0)return this.noteOn(source,ch,a,b);
    if(op===128||(op===144&&b===0))return this.noteOff(source,ch,a);
    if(op===176&&(a===120||a===123))this.allNotesOff(source,ch);
    return this.getStage()?.message(source,data);
  }
  setArp(enabled){
    if(this.settings.arp===enabled)return;
    this.allNotesOff();this.settings.arp=enabled;
    this.haltArp();this.onStatus();
  }
  ensureArp(){
    if(!this.settings.arp||this.arpTimer||!this.held.size)return;
    this.tickArp();this.arpTimer=setInterval(()=>this.tickArp(),stepDuration(this.settings.bpm,this.settings.rate));
  }
  restartArp(){if(this.arpTimer){clearInterval(this.arpTimer);this.arpTimer=null;this.ensureArp()}}
  tickArp(){
    const st=this.getStage();if(!st)return;
    if(this.arpVoice){st.releaseId(this.arpVoice);this.arpVoice=null}
    const notes=[...this.held.values()].flatMap(item=>this.voiceNotes(item).map(n=>({...item,n})));
    if(!notes.length){this.haltArp();return}
    notes.sort((a,b)=>a.n-b.n);const item=notes[this.position++%notes.length];
    this.arpVoice=st.startNote(item.source,item.channel,item.n,item.velocity);
  }
  haltArp(){
    if(this.arpTimer)clearInterval(this.arpTimer);this.arpTimer=null;
    if(this.arpVoice)this.getStage()?.releaseId(this.arpVoice);
    this.arpVoice=null;
  }
  record(type,item){
    if(!this.recording)return;
    const length=this.loopMs(),t=Math.max(0,performance.now()-this.recordStart);
    if(t>=length)return;
    this.events.push({type,t,source:item.source,channel:item.channel,key:item.key,velocity:item.velocity});
  }
  loopMs(){return 60000/this.settings.bpm*4*Number(this.settings.loopBars)}
  startRecording(){
    this.stopLoop();this.events=[];this.recording=true;this.recordStart=performance.now();
    this.recordEndTimer=setTimeout(()=>this.stopRecording(),this.loopMs());this.onStatus();
  }
  stopRecording(){
    if(!this.recording)return;
    clearTimeout(this.recordEndTimer);this.recording=false;
    // Release any note-on which had no note-off in the recording window.
    const outstanding=new Map();for(const event of this.events){const k=event.source+'/'+event.channel+'/'+event.key;
      if(event.type==='on')outstanding.set(k,event);else outstanding.delete(k)}
    for(const event of outstanding.values())this.events.push({...event,type:'off',t:Math.min(this.loopMs()-1,Math.max(event.t+80,performance.now()-this.recordStart))});
    this.events.sort((a,b)=>a.t-b.t);
    if(this.events.length)this.startLoop();this.onStatus();
  }
  startLoop(){
    if(!this.events.length)return;
    this.stopLoop();this.loopPlaying=true;this.loopStart=performance.now();this.loopIndex=0;this.loopCycle=0;
    this.loopTimer=setInterval(()=>this.tickLoop(),12);this.onStatus();
  }
  tickLoop(){
    if(!this.loopPlaying)return;
    const t=performance.now()-this.loopStart,length=this.loopMs();
    if(t-this.loopCycle*length>length*2){this.loopCycle=Math.floor(t/length);this.loopIndex=0}
    let processed=0;while(processed++<64){
      if(this.loopIndex>=this.events.length){this.loopIndex=0;this.loopCycle++}
      const ev=this.events[this.loopIndex],when=this.loopCycle*length+ev.t;
      if(when>t+4)break;
      const id=ev.source+'/'+ev.channel+'/'+ev.key;
      if(ev.type==='on'){
        const voice=this.noteOn('looper',ev.channel,ev.key,ev.velocity,{fromLoop:true});
        if(!this.loopHeld.has(id))this.loopHeld.set(id,[]);this.loopHeld.get(id).push(voice);
      } else {const voices=this.loopHeld.get(id)||[];if(voices.length)this.noteOffId(voices.shift(),{fromLoop:true})}
      this.loopIndex++;
      if(this.loopIndex===this.events.length&&this.loopCycle*length+length>t+length)break;
      if(this.loopIndex>this.events.length*2)break;
    }
  }
  stopLoop(){
    if(this.loopTimer)clearInterval(this.loopTimer);this.loopTimer=null;this.loopPlaying=false;
    for(const voices of this.loopHeld.values())for(const id of voices)this.noteOffId(id,{fromLoop:true});
    this.loopHeld.clear();this.onStatus();
  }
  clearLoop(){this.stopRecording();this.stopLoop();this.events=[];this.onStatus()}
  panic(){this.recording=false;clearTimeout(this.recordEndTimer);this.stopLoop();this.allNotesOff();this.haltArp()}
  disconnect(source){this.allNotesOff(source);this.getStage()?.disconnect(source)}
}
