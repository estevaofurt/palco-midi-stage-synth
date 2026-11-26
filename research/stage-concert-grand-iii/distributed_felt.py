"""Distributed dissipative felt contact and wire stiffness loss hypotheses."""
import copy
import numpy as np
from numpy.polynomial.legendre import leggauss
from duplex_diagnostic import LOSS
from physical_pedal_repeat import damper_ports

def distributed_ports(a,rows,width,order=7,fraction=.18):
    if width<=0 or order<2 or not 0<fraction<1:raise ValueError('felt geometry')
    x,w=leggauss(order);weights=w/2
    B=np.zeros((a.n,a.nw*order));I=np.zeros((a.nw,a.partials,a.nw*order))
    for j,wire in enumerate(a.wires):
        key=int(wire.id.split('-')[0][1:]);L=rows[key]['lengthM']
        if width>=2*min(fraction,1-fraction)*L:raise ValueError('felt outside wire')
        f=fraction+x*width/(2*L);ids=slice(j*order,(j+1)*order)
        n=np.arange(1,len(wire.w2)+1)
        shape=np.sqrt(2/L)*np.sin(np.pi*n[:,None]*f[None,:])
        B[:,ids]=a.A[j,:,None]*f
        I[j,:,ids]=wire.U[:,:a.partials].T@shape
    return B,I,weights

def contact(a,rows,width,order=7):
    if width==0:
        B,I=damper_ports(a,rows);return B,I,np.ones(1)
    return distributed_ports(a,rows,width,order)

def damping_levels(d,w):
    return (np.asarray(d)[:,None]*w[None,:]).ravel()

def wire_loss(wires,scale):
    if not np.isfinite(scale) or scale<1:raise ValueError('stiffness loss factor')
    result=copy.deepcopy(wires)
    for w in result:
        w.D=2*(LOSS['mainSigma0PerS']*w.M+scale*LOSS['mainSigma2S']*w.K)
        w.d=w.U.T@w.D[1:,0]
        w.gamma=2*(LOSS['mainSigma0PerS']+scale*LOSS['mainSigma2S']*w.w2)
    return result
