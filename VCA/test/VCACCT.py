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
    t1,U=-1.0,8.0
    H2,H4A,H4B,H8P=Hexagon('H2'),Hexagon('H4A'),Hexagon('H4B'),Hexagon('H8P')
    cell,LA,LB=H2('1P-1P',nneighbour=1),H4A(nneighbour=1),H4B(nneighbour=1)
    lattice=Lattice.compose(name='H4CCT',points=LA.points+LB.points,vectors=H8P.vectors,nneighbour=1)
    map=lambda ndx: Fermi(atom=0 if (ndx.scope in ('H4A','H2') and ndx.site==0) or (ndx.scope=='H4B' and ndx.site>0) else 1,norbital=1,nspin=2,nnambu=1)
    config=IDFConfig(priority=DEFAULT_FERMIONIC_PRIORITY,pids=lattice.pids,map=map)
    cgf=ED.FGF(operators=fspoperators(config.table(),lattice),nstep=200,savedata=False,prepare=VCACCTGFP,run=VCACCTGF)
    vcacct=VCACCT(
        name=           'H4CCT',
        cgf=            cgf,
        cell=           cell,
        lattice=        lattice,
        config=         config,
        terms=[         Hopping('t1',t1),
                        Hubbard('U',U)
                        ],
        weiss=[         Onsite('afm',0.0,indexpacks=sigmaz('sp')*sigmaz('sl'),modulate=True)
                        ],
        subsystems=[    {'basis':FBasis(up=(4,2),down=(4,2)),'lattice':LA},
                        {'basis':FBasis(up=(4,2),down=(4,2)),'lattice':LB}
                        ],
        )
    gp=GP(name='GP',mu=U/2,BZ=KSpace(reciprocals=lattice.reciprocals,nk=100),run=VCAGP)
    vcacct.register(GPM(name='afm',BS=BaseSpace(('afm',np.linspace(0.0,0.1,11))),dependences=[gp],savedata=False,run=VCAGPM))
    vcacct.register(EB(name='EB',parameters={'afm':0.0},path=hexagon_gkm(nk=100),mu=U/2,emax=6.0,emin=-6.0,eta=0.05,ne=400,savedata=False,run=VCAEB))
    vcacct.register(DOS(name='DOS',parameters={'afm':0.0},BZ=hexagon_bz(nk=50),mu=U/2,emin=-5,emax=5,ne=400,eta=0.05,savedata=False,run=VCADOS))
    vcacct.summary()
