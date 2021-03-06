'''
dmrg template.
'''

__all__=['fdmrg','idmrg']

fdmrg_template="""\
import numpy as np
import HamiltonianPy.DMRG as DMRG
from HamiltonianPy import *
from HamiltonianPy.TensorNetwork import *
from .config import *

__all__=['fdmrgconstruct']

def fdmrgconstruct(name,parameters,lattice,terms,target,niter=None,{argumentstatistics}boundary=None,**karg):
    config=IDFConfig(priority=DEFAULT_{system}_PRIORITY,map=idfmap)
    degfres=DegFreTree(layers=DEGFRE_{system}_LAYERS,map=qnsmap)
    if isinstance(lattice,Cylinder):
        tsg=DMRG.TSG(name='GROWTH',target=target,maxiter=niter,nmax=100,plot=False,run=DMRG.fDMRGTSG)
        tss=DMRG.TSS(name='SWEEP',target=target(niter-1),nsite=DMRG.NS(config,degfres,lattice,[{mask}])*2*niter,nmaxs=[100,100],run=DMRG.fDMRGTSS)
    else:
        tsg=None
        tss=DMRG.TSS(name='SWEEP',target=target,nsite=DMRG.NS(config,degfres,lattice,[{mask}]),nmaxs=[100,100],run=DMRG.fDMRGTSS)
    dmrg=DMRG.fDMRG(
        dlog=       'log',
        din=        'data',
        dout=       'result/fdmrg',
        name=       '%s_%s'%(name,lattice.name),
        tsg=        tsg,
        tss=        tss,
        parameters= parameters,
        map=        parametermap,
        lattice=    lattice,
        config=     config,
        degfres=    degfres,
        terms=      [term({termstatistics}**parameters) for term in terms],
        mask=       [{mask}],
        boundary=   boundary,
        ttype=      ttype,
        dtype=      np.complex128
        )
    return dmrg
"""

idmrg_template="""\
import numpy as np
import HamiltonianPy.DMRG as DMRG
from HamiltonianPy import *
from HamiltonianPy.TensorNetwork import *
from .config import *

__all__=['idmrgconstruct']

def idmrgconstruct(name,parameters,lattice,terms,target,{argumentstatistics}boundary=None,**karg):
    dmrg=DMRG.iDMRG(
        dlog=       'log',
        din=        'data',
        dout=       'result/idmrg',
        name=       '%s_%s'%(name,lattice.name),
        tsg=        DMRG.TSG(name='ITER',target=target,miniter=nnb+6,maxiter=50,nmax=100,plot=True,run=DMRG.iDMRGTSG),
        parameters= parameters,
        map=        parametermap,
        lattice=    lattice,
        config=     IDFConfig(priority=DEFAULT_{system}_PRIORITY,map=idfmap),
        degfres=    DegFreTree(layers=DEGFRE_{system}_LAYERS,map=qnsmap),
        terms=      [term({termstatistics}**parameters) for term in terms],
        mask=       [{mask}],
        boundary=   boundary,
        ttype=      ttype,
        dtype=      np.complex128
        )
    return dmrg
"""

def fdmrg(**karg):
    return fdmrg_template.format(
            argumentstatistics=     '' if karg['system']=='spin' else "statistics='f',",
            termstatistics=         '' if karg['system']=='spin' else "statistics,",
            system=                 'SPIN' if karg['system']=='spin' else 'FOCK',
            mask=                   '' if karg['system']=='spin' else "'nambu'"
            )

def idmrg(**karg):
    return idmrg_template.format(
            argumentstatistics=     '' if karg['system']=='spin' else "statistics='f',",
            termstatistics=         '' if karg['system']=='spin' else "statistics,",
            system=                 'SPIN' if karg['system']=='spin' else 'FOCK',
            mask=                   '' if karg['system']=='spin' else "'nambu'"
            )
