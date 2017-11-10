'''
FED test.
'''

__all__=['test_fed']

from numpy import *
from HamiltonianPy import *
from HamiltonianPy.ED import *

def test_fed():
    print 'test_fed'
    t,U,m,n=-1.0,8.0,2,2
    basis=FBasis(up=(m*n,m*n/2),down=(m*n,m*n/2))
    lattice=Square('S1')('%sO-%sO'%(m,n))
    config=IDFConfig(priority=DEFAULT_FERMIONIC_PRIORITY,pids=lattice.pids,map=lambda pid: Fermi(atom=0,norbital=1,nspin=2,nnambu=1))
    fed=FED(
            name=       'WG-%s-%s'%(lattice.name,basis.rep),
            basis=      basis,
            lattice=    lattice,
            config=     config,
            terms=[     Hopping('t',t,neighbour=1),
                        Hubbard('U',U,modulate=True)
                        ]
        )
    fed.register(EL(name='EL',path=BaseSpace(('U',linspace(0.0,5.0,100))),ns=6,savedata=False,run=EDEL))
    gf=FGF(name='GF',operators=fspoperators(config.table(),lattice),nstep=100,savedata=False,prepare=EDGFP,run=EDGF)
    fed.register(DOS(name='DOS-1',parameters={'U':0.0},mu=0.0,emin=-10,emax=10,ne=501,eta=0.05,savedata=False,run=EDDOS,dependences=[gf]))
    fed.register(DOS(name='DOS-2',parameters={'U':8.0},mu=4.0,emin=-10,emax=10,ne=501,eta=0.05,savedata=False,run=EDDOS,dependences=[gf]))
    fed.summary()
    print