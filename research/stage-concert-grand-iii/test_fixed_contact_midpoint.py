import unittest
import numpy as np
from types import SimpleNamespace
from compiled_wire_midpoint import Compiled
from physical_pedal_repeat import PointSchur,PointDense
from distributed_felt import contact,damping_levels
from fixed_contact_midpoint import FixedContacts
from split_radiation import relative
class FixedContactTest(unittest.TestCase):
    def test_fixed(self):
        M=np.array([[.5,.1],[.1,1.]])
        K=np.diag([100.,1000.]);D=.2*M+2e-9*K
        w=SimpleNamespace(M=M,K=K,D=D,P=np.array([.2,1.]),port=0,U=np.eye(1),id='k60-s1',
            m=M[1:,0],k=K[1:,0],d=D[1:,0],w2=np.diag(K)[1:],gamma=np.diag(D)[1:],p=np.array([1.]))
        make=lambda:Compiled(np.array([200.,500.]),np.eye(2),np.ones((2,1)),np.array([[.8,.2]]),[w],48000,1)
        for width in (0.,.005,.020):
            for level in (0.,.5,2.):
                a,b,c=make(),make(),make()
                B,I,wt=contact(a,{60:dict(lengthM=.5)},width)
                d=damping_levels([level],wt);A=PointSchur(a,B,I);R=PointSchur(b,B,I);Q=PointDense(c,B,I)
                for z in (A,R,Q):z.set_levels(d)
                f=np.random.default_rng(42).normal(size=(513,1));f[200:]=0
                o=np.zeros_like(f);l=np.zeros((len(f),2));acc=np.zeros((len(f),2))
                fixed=FixedContacts(A);fixed.process(f,o,l,acc)
                ref=[];led=[];ar=[]
                for F in f:
                    old=b.v.copy();y,work,loss=R.step(F);ref.append(y);led.append([work,loss]);ar.append((b.v-old)/b.h)
                    Q.step(F)
                self.assertLess(relative(o,np.asarray(ref)),1e-8)
                self.assertLess(relative(l,np.asarray(led)),1e-8)
                self.assertLess(relative(acc,np.asarray(ar)),1e-8)
                self.assertLess(relative(np.asarray(A.state()),np.asarray(Q.state())),1e-8)
                self.assertLess(abs(a.energy()+l[:,1].sum()-l[:,0].sum())/max(a.energy(),abs(l[:,0]).sum(),1e-30),1e-8)
                A.set_levels(d+1.)
                with self.assertRaises(ValueError):fixed.process(f,o,l,acc)
if __name__=='__main__':unittest.main()
