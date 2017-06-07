'''
VCACCT test.
'''

__all__=['test_vcacct']

from HamiltonianPy import *
from HamiltonianPy.VCA import *
import numpy as np
import HamiltonianPy.ED as ED

def test_vcacct():
    print 'test_vcacct'
    t1,U=-1.0,4.0
    H2,H8P=Hexagon('H2'),Hexagon('H8P')
    cell=Lattice(name='H2',rcoords=H2.rcoords,vectors=H2.vectors,nneighbour=1)
    LA=Lattice(name='H4-A',rcoords=H8P.rcoords[[3,0,4,6]],nneighbour=1)
    LB=Lattice(name='H4-B',rcoords=H8P.rcoords[[2,1,5,7]],nneighbour=1)
    lattice=Lattice.compose(name='H4CCT',points=LA.points+LB.points,vectors=H8P.vectors,nneighbour=1)
    map=lambda ndx: Fermi(atom=0 if (ndx.scope in ('H4-A','H2') and ndx.site==0) or (ndx.scope=='H4-B' and ndx.site>0) else 1,norbital=1,nspin=2,nnambu=1)
    config=IDFConfig(priority=DEFAULT_FERMIONIC_PRIORITY,pids=lattice.pids,map=map)
    cgf=ED.FGF(operators=fspoperators(config.table(),lattice),nstep=200,save_data=False,prepare=VCACCTGFP,run=VCACCTGF)
    vcacct=VCACCT(
        name=           'H4CCT',
        cgf=            cgf,
        cell=           cell,
        lattice=        lattice,
        config=         config,
        terms=[         Hopping('t1',t1),
                        Hubbard('U',U)
                        ],
        subsystems=[    {'basis':FBasis(up=(4,2),down=(4,2)),'lattice':LA},
                        {'basis':FBasis(up=(4,2),down=(4,2)),'lattice':LB}
                        ],
        )
    vcacct.register(EB(name='EB',path=hexagon_gkm(nk=100),mu=U/2,emax=6.0,emin=-6.0,eta=0.05,ne=400,save_data=False,run=VCAEB))
    vcacct.register(DOS(name='DOS',BZ=hexagon_bz(nk=50),mu=U/2,emin=-5,emax=5,ne=400,eta=0.05,save_data=False,run=VCADOS))
    vcacct.summary()
