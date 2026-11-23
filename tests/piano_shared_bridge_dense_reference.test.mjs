/**
 * Independent numerical oracle for the research-only shared piano bridge.
 * A dense Gaussian solve, built from M/C/K each sample, deliberately does NOT
 * reuse the production Schur complement nor any cached factorization.
 * This tests equation implementation, not acoustic fidelity.
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import {SharedPassivePianoBridge} from '../research/shared-passive-piano-bridge.mjs';

function denseState(model){
  return {
    x:Float64Array.from([...model.x,...model.bx]),
    v:Float64Array.from([...model.v,...model.bv]),
  };
}

function solveByGaussianElimination(A,b){
  const n=b.length;
  const x=Float64Array.from(b);
  for(let j=0;j<n;j++){
    let pivot=j;
    for(let i=j+1;i<n;i++)
      if(Math.abs(A[i][j])>Math.abs(A[pivot][j]))pivot=i;
    assert.ok(Math.abs(A[pivot][j])>1e-20,'dense reference must be nonsingular');
    if(pivot!==j){[A[j],A[pivot]]=[A[pivot],A[j]];
      [x[j],x[pivot]]=[x[pivot],x[j]];}
    for(let i=j+1;i<n;i++){
      const q=A[i][j]/A[j][j];
      for(let k=j+1;k<n;k++)A[i][k]-=q*A[j][k];
      x[i]-=q*x[j];
      A[i][j]=0;
    }
  }
  for(let i=n-1;i>=0;i--){
    for(let j=i+1;j<n;j++)x[i]-=A[i][j]*x[j];
    x[i]/=A[i][i];
  }
  return x;
}

function denseMidpointStep(p,ref){
  const ns=p.n,N=ns+2,h=p.dt;
  const K=Array.from({length:N},()=>new Float64Array(N));
  const m=new Float64Array(N),c=new Float64Array(N),f=new Float64Array(N);
  for(let i=0;i<ns;i++){
    const spring=p.coupling[i];
    m[i]=p.mass[i];c[i]=p.damping[i];f[i]=p.forces[i];
    K[i][i]=p.ground[i]+spring;
    K[i][ns]=-spring;
    K[ns][i]=-spring;
    K[ns][ns]+=spring;
  }
  for(let i=0;i<2;i++){
    m[ns+i]=p.bmass[i];c[ns+i]=p.bdamper[i];
    K[ns+i][ns+i]+=p.bground[i]+p.boardSpring;
  }
  K[ns][ns+1]=-p.boardSpring;
  K[ns+1][ns]=-p.boardSpring;
  const A=Array.from({length:N},()=>new Float64Array(N));
  const b=new Float64Array(N);
  for(let i=0;i<N;i++){
    let restoring=0;
    for(let j=0;j<N;j++){
      restoring+=K[i][j]*ref.x[j];
      A[i][j]=h*h*.25*K[i][j];
    }
    A[i][i]+=m[i]+h*.5*c[i];
    b[i]=m[i]*ref.v[i]-h*.5*restoring+h*.5*f[i];
  }
  const midpointVelocity=solveByGaussianElimination(A,b);
  for(let i=0;i<N;i++){
    ref.x[i]+=h*midpointVelocity[i];
    ref.v[i]=2*midpointVelocity[i]-ref.v[i];
  }
  return .67*midpointVelocity[ns]+.33*midpointVelocity[ns+1];
}

function near(actual,expected,context){
  const tolerance=2e-11+2e-8*Math.max(Math.abs(actual),Math.abs(expected));
  assert.ok(Number.isFinite(actual)&&Math.abs(actual-expected)<=tolerance,
    `${context}: optimized=${actual}, dense=${expected}, tolerance=${tolerance}`);
}

test('O(N) Schur bridge matches independent dense M/C/K implicit midpoint state and output',()=>{
  for(const sampleRate of [44100,48000,96000])
  for(const coupling of [0,.12,.8])
  for(const keys of [[36],[21,48,72],[24,36,43,60,84]]){
    const fast=new SharedPassivePianoBridge({sampleRate,coupling,keys});
    fast.setInitialStringDisplacement(0,6e-5);
    fast.v[1]=.00013;
    fast.bx[1]=2e-7;
    const ref=denseState(fast);
    for(let frame=0;frame<97;frame++){
      fast.forces.fill(0);
      if(frame<14)fast.forces[0]=3*Math.sin(Math.PI*(frame+.5)/14)**2;
      if(frame>=8&&frame<30)fast.forces[fast.n-1]=1.2;
      const actual=fast.step();
      const expected=denseMidpointStep(fast,ref);
      near(actual,expected,`board sample=${frame} rate=${sampleRate} coupling=${coupling}`);
      for(let i=0;i<fast.n;i++){
        near(fast.x[i],ref.x[i],`x[${i}] frame=${frame}`);
        near(fast.v[i],ref.v[i],`v[${i}] frame=${frame}`);
      }
      for(let i=0;i<2;i++){
        near(fast.bx[i],ref.x[fast.n+i],`bx[${i}] frame=${frame}`);
        near(fast.bv[i],ref.v[fast.n+i],`bv[${i}] frame=${frame}`);
      }
    }
  }
});

test('complete 88-key research network remains passive with distinct physical keys',()=>{
  const keys=Array.from({length:88},(_,i)=>21+i);
  for(const sampleRate of [44100,48000,96000]){
    const p=new SharedPassivePianoBridge({sampleRate,keys,coupling:.5});
    assert.equal(p.n,176);
    for(let i=0;i<p.n;i+=13)p.setInitialStringDisplacement(i,2e-6);
    let previous=p.energy();
    for(let frame=0;frame<256;frame++){
      const y=p.step();
      const next=p.energy();
      assert.ok(Number.isFinite(y)&&Number.isFinite(next));
      assert.ok(next>=0&&next<=previous+1e-10,
        `unexpected energy growth: rate=${sampleRate}, frame=${frame}`);
      previous=next;
    }
  }
});
