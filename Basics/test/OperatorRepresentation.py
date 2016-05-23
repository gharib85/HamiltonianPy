'''
OperatorRepresentation test.
'''

__all__=['test_opt_rep']

from numpy import *
from HamiltonianPy.Basics import *
import itertools
import time

def test_opt_rep():
    print 'test_opt_rep'
    m=2;n=2;nloop=500
    p=Point(pid=PID(site=0,scope="WG"),rcoord=[0.0,0.0],icoord=[0.0,0.0])
    a1=array([1.0,0.0]);a2=array([0.0,1.0])
    points=tiling(cluster=[p],vectors=[a1,a2],indices=itertools.product(xrange(m),xrange(n)))
    config=Configuration(priority=DEFAULT_FERMIONIC_PRIORITY)
    for point in points:
        config[point.pid]=Fermi(atom=0,norbital=1,nspin=2,nnambu=2)
    l=Lattice(name="WG",points=points)
    l.plot(pid_on=True)
    table=config.table(nambu=True)
    a=+Hopping('t',1.0,neighbour=1,indexpackages=sigmaz("SP"))
    b=+Onsite('mu',1.0,neighbour=0,indexpackages=sigmaz("SP"))
    c=+Pairing('delta',1.0,neighbour=1,indexpackages=sigmaz("SP"))
    opts=OperatorCollection()
    for bond in l.bonds:
        opts+=a.operators(bond,table,config)
        opts+=b.operators(bond,table,config)
        opts+=c.operators(bond,table,config)
    print opts
    basis=BasisF(nstate=2*m*n)
#    basis=BasisF((2*m*n,m*n))
#    basis=BasisF(up=(m*n,m*n/2),down=(m*n,m*n/2))
#    print basis
    stime=time.time()
    for i in xrange(nloop):
        opt_rep(opts.values()[0],basis,transpose=False)
#        print opt_rep(opts[0],basis,transpose=False)
    etime=time.time()
    print etime-stime
    print
