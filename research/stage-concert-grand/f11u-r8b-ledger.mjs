// R8b diagnostic: diagonal modal coordinate energy, excludes bridge lifting
// and mass cross terms. Not the exact conserved energy; existing gate remains authoritative.
export const WINDOWS=Object.freeze([[.15,.45],[.8,1.1],[1.65,2.05],[3,3.5],[5,5.5],[9,9.5]].map(Object.freeze));
export function partialLedger(bridge,rate,windows=WINDOWS){
 if(!Number.isFinite(rate)||rate<=0)throw RangeError('rate');
 const axes=[bridge.vAxis,bridge.hAxis],selected=axes.map(a=>a.modes.map((m,i)=>({m,i})).filter(q=>q.m.n<=8));
 const rows=windows.map(([start,end])=>({start,end,count:0,vertical:Array(8).fill(0),horizontal:Array(8).fill(0)}));
 return {
  observe(step){
   const t=(step+1)/rate;
   const row=rows.find(w=>t>=w.start&&t<w.end);
   if(!row)return;
   row.count++;
   axes.forEach((a,j)=>{const dst=j?row.horizontal:row.vertical;
    for(const {m,i} of selected[j]){
     const e=.5*(m.m*a.v[i]**2+m.k*a.x[i]**2);
     if(!Number.isFinite(e)||e<0)throw Error('modal ledger');
     dst[m.n-1]+=e;
    }
   });
  },
  result(){
   return rows.map(w=>{
    if(!w.count)throw Error('empty ledger window');
    const vertical=w.vertical.map(v=>v/w.count),horizontal=w.horizontal.map(v=>v/w.count);
    const total=vertical.map((v,i)=>v+horizontal[i]);
    return {start:w.start,end:w.end,samples:w.count,vertical,horizontal,total,relativeDb:total.map(v=>10*Math.log10(Math.max(v,1e-40)/Math.max(total[0],1e-40)))};
   });
  }
 };
}
