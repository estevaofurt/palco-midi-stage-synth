/** Synthetic delay-loop test fixture, NOT an acoustic piano model. */
export class MultiStringProbe {
  constructor(count=32,rate=48000){
    if(!Number.isInteger(count)||count<1||count>64)throw new RangeError('count 1..64');
    this.count=count;
    this.buffer=[];this.indices=new Int32Array(count);
    this.returns=0;this.feedback=0;
    this.dryL=this.dryR=this.bridgeL=this.bridgeR=0;
    for(let i=0;i<count;i++){
      const note=24+i,frequency=440*2**((note-69)/12);
      const n=Math.max(3,Math.round(rate/frequency));
      const loop=new Float64Array(n);
      for(let j=0;j<n;j++){
        const phase=2*Math.PI*j/n;
        loop[j]=.10*(Math.sin(phase)+.15*Math.sin(2*phase))*(.5-.5*Math.cos(phase));
      }
      this.buffer.push(loop);
    }
  }
  sample(){
    let y=0;
    for(let k=0;k<this.count;k++){
      const line=this.buffer[k],i=this.indices[k],v=line[i];
      line[i]=.9994*v+this.feedback*.014/this.count;
      if(++this.indices[k]>=line.length)this.indices[k]=0;
      y+=v;
    }
    const dry=y/Math.sqrt(this.count);
    this.bridgeL=this.bridgeR=this.dryL=this.dryR=dry;
  }
  pushBridge(impulse){this.feedback=Math.max(-.08,Math.min(.08,impulse));if(Math.abs(impulse)>1e-12)this.returns++}
  reset(){this.feedback=0;this.returns=0;for(const x of this.buffer)x.fill(0)}
}
