// G3: independent synthetic reciprocal oscillator diagnostic; no instrument parameters.
function runPilot() {
  const keys=[48,60,64,45,55,72], n=keys.length, bridge=n;
  const omega=keys.map(k=>2*Math.PI*440*2**((k-69)/12));
  const diag=omega.map(w=>w*w), springs=diag.map(w=>0.012*w);
  const base="1c565e346d40c9b818d9e8b1fadade740d0ebc2f";
  const duration=.5, eventList=[[0,"on",0,.3],[.015,"pedal",1],[.04,"on",1,1],[.08,"on",2,3],[.1,"off",0],[.12,"on",0,1],[.17,"off",1],[.2,"off",2],[.23,"off",0],[.35,"pedal",0]];
  function simulate(rate, blocked=-1, coupled=true) {
    const h=1/rate, N=Math.round(duration*rate);
    const k=springs.map(x=>coupled?x:0), kb=(2*Math.PI*180)**2+k.reduce((a,b)=>a+b,0);
    const K=diag.map((x,j)=>x+k[j]);
    const q=new Float64Array(n+1),v=new Float64Array(n+1),u=new Float64Array(n+1),rhs=new Float64Array(n+1);
    const H=new Float64Array(n), level=new Float64Array(n).fill(1), d=new Float64Array(n), held=new Array(n).fill(false);
    const damperLoss=new Float64Array(n), rms=new Float64Array(n), tail=new Float64Array(n), maxBefore=new Float64Array(n);
    const prefix=[], snapshots=[], count=[0,0]; let pedal=0, injected=0, loss=0, maxError=0, next=0, minimumLoss=0;
    function energy(){let e=.5*(v[bridge]**2+(2*Math.PI*180)**2*q[bridge]**2);for(let j=0;j<n;j++)e+=.5*(v[j]**2+diag[j]*q[j]**2+k[j]*(q[j]-q[bridge])**2);return e;}
    for(let i=0;i<N;i++){
      while(next<eventList.length&&Math.round(eventList[next][0]*rate)===i){
        const [,kind,j,speed]=eventList[next++];
        if(kind==="pedal")pedal=j;
        else if(kind==="off")held[j]=false;
        else {held[j]=true;const old=v[j];v[j]+=speed;injected+=.5*(v[j]**2-old**2);}
      }
      const hb=2/h+5+h*kb/2;
      let b=2*v[bridge]/h-kb*q[bridge], den=hb;
      for(let j=0;j<n;j++){
        const target=j===blocked?1:held[j]?0:1-pedal, inc=1/(.005*rate);
        level[j]+=Math.max(-inc,Math.min(inc,target-level[j]));
        d[j]=3+120*level[j];
        H[j]=2/h+d[j]+h*K[j]/2;
        rhs[j]=2*v[j]/h-K[j]*q[j]+k[j]*q[bridge];
        const off=-h*k[j]/2;
        b+=k[j]*q[j]-off*rhs[j]/H[j];
        den-=off*off/H[j];
      }
      u[bridge]=b/den;
      let dl=h*5*u[bridge]**2;
      for(let j=0;j<n;j++){u[j]=(rhs[j]+h*k[j]*u[bridge]/2)/H[j];const ed=h*120*level[j]*u[j]**2;damperLoss[j]+=ed;dl+=h*d[j]*u[j]**2;}
      for(let j=0;j<=n;j++){q[j]+=h*u[j];v[j]=2*u[j]-v[j];}
      loss+=dl;minimumLoss=Math.min(minimumLoss,dl);
      maxError=Math.max(maxError,Math.abs(energy()+loss-injected)/Math.max(Math.abs(injected),1e-30));
      if(i<Math.round(.015*rate)){for(let j=0;j<n;j++)maxBefore[j]=Math.max(maxBefore[j],Math.abs(v[j]));if(i%Math.max(1,rate/48000)===0)prefix.push(...q,...v);}
      if(i>=Math.round(.2*rate)&&i<Math.round(.3*rate)){count[0]++;for(let j=0;j<n;j++)rms[j]+=u[j]**2;}
      if(i>=Math.round(.4*rate)){count[1]++;for(let j=0;j<n;j++)tail[j]+=u[j]**2;}
      if((i+1)%Math.round(.05*rate)===0)snapshots.push({ms:1000*(i+1)/rate,energy:energy(),loss});
    }
    return {rate,blocked:blocked<0?null:keys[blocked],coupled,steps:N,maxEnergyResidual:maxError,minimumLoss,injected,finalEnergy:energy(),loss,damperLoss:[...damperLoss],rms:[...rms].map(x=>Math.sqrt(x/count[0])),tailRms:[...tail].map(x=>Math.sqrt(x/count[1])),prefix,maxBefore:[...maxBefore],snapshots};
  }
  const cases=[];
  let prefixError=0,unstruckLeak=0;
  for(const rate of [96000,192000,384000]){
    const open=simulate(rate);
    const rows=[open,...[3,4,5].map(j=>simulate(rate,j)),simulate(rate,-1,false)];
    for(const r of rows.slice(1,4)){for(let i=0;i<r.prefix.length;i++)prefixError=Math.max(prefixError,Math.abs(r.prefix[i]-open.prefix[i]));}
    const unc=rows[4];unstruckLeak=Math.max(unstruckLeak,...unc.rms.slice(3),...unc.tailRms.slice(3),...unc.maxBefore.slice(3));
    for(const r of rows){delete r.prefix;cases.push(r);}
  }
  const a=cases.filter(x=>x.rate===192000), b=cases.filter(x=>x.rate===384000);
  let maxRmsChange=0;
  for(let i=0;i<a.length;i++)for(const field of ["rms","tailRms"])for(let j=0;j<n;j++)maxRmsChange=Math.max(maxRmsChange,Math.abs(a[i][field][j]-b[i][field][j])/Math.max(Math.abs(b[i][field][j]),1e-12));
  const maxEnergyResidual=Math.max(...cases.map(x=>x.maxEnergyResidual));
  const gate=Number.isFinite(maxEnergyResidual)&&Number.isFinite(maxRmsChange)&&maxEnergyResidual<=1e-10&&maxRmsChange<=.02&&prefixError===0&&unstruckLeak===0&&cases.every(x=>x.minimumLoss>=0);
  return {base,diagnosticOnly:true,synthetic:true,hammerContact:false,acousticLoad:false,keys,events:eventList,duration,gate,maxEnergyResidual,maxRmsChange,prefixError,unstruckLeak,cases};
}
console.log(JSON.stringify(runPilot(),null,2));
