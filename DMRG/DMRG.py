'''
DMRG.
'''

__all__=['Block','IDMRG']

from ..Math.Tensor import *
from ..Math.MPS import *
from ..Basics import *

class Block(object):
    '''
    '''
    def __init__(self,length,lattice,basis,H):
        self.length=length
        self.lattice=lattice
        self.basis=basis
        self.H=H

class IDMRG(Engine):
    '''
    '''
    def __init__(self,name,lattice,config,term,**karg):
        self.name=name
        self.lattice=lattice
        self.config=config
        self.table=config.table
        self.term=term
        self.sys=Block()
        self.env=Block()

    def proceed(self):
        self.enlarge_lattice()
        self.find_operators()
        self.set_matrix()
        self.find_gs()
        self.truncate()

    def enlarge_lattice(self):
        sp,ep=self.lattice.point.values[0],self.lattice.point.values[0]
        