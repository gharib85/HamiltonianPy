'''
Linear algebra test.
'''

__all__=['test_linalg']

from numpy import *
from numpy.linalg import norm
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import eigsh
from HamiltonianPy import QuantumNumber,QuantumNumberCollection,SpinMatrix
from HamiltonianPy.DMRG.linalg import *

def test_linalg():
    print 'test_linalg'
    test_kron()
    #test_block_svd_part_I()
    #test_block_svd_part_II()

def test_kron():
    print 'test_kron'
    qn1=QuantumNumber([('Sz',1,'U1')])
    qn2=QuantumNumber([('Sz',0,'U1')])
    qn3=QuantumNumber([('Sz',-1,'U1')])
    a=QuantumNumberCollection([(qn1,1),(qn2,1),(qn3,1)])
    b=a.tensordot(a,history=True)
    print 'a:%s'%a
    print 'b:%s'%(b)
    sz=SpinMatrix((1,'z'),dtype=float64)
    sp=SpinMatrix((1,'+'),dtype=float64)
    sm=SpinMatrix((1,'-'),dtype=float64)
    print 'sz:\n%s'%sz
    print 'sp:\n%s'%sp
    print 'sm:\n%s'%sm
    matrix=kron(sz,sz,a,a,b,target=qn2,format='csr')+kron(sp,sm,a,a,b,target=qn2,format='csr')+kron(sm,sp,a,a,b,target=qn2,format='csr')
    print matrix.todense()
    print

def test_block_svd_part_I():
    print 'test_block_svd_part_I'
    a=random.random((9,))
    print 'a:\n%s'%a
    u,s,v=block_svd(a,3,3)
    print 'u,s,v:\n%s\n%s\n%s'%(u,s,v)
    print 'u*s*v:\n%s'%(einsum('ij,j,jk->ik',u,s,v))
    u,s,v,err=block_svd(a,3,3,n=2)
    print 'truncated u,s,v:\n%s\n%s\n%s'%(u,s,v)
    print 'truncation error:%s'%err
    b=einsum('ij,j,jk->ik',u,s,v).reshape((9,))
    print 'truncated a:\n%s'%(b)
    print 'err:%s'%(norm(b-a))
    print

def test_block_svd_part_II():
    print 'test_block_svd_part_II'
    qn1=QuantumNumber([('Sz',1,'U1')])
    qn2=QuantumNumber([('Sz',0,'U1')])
    qn3=QuantumNumber([('Sz',-1,'U1')])
    a=QuantumNumberCollection([(qn1,1),(qn2,1),(qn3,1)])
    sz=SpinMatrix((1,'z'),dtype=float64)
    sp=SpinMatrix((1,'+'),dtype=float64)
    sm=SpinMatrix((1,'-'),dtype=float64)
    print